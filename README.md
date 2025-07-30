# CarbonEdge

## Introduction

This is the official repository for **_CarbonEdge_**, a carbon-aware framework for edge computing that optimizes the placement of edge workloads across mesoscale edge data centers to reduce carbon emissions while meeting latency SLOs. CarbonEdge was built on top of the [Sinfonia framework](https://github.com/cmusatyalab/sinfonia).

Our work was presented at [HPDC 2025](https://hpdc.sci.utah.edu/2025/). Link to paper [here](https://github.com/umassos/CarbonEdge/tree/main).

## Architecture

Add diagram.

How CarbonEdge reporting works, how Tier1 uses carbon data to route request.

## Organization

The project is organized into the following noteworthy modules:
- **deploy-tier1** - Contains deployment scripts to deploy CarbonEdge-Tier1.
- **deploy-tier2** - Contains deployment scripts to deploy CarbonEdge-Tier2.
- **deploy-tier2/inv** - Contains Ansible inventory and secrets to deploy CarbonEdge-Tier2.
- **RECIPES** - Contains Sinfonia recipes to deploy user applications in CarbonEdge.
- **src** - Contains CarbonEdge code and logic.

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

## Deployment

### Quickstart

We provided an initial pre-configured Ansible playbook at *deploy-tier2/deploy.yml* to deploy a local CarbonEdge-Tier1 and CarbonEdge-Tier2 instance on Kuberentes. First, edit the Ansible playbook to provide your local system information,
- Change `hosts` to 'localhost'.
- Change `become_user` to your system's superuser.
- Change `sinfonia_tier1_url` and `sinfonia_tier2_url` to the explicit URL address of your system. **Note that CarbonEdge-Tier1 and CarbonEdge-Tier2 is configured to always run on port 30050 and 30051 respectively per their provided Helm charts.**
- Verify the external tasks imported in the Ansible playbook matches your intended use case and system resources (e.g. comment out the `nvidia_gpu_operator` task if your system does not support NVIDIA GPU).

Next, you need to provide your Electricity Maps API key. We strongly recommend that you manage secret key via Ansible vault secret, or you can directly provide the secret key in the Ansible playbook. To create an Ansible vault secret file,
```
ansible-vault create deploy-tier2/inv/secrets.yaml
```
and include the following field,
```
carbonedge_tier2_electricity_maps_auth_token: <AUTH_TOKEN>
```

After all necessary configurations are specified, run the Ansible playbook as follows,
```
ansible-playbook deploy-tier2/deloy.yml -KJ
```

Ansible will now install the necessary infrastructures (k3s), dependencies (e.g. Prometheus, Grafana, Kilo, etc.), and finally CarbonEdge-Tier1 and CarbonEdge-Tier2. You can list all running pods to verify that all deployments were correctly installed,
```
k3s kubectl get po -A
```

### Deploying CarbonEdge-Tier1

Currently, CarbonEdge is designed to be deployed as 1 Tier-1 to many Tier-2s. Ideally, there should only be one CarbonEdge-Tier1 service present. You can deploy CarbonEdge-Tier1 manually via Helm or via the provided Ansible playbook.

The available Ansible configurations for CarbonEdge-Tier1 are as follows,
- `sinfonia_recipes` [Optional]: Folder path to mount *Sinfonia recipes* for deploying user-specified applications on CarbonEdge. 
- `sinfonia_tier1_matchers` [Default = *"carbon-aware"*]: List of matchers Tier-1 will use. The available matchers are *"location"*, *"network"*, *"random"*, and *"carbon-aware"*. The matchers are listed as comma-separated values and will be applied in the order they are given. An example would be *"location,network,carbon-aware"*.
- `sinfonia_tier1_cloudlets` [Optional]: File path to cloudlet configuration file to preemptively register Tier-2 instances.
- `carbonedge_tier1_carbon_log_folder_path` [Optional]: Path to log CarbonEdge-Tier2 reporting.

We provide a Docker image of the latest source code at *k2nt/carbonedge-tier1:dev3*. Should you update the source code and wish to deploy your changes, containerize the new source code, push to a public repository, and update the `image` and `tag` field accordingly either in the Ansible playbook or the Helm configuration file.

### Deploying CarbonEdge-Tier2

You can deploy CarbonEdge-Tier2 manually via Helm or via the provided Ansible playbook. 

The available Ansible configurations common for all CarbonEdge-Tier2 deployments are as follows,
- `sinfonia_tier1_url` [Required]: Public URL address for CarbonEdge-Tier1. Note that Tier-1 is always at port 30050 if deployed via provided Helm chart.
- `carbonedge_tier2_carbon_intensity_query_mode` [Optional]: The method to support acquire carbon intensity level at CarbonEdge-Tier2 location. As of now, the supported modes are *"REALTIME"* (querying live data from Electricity Maps) and "OFF"*.

The available Ansible configurations for CarbonEdge-Tier2 that are deployment-specific are as follows,
- `sinfonia_tier2_url` [Required]: Public URL address for CarbonEdge-Tier2. Note that Tier-2 is always at port 30051 if deployed via provided Helm chart.
-  `carbonedge_tier2_latitude` / `carbonedge_tier2_longitude` [Optional]: The coordinates at the CarbonEdge-Tier2 deployment. If not specified, CarbonEdge-Tier2 will attempt to estimate its coordinates via its public URL address.

The provided Ansible playbook is initially configured for local deployment. To enable deploying across multiple targets, first update the Ansible playbook as follows,
- Change `hosts` field to host-group name (e.g. *tier2hosts*)
- Comment out the localhost config section.
- Uncomment out the multiple target config section.

Next, define an Ansible inventory file in the following format,
```
# inv.yaml

<host-group name>  # (e.g. tier2hosts)
    hosts:
        <target-1 name>:
            # List of CarbonEdge-Tier2 configurations
            ansible_host: <IP_ADDRESS>
            sinfonia_tier2_url: <URL_ADDRESS>
            carbonedge_tier2_latitude: <LATITUDE>
            carbonedge_tier2_longitude: <LONGITUDE>
        <target-2 name>:
            ...
        ...
```

Then, provide the Electricity Maps API authentication key either via an Ansible vault secret or directly in the Ansible playbook. The steps are specified in the [Quickstart](#quickstart) section.

To run the Ansible playbook with inventory file, specify the `-i` option,
```
ansible-playbook deploy-tier2/deploy.yml -KJ -i <PATH_TO_INV_FILE>
```

We provided an example inventory file for your reference at *deploy-tier2/inv/inv.yaml*, and the full deployment command is,
```
ansible-playbook deploy-tier2/deploy.yml -KJ -i deploy-tier2/inv/inv.yaml
```

### Manual deployment via Helm

To facilitate configuration, CarbonEdge-Tier1 and CarbonEdge-Tier2 installations are managed as Helm chart deployments. We provide a Helm repository on Github at `https://k2nt.github.io/helm/carbonedge`. To add the repository to Helm,
```
helm repo add carbonedge https://k2nt.github.io/helm/carbonedge
```

The Helm charts for Tier-1 and Tier-2 are *carbonedge/carbonedge-tier1* and *carbonedge/carbonedge-tier2* respectively. We also provide an example Helm config file at *deploy-tier2/helm-manual-inv-tier2.yaml* for manual install,
```
helm install carbonedge-tier<1/2> carbonedge/carbonedge-tier<1/2> -f deploy-tier<1/2>/helm-manual-inv-tier<1/2>.yaml
```

Note that via our provided Helm chart, CarbonEdge-Tier1 and CarbonEdge-Tier2 will be launched as a NodePort service at port 30050 and 30051 respectively.

### Enabling CarbonEdge

CarbonEdge was designed to be a feature of the Sinfonia platform. CarbonEdge can be enabled by setting the necessary required fields in Tier-1 and Tier-2, where services will log *Carbon enabled* or *Carbon disabled* depending whether CarbonEdge configurations were correctly specified. You can also check that CarbonEdge is enable by verifying that CarbonEdge-Tier2 is reporting carbon and energy data fields to CarbonEdge-Tier1.

## Development

### Getting started

Dependencies are managed by the Poetry package manager. The included *pyproject.toml* file lists all required dependencies and their versions. To install, create a Poetry-managed Python virtual environment ```poetry env activate``` and run ```poetry install```. Poetry will then install the necessary dependencies as well as CarbonEdge-Tier1 and CarbonEdge-Tier2 as modules. To check that installation was successful, run ```poetry run sinfonia-tier<1/2>``` to see whether the services were launched. CarbonEdge Tier-1 and Tier-2 are essentially Flask services, and you can view the list of available APIs via OpenAPI at the *api/v1/ui/* endpoint.

CarbonEdge is enabled on Sinfonia via environment variables. Specific environment variables for Tier-1 and Tier-2 are listed in the [CarbonEdge-Tier1](#carbonedge-tier1) and [CarbonEdge-Tier2](#carbonedge-tier2) section respectively. All Sinfonia-specific and CarbonEdge-specific variables are prefixed with *SINFONIA_* and *CARBONEDGE_* respectively. For both Tier-1 and Tier-2, we provide an easy ```--carbonedge-config``` option to point to an *.env* file to specify CarbonEdge environment variables. To view the detailed help panel on other options, run ```poetry run sinfonia-tier<1/2> --help```. 

### CarbonEdge-Tier1

Sinfonia environment variables, can also be specified via CLI option noted below,
- `SINFONIA_RECIPES` [Optional, Default = *"RECIPES"*, `--recipes`]
- `SINFONIA_MATCHERS` [Optional, Default = *"carbon-aware"*, `--match`]
- `SINFONIA_CLOUDLETS` [Optional]

CarbonEdge environment variables:
- `CARBONEDGE_CARBON_LOG_FOLDER_PATH` [Optional]

### CarbonEdge-Tier2

Sinfonia environment variables, can also be specified via CLI option noted below,
- `SINFONIA_RECIPES` [Optional, Default = *"RECIPES"*, `--recipes`]
- `SINFONIA_KUBECONFIG` [Optional, `--kubeconfig`]
- `SINFONIA_KUBECONTEXT` [Optional, `--kubecontext`]
- `SINFONIA_PROMETHEUS` [Optional, `--prometheus`]
- `SINFONIA_TIER1_URLS` [Required, `--tier1-url`] 
- `SINFONIA_TIER2_URL` [Required, `--tier2-url`]
- `REPORT_TO_TIER1_INTERVAL_SECONDS` [Optional, Default = 15]

CarbonEdge environment variables:
- `CARBONEDGE_LATITUDE` / `CARBONEDGE_LONGITUDE` [Optional]
- `CARBONEDGE_CARBON_INTENSITY_QUERY_MODE` [Optional]
- `CARBONEDGE_REALTIME_ELECTRICITY_MAPS_AUTH_TOKEN` [Optional]

Note that `SINFONIA_TIER1_URLS` and `SINFONIA_TIER2_URL` **_must_** be defined to enable reporting job from Tier-2 to Tier-1. Also, Tier-2 requires a Prometheus to query system telemetry. If Prometheus is deployed on Kubernetes, you can manually acquire the Prometheus service IP address by running ```kubectl get po -n monitoring -o wide``` and get the IP address of pod ```prometheus-kube-prometheus-stack-prometheus-0```. Note that Prometheus runs on default port 9090.

### CarbonEdge-Tier3

TBD

### Containerization

TBD

### Recipes

TBD

### Matchers

TBD

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For questions, issues, or contributions, please contact:
- **Li (Lilly) Wu** — [liwu@umass.edu](mailto:liwu@umass.edu)
- **Khai Nguyen** — [tuankhai2k@gmail.com](mailto:tuankhai2k@gmail.com)  
