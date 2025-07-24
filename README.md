# CarbonEdge

## Introduction

## Architecture

Add diagram.

How CarbonEdge reporting works, how Tier1 uses carbon data to route request.

## Organization

The project is organized into the following modules:
- **deploy-tier1** - Contains Ansible deployment scripts to deploy CarbonEdge-enabled Sinfonia-Tier2. Currently not in use.
- **deploy-tier2** - Contains Ansible deployment scripts to deploy CarbonEdge-enabled Sinfonia-Tier2.
- **deploy-tier2/inv** - Contains Ansible deployment scripts to deploy CarbonEdge-enabled Sinfonia-Tier2.
- **RECIPES** - Contains Sinfonia recipes to deploy user applications in Sinfonia.
- **src** - Contains CarbonEdge/Sinfonia code and logic.

## Prerequisites

CarbonEdge has been tested with the following environment:
- Ubuntu 22.04
- Python 3.10.18
- Poetry 2.1.3
- Helm 3.15.3
- k3s 1.32.6
- kubectl 1.32.6
- Docker 27.1.0
- Ansible 2.16.14

In addition, CarbonEdge requires an API authentication key from Electricity Maps, which you can acquire for free [here](https://portal.electricitymaps.com/auth/signup?return=%2Fauth%2Flogin).

**To avoid permission errors, we strongly recommend installing dependencies globally across all users.**

## Deployment

### Deploying CarbonEdge

Sinfonia is designed to be deployed as a Kubernetes deployment. We provided an Ansible script to automate Sinfonia-Tier2 
deployment across multiple target machines. The Ansible script will provision the necessary infrastructure and services to run Sinfonia, and will deploy Sinfonia as a Helm chart deployment. A template Ansible inventory file is given at `deploy-tier2/inv/inv.yaml`. To provide the Electricity maps authentication key, create an Ansible vault file,
```
ansible-vault create deploy-tier2/inv/secrets.yaml
```
with the following field,
```
carbonedge_tier2_electricity_maps_auth_token: <AUTH_TOKEN>
```

To deploy, modify the Ansible deployment script with your system's configuration (username, IP), and run the provided Ansible script as follows,
```
ansible-playbook deploy-tier2/deploy.yml -KJ 
```

If you want to deploy to multiple target machines via Ansible inventory, modify the Ansible deployment script accordingly and run the command,
```
ansible-playbook deploy-tier2/deploy.yml -KJ -i <PATH_TO_INVENTORY_FILE>
```

This will deploy the necessary infrastructure and a CarbonEdge-enabled Sinfonia-Tier2 instance on Kubernetes. To verify that all deployments are up and running, you can run,
```
kubectl get po -A
```

### Configuration

Sinfonia-Tier1 provides the following configurable environment variables,
- `SINFONIA_CLOUDLETS` [OPTIONAL]: 
- `SINFONIA_MATCHERS` [DEFAULT ["carbon-edge"]]: 
- `SINFONIA_RECIPES` [DEFAULT 'RECIPIES']:

Sinfonia-Tier2

CarbonEdge is configured via environment variables. For Sinfonia-Tier1, the available environment variables are,
- `CARBONEDGE_CARBON_LOG_FOLDER_PATH`: Folder path to log carbon logs.

For Sinfonia-Tier2, the available environment variables are,
- `CARBONEDGE_LATITUDE` / `CARBONEDGE_LATITUDE` [OPTIONAL]: Coordinates for Sinfonia-Tier2 server location. If unspecified, Sinfonia will attempt to estimate coordinates based on IP address.
- `CARBONEDGE_CARBON_INTENSITY_QUERY_MODE` ('REALTIME' | 'REPLAY'): Method to inquire carbon intensity at Sinfonia-Tier2 location. **Note: For now, only 'REALTIME' mode is supported.**
- `CARBONEDGE_REALTIME_ELECTRICITY_MAPS_AUTH_TOKEN`: Electricity Maps API authentication token.

All CarbonEdge environment variables, unless specified as optional or default, must be configured in order for CarbonEdge to be enabled. On successful configuration, the server will log `CarbonEdge enabled`, otherwise the server will log `CarbonEdge disabled`.

To configure CarbonEdge environment variables in Kubernetes deployment, we provided hooks in the Ansible deployment scripts that you can specify. For Sinfonia-Tier2 deployment,
- `sinfonia_recipes`: Path or public URL to Sinfonia recipe repository.
- `sinfonia_tier1_url`: Public URL of Sinfonia-Tier1 instance.
- `sinfonia_tier2_url`: Public URL of Sinfonia-Tier2 instance. **Note: Sinfonia-Tier2 deployed via Helm is always at port 30051.**
- `carbonedge_tier2_carbon_intensity_query_mode`
- `carbonedge_tier2_latitude` / `carbonedge_tier2_longitude`

### CarbonEdge reporting



## Development

### Getting started

Dependencies for the project are managed by the Poetry package manager, and can be found in pyproject.toml. We recommend that you start a virtual environment via `poetry env activate`. To install, 
run:
```
poetry install
```

Poetry will spawn a virtual environment, install the necessary packages, and install Sinfonia-Tier1 and Sinfonia-Tier2 
as modules. To verify that installation was successful, you can now run Sinfonia-Tier1 or Sinfonia-Tier2 as follows,
```
poetry run sinfonia-tier<1/2>
```

### Running Sinfonia locally

To enable CarbonEdge, environment variables must be defined as specified in the CarbonEdge configuration section. For local development, we provide a convenient `--carbonedge-config` option to parse environment variables from a `.env` file.

For Sinfonia-Tier1, the

To view help panels, you can run,
```
poetry run sinfonia-tier<1/2> --help
```

### Sinfonia matchers

TBD

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For questions, issues, or contributions, please contact:
- **Li (Lilly) Wu** — [liwu@umass.edu](mailto:liwu@umass.edu)
- **Khai Nguyen** — [tuankhai2k@gmail.com](mailto:tuankhai2k@gmail.com)  
