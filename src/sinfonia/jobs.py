#
# Sinfonia
#
# run periodic tasks
#
# Copyright (c) 2022 Carnegie Mellon University
#
# SPDX-License-Identifier: MIT
#

import logging

import pendulum
import requests
from flask_apscheduler import APScheduler
from requests.exceptions import RequestException
from yarl import URL

from .carbonedge_fetcher import RealTimeFetcher, ReplayFetcher


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = APScheduler()


def expire_cloudlets():
    cloudlets = scheduler.app.config["cloudlets"]

    expiration = pendulum.now().subtract(minutes=5)

    for cloudlet in list(cloudlets.values()):
        if cloudlet.last_update is not None and cloudlet.last_update < expiration:
            logging.info(f"Removing stale {cloudlet}")
            cloudlets.pop(cloudlet.uuid, None)


def start_expire_cloudlets_job():
    scheduler.add_job(
        func=expire_cloudlets,
        trigger="interval",
        seconds=60,
        max_instances=1,
        coalesce=True,
        id="expire_cloudlets",
        replace_existing=True,
    )


def expire_deployments():
    cluster = scheduler.app.config["K8S_CLUSTER"]
    with scheduler.app.app_context():
        cluster.expire_inactive_deployments()


def start_expire_deployments_job():
    scheduler.add_job(
        func=expire_deployments,
        trigger="interval",
        seconds=60,
        max_instances=1,
        coalesce=True,
        id="expire_deployments",
        replace_existing=True,
    )


def report_to_tier1_endpoints():
    config = scheduler.app.config

    tier2_uuid = config["UUID"]
    tier2_endpoint = URL(config["TIER2_URL"]) / "api/v1/deploy"

    cluster = config["K8S_CLUSTER"]
    
    resources = cluster.get_resources()

    if 'CARBONEDGE_REALTIME_FETCHER':
        fetcher: RealTimeFetcher = config['CARBONEDGE_REALTIME_FETCHER']
        resources['carbon_intensity_gco2_kwh'] = fetcher.fetch()
    elif 'CARBONEDGE_REPLAY_FETCHER':
        raise Exception('not yet supported')
        # fetcher: ReplayFetcher = config['CARBONEDGE_REPLAY_FETCHER']
        # resources['carbon_intensity_gco2_kwh'] = fetcher.fetch()

    logging.info("Got %s", str(resources))

    body = {
        "uuid": str(tier2_uuid),
        "endpoint": str(tier2_endpoint),
        "resources": resources,                
    }

    if 'CARBONEDGE_COORDINATE' in config:
        body['locations'] = [config['CARBONEDGE_COORDINATE'].to_tuple()]

    for tier1_url in config["TIER1_URLS"]:
        tier1_endpoint = URL(tier1_url) / "api/v1/cloudlets/"
        try:
            requests.post(
                str(tier1_endpoint),
                json=body,
            )
        except RequestException:
            logging.warning(f"Failed to report to {tier1_endpoint}")


def start_reporting_job():
    config = scheduler.app.config
    if not config["TIER1_URLS"] or config["TIER2_URL"] is None:
        logging.warning('TIER1_URLS and TIER2_URL not configured, skipping reporting job to Tier-1.')
        return

    logging.info("Reporting cloudlet status to Tier1 endpoints")
    scheduler.add_job(
        func=report_to_tier1_endpoints,
        trigger="interval",
        seconds=10,
        max_instances=1,
        coalesce=True,
        id="report_to_tier1",
        replace_existing=True,
    )
