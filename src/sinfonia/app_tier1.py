#
# Sinfonia
#
# Copyright (c) 2021-2022 Carnegie Mellon University
#
# SPDX-License-Identifier: MIT
#

from __future__ import annotations

import logging
import sys
from pathlib import Path
from uuid import UUID

import flask
import typer
from connexion import FlaskApp
from connexion.resolver import MethodViewResolver
from flask_executor import Executor
from geolite2 import geolite2
from rich import print
from werkzeug.middleware.proxy_fix import ProxyFix
from yarl import URL

from .app_common import (
    OptionalBool,
    OptionalPath,
    OptionalStr,
    StrList,
    port_option,
    recipes_option,
    version_option,
)
from .carbonedge_carbon_history import CarbonHistoryCsvLogger
from .carbonedge_config import Tier1CarbonEdgeConfig
from .cloudlets import Cloudlet
from .cloudlets import load as cloudlets_load
from .deployment_repository import DeploymentRepository
from .jobs import scheduler, start_expire_cloudlets_job
from .matchers import Tier1MatchFunction, get_match_function_plugins


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def init_carbonedge(
        flask_cfg: flask.Config,
        ce_cfg: Tier1CarbonEdgeConfig
):
    flask_cfg['CARBON_HISTORY_CSV_LOGGER'] = CarbonHistoryCsvLogger(
        ce_cfg.carbon_log_folder_path
    )

    flask_cfg['CARBON_HISTORY_CSV_LOGGER'].write_headers()



class Tier1DefaultConfig:
    CLOUDLETS: str | Path | None = None
    MATCHERS: list[str] = ["network", "location", "random", "carbon-aware"]
    RECIPES: str | Path | URL = "RECIPES"

    # These are initialized by the wsgi app factory from the config
    # cloudlets: dict[UUID, Cloudlet] = {}                          # CLOUDLETS
    # executor = Executor(flask_app)
    # geolite2_reader = geolite2.reader()
    # match_functions: list[Tier1MatchFunction] = []                # MATCHERS
    # deployment_repository: DeploymentRepository | None = None     # RECIPES


def load_cloudlets_conf(cloudlets_conf: str | Path | None) -> dict[UUID, Cloudlet]:
    """read cloudlets.yaml configuration file to preseed Tier2 cloudlets

    this depends on flask_app.config["geolite2_reader"]
    """
    if cloudlets_conf is None:
        return {}

    with Path(cloudlets_conf).open() as stream:
        cloudlets = cloudlets_load(stream)

    return {cloudlet.uuid: cloudlet for cloudlet in cloudlets}


def list_match_functions(value):
    if value:
        print("Available tier1 match functions:")
        matchers = get_match_function_plugins().keys()
        print(sorted(matchers))
        raise typer.Exit()


def load_match_functions(matchers: list[str]) -> list[Tier1MatchFunction]:
    """load pluggable functions to select Tier2 candidates"""
    try:
        tier1_matchers = get_match_function_plugins()
        match_functions = [tier1_matchers[matcher].load() for matcher in matchers]
        logging.info(f"Loaded match functions {matchers}")
    except KeyError as e:
        sys.exit(f"Error: Match function '{e.args[0]}' not found")
    return match_functions


def wsgi_app_factory(**args) -> FlaskApp:
    """Sinfonia Tier 1 API server"""
    app = FlaskApp(__name__, specification_dir="openapi/")

    flask_app = app.app

    # Load default config
    flask_app.config.from_object(Tier1DefaultConfig)

    # Load config from environment file
    # 'SINFONIA_SETTINGS' is path to environment file
    flask_app.config.from_envvar("SINFONIA_SETTINGS", silent=True)

    # Load config from prefixed environment variable
    flask_app.config.from_prefixed_env(prefix="SINFONIA")

    # Load config from command line arguments
    cmdargs = {k.upper(): v for k, v in args.items() if v}
    flask_app.config.from_mapping(cmdargs)

    # Load CarbonEdge config from environment variables
    if 'CARBONEDGE_CONFIG' in flask_app.config:
        ce_cfg_path = flask_app.config['CARBONEDGE_CONFIG']
        ce_cfg = Tier1CarbonEdgeConfig.from_env_file(ce_cfg_path)
    else:
        ce_cfg = Tier1CarbonEdgeConfig()

    if ce_cfg.is_carbonedge_enabled():
        flask_app.config['CARBONEDGE_ENABLED'] = True
        init_carbonedge(flask_app.config, ce_cfg)
        logging.info('CarbonEdge enabled')
        logging.info(ce_cfg.model_dump())
    else:
        flask_app.config['CARBONEDGE_ENABLED'] = False
        logging.info('CarbonEdge disabled')

    flask_app.config["executor"] = Executor(flask_app)
    flask_app.config["geolite2_reader"] = geolite2.reader()

    with flask_app.app_context():
        flask_app.config["cloudlets"] = load_cloudlets_conf(
            flask_app.config.get("CLOUDLETS")
        )
    flask_app.config["deployment_repository"] = DeploymentRepository(
        flask_app.config["RECIPES"]
    )
    flask_app.config["match_functions"] = load_match_functions(
        flask_app.config["MATCHERS"]
    )

    # start background job to expire Tier2 cloudlets that are no longer reporting
    scheduler.init_app(flask_app)
    scheduler.start()
    start_expire_cloudlets_job()

    # handle running behind reverse proxy (should this be made configurable?)
    flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app)

    # add Tier1 APIs
    app.add_api(
        "sinfonia_tier1.yaml",
        resolver=MethodViewResolver("sinfonia.api_tier1"),
        validate_responses=True,
    )

    @app.route("/")
    def index():
        return ""

    return app


def resource_cleanup(app: FlaskApp):
    logging.info('Cleaning up resources')

    if 'CARBON_HISTORY_CSV_LOGGER' in app.app.config:
        app.app.config['CARBON_HISTORY_CSV_LOGGER'].close()


cli = typer.Typer()


@cli.command()
def tier1_server(
    version: OptionalBool = version_option,
    port: int = port_option,
    cloudlets: OptionalPath = typer.Option(
        None,
        help="Read YAML file containing known Tier2 cloudlets",
        show_default=False,
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    recipes: OptionalStr = recipes_option,
    matchers: StrList = typer.Option(
        [],
        "--match",
        "-m",
        help="Select Tier2 best match functions [default: network, location, random]",
    ),
    list_matchers: OptionalBool = typer.Option(
        None,
        "--list-matchers",
        callback=list_match_functions,
        is_eager=True,
        help="Show available best match functions",
        rich_help_panel='Callbacks'
    ),
    carbonedge_config: OptionalPath = typer.Option(
        None,
        help="Path to CarbonEdge config file",
        show_default=False,
        exists=True,
        dir_okay=False,
        resolve_path=True,
        rich_help_panel="CarbonEdge",
    ),
):
    """Run Sinfonia Tier1 with Flask's builtin server (for development)"""
    app = wsgi_app_factory(
        cloudlets=cloudlets, 
        recipes=recipes, 
        matchers=matchers,
        carbonedge_config=carbonedge_config,
    )

    try:
        app.run(port=port)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(e)
    finally:
        resource_cleanup(app)
