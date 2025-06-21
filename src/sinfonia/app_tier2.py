#
# Sinfonia
#
# Copyright (c) 2021-2022 Carnegie Mellon University
#
# SPDX-License-Identifier: MIT
#

from __future__ import annotations

import logging
import socket
from pathlib import Path
from uuid import uuid4

import typer
from attrs import define
from connexion import FlaskApp
from connexion.resolver import MethodViewResolver
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.serving import get_interface_ip
from yarl import URL
from zeroconf import ServiceInfo, Zeroconf

from .app_common import (
    OptionalBool,
    OptionalPath,
    OptionalStr,
    StrList,
    port_option,
    recipes_option,
    version_option,
)
from .carbonedge_config import Tier2CarbonEdgeConfig, CarbonIntensityQueryMode
from .carbonedge_fetcher import RealTimeFetcher, ReplayFetcher
from .cluster import Cluster
from .deployment_repository import DeploymentRepository
from .jobs import scheduler, start_expire_deployments_job, start_reporting_job


class Tier2DefaultConfig:
    RECIPES: str | Path | URL = "RECIPES"
    KUBECONFIG: str = ""
    KUBECONTEXT: str = ""
    PROMETHEUS: str = "http://kube-prometheus-stack-prometheus.monitoring:9090"
    TIER1_URLS: list[str] = []
    TIER2_URL: str | None = None
    REPORT_TO_TIER1_INTERVAL_SECONDS: int = 10

    # These are initialized by the wsgi app factory from the config
    # UUID: UUID
    # deployment_repository: DeploymentRepository | None = None     # RECIPES
    # K8S_CLUSTER : Cluster | None = None   # KUBECONFIG KUBECONTEXT PROMETHEUS


def tier2_app_factory(**args) -> FlaskApp:
    """Sinfonia Tier 2 API server"""
    app = FlaskApp(__name__, specification_dir="openapi/")

    flask_app = app.app

    # Load default config
    flask_app.config.from_object(Tier2DefaultConfig)

    # Load config from environment file
    # 'SINFONIA_SETTINGS' is path to .env file
    flask_app.config.from_envvar("SINFONIA_SETTINGS", silent=True)

    # Load config from prefixed environment variables
    flask_app.config.from_prefixed_env(prefix='SINFONIA')
    if flask_app.config.get("TIER1_URL"):
        flask_app.config["TIER1_URLS"] = [flask_app.config["TIER1_URL"]]

    # Load config from command line argument
    cmdargs = {k.upper(): v for k, v in args.items() if v}
    flask_app.config.from_mapping(cmdargs)

    # Load CarbonEdge config from prefixed environment variables
    flask_app.config.from_prefixed_env(prefix='CARBONEDGE')

    # Load CarbonEdge config from file
    if 'CARBONEDGE_CONFIG' in flask_app.config:
        logging.info('CarbonEdge config detected')

        cfg = Tier2CarbonEdgeConfig.from_yaml(
            flask_app.config['CARBONEDGE_CONFIG']
        )

        if cfg.coordinate is not None:
            flask_app.config['COORDINATE'] = cfg.coordinate

        flask_app.config['CARBON_INTENSITY_QUERY_MODE'] = cfg.carbon_intensity_query_mode
        
        if cfg.carbon_intensity_query_mode is CarbonIntensityQueryMode.REALTIME:
            flask_app.config['CARBON_REALTIME_FETCHER'] = RealTimeFetcher.from_config(cfg.realtime_config)

        if cfg.carbon_intensity_query_mode is CarbonIntensityQueryMode.REPLAY:
            flask_app.config['CARBON_REPLAY_FETCHER'] = ReplayFetcher.from_config(cfg.replay_config)
    else:
        logging.info('CarbonEdge config not found')
        flask_app.config['CARBON_INTENSITY_QUERY_MODE'] = CarbonIntensityQueryMode.OFF

    flask_app.config["UUID"] = uuid4()
    flask_app.config["deployment_repository"] = DeploymentRepository(
        flask_app.config["RECIPES"]
    )

    # connect to local kubernetes cluster
    cluster = Cluster.connect(
        flask_app.config.get("KUBECONFIG"), flask_app.config.get("KUBECONTEXT")
    )
    cluster.prometheus_url = (
        URL(flask_app.config["PROMETHEUS"]) / "api" / "v1" / "query"
    )
    flask_app.config["K8S_CLUSTER"] = cluster

    # start background jobs to expire deployments and report to Tier1
    scheduler.init_app(flask_app)
    scheduler.start()
    start_expire_deployments_job()
    start_reporting_job()

    # handle running behind reverse proxy (should this be made configurable?)
    flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app)

    # add Tier1 APIs
    app.add_api(
        "sinfonia_tier2.yaml",
        resolver=MethodViewResolver("sinfonia.api_tier2"),
        validate_responses=True,
    )

    @app.route("/")
    def index():
        return ""
    
    logging.info

    return app


@define
class ZeroconfMDNS:
    """Wrapper helping with zeroconf service registration"""

    zeroconf: Zeroconf | None = None

    def announce(self, port: int) -> None:
        """Try to announce our service on IPv4 and IPv6 on all interfaces"""
        if self.zeroconf is not None:
            self.withdraw()

        # werkzeug uses this function to figure out the ip address of the interface
        # that handles the default route. This should work as long as we don't
        # happen to have a secondary interface on the 10.0.0.0/8 network, I think.
        # either way, this seems to be about the best we can do for now because
        # when we just give a list of all known local addresses, it seems like
        # only the last IPv4 and IPv6 addresses end up being resolvable, and
        # these tend to be local-only docker or kvm network addresses on my system.
        address = get_interface_ip(socket.AF_INET)

        info = ServiceInfo(
            "_sinfonia._tcp.local.",
            "cloudlet._sinfonia._tcp.local.",
            parsed_addresses=[address],
            port=port,
            properties=dict(path="/"),
        )
        self.zeroconf = Zeroconf()
        self.zeroconf.register_service(info, allow_name_change=True)

    def withdraw(self) -> None:
        """Withdraw service registration"""
        if self.zeroconf is not None:
            self.zeroconf.unregister_all_services()
            self.zeroconf.close()
            self.zeroconf = None


cli = typer.Typer()


@cli.command()
def tier2_server(
    version: OptionalBool = version_option,
    port: int = port_option,
    recipes: OptionalStr = recipes_option,
    kubeconfig: OptionalPath = typer.Option(
        None,
        help="Path to kubeconfig file",
        show_default=False,
        exists=True,
        dir_okay=False,
        resolve_path=True,
        rich_help_panel="Kubernetes cluster config",
    ),
    kubecontext: str = typer.Option(
        "",
        help="Name of kubeconfig context to use",
        show_default=False,
        rich_help_panel="Kubernetes cluster config",
    ),
    prometheus: OptionalStr = typer.Option(
        None,
        metavar="URL",
        help="Prometheus endpoint",
        show_default=False,
        rich_help_panel="Kubernetes cluster config",
    ),
    tier1_urls: StrList = typer.Option(
        [],
        "--tier1-url",
        metavar="URL",
        help="Base URL of Tier 1 instances to report to (may be repeated)",
        rich_help_panel="Sinfonia Tier1 reporting",
    ),
    tier2_url: OptionalStr = typer.Option(
        None,
        metavar="URL",
        help="Base URL of this Tier 2 instance",
        show_default=False,
        rich_help_panel="Sinfonia Tier1 reporting",
    ),
    zeroconf: bool = typer.Option(
        False,
        help="Announce cloudlet on local network(s) with zeroconf mdns",
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
    """Run Sinfonia Tier-2 with Flask's builtin server (for development)"""
    try:
        app = tier2_app_factory(
            recipes=recipes,
            kubeconfig=kubeconfig,
            kubecontext=kubecontext,
            prometheus=prometheus,
            tier1_urls=tier1_urls,
            tier2_url=tier2_url,
            carbonedge_config=carbonedge_config,
        )
    except Exception as e:
        logging.error(e)
        return

    # run application, optionally announcing availability with MDNS
    zeroconf_mdns = ZeroconfMDNS()
    if zeroconf:
        zeroconf_mdns.announce(port)

    try:
        app.run(port=port)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(e)
    finally:
        zeroconf_mdns.withdraw()
