# CarbonEdge Development Notes

Note that (SINFONIA) denotes elements already provided by original Sinfonia codebase.


## [ ] Infra
- [x] Get base Sinfonia to run.
- [x] Upgrade package dependencies to Python 3.10.
- [ ] Helm repo.
- [ ] Carbon trace repo.


## [ ] Core

### [ ] Tier-1
- [x] Carbon-aware matcher logic and registered as Poetry package.

### [ ] Tier-2
- [ ] RAPL (Intel) energy report as cloudlet resources via Prometheus.
    - [ ] Write RAPL exporter for Prometheus.
- [ ] DCGM (NVIDIA) energy report as cloudlet resources via Prometheus.
- [ ] Carbon trace interface and logic.
    - [ ] Real-time carbon trace.
        - Get Electricity Maps region code: User-provide (lat-long) > Auto-detect (provided byElectricity Maps)
    - [ ] Carbon trace replay.
        - [ ] Pull trace from repo.
        - [ ] Parse trace file.

### [ ] Tier-3
TBD

- Tier-3 recipe
- Choose which app to serve as example.


### [ ] Cross-tier
- [ ] Global clock sync (for carbon trace replay).
    - [ ] Clock origin at Tier-1.
    - [ ] Tier-1 broadcast clock to Tier-2s.

## [ ] User interface
- [x] (SINFONIA) Able to select which matchers to use.
- [ ] Able to select from real-time carbon trace OR trace replay (from repository).


## [ ] Addons (optional)
- [ ] Prettified logger.


## [ ] Experiment
- [ ] Geographic simulation.
    - [ ] Latency via `tc`.
    - [ ] Tier-2 server lat-long.
    - [ ]


## Functional requirements

Must-work functionalities in the end-product:

1. User must be able to interface with CarbonEdge as listed in the User interface section.


## Notes

### Configurable environment variables

- CARBON_QUERY_MODES = "realtime" | "playback" 
    - How to query carbon intensity data.
