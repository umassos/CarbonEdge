# CarbonEdge

## Introduction

## Architecture

## Organization

The project is organized into the following modules:
- **deploy-tier1** - Contains Ansible deployment scripts to deploy CarbonEdge-enabled Sinfonia-Tier2. Currently not in use.
- **deploy-tier2** - Contains Ansible deployment scripts to deploy CarbonEdge-enabled Sinfonia-Tier2.
- **deploy-tier2/inv** - Contains Ansible deployment scripts to deploy CarbonEdge-enabled Sinfonia-Tier2.
- **RECIPES** - Contains Sinfonia recipes to deploy user applications in Sinfonia.
- **src** - Contains CarbonEdge/Sinfonia code and logic.

## Deployment

### Prerequisites

CarbonEdge has been tested with the following environment:
- Ubuntu 22.04
- Python 3.10.18
- Poetry 2.1.3
- Helm 3.15.3
- k3s 1.32.6
- kubectl 1.32.6
- Docker 27.1.0

### Setup

Dependencies for the project are managed by the Poetry package manager, and can be found in pyproject.toml. To install, run:
```
poetry install
```

Poetry will spawn a virtual environment, install the necessary packages, and install Sinfonia-Tier1 and Sinfonia-Tier2 as modules. To verify that installation was successful, you can now run Sinfonia-Tier1 as follows,
```
poetry run sinfonia-tier1
```
and Sinfonia-Tier2 as follows,
```
poetry run sinfonia-tier2
```

Sinfonia also requires supporting services to function (e.g. Prometheus). To set up, 


## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For questions, issues, or contributions, please contact:
- **Li (Lilly) Wu** — [liwu@umass.edu](mailto:liwu@umass.edu)
- **Khai Nguyen** — [tuankhai2k@gmail.com](mailto:tuankhai2k@gmail.com)  

