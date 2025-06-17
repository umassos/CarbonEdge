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
- [x] RAPL (Intel) energy report as cloudlet resources (via Prometheus ?)
    - [ ] Write RAPL exporter for Prometheus. ?
- [ ] DCGM (NVIDIA) energy report as cloudlet resources via Prometheus.
- [ ] Carbon trace interface and logic.
    - [x] Real-time carbon trace.
        - [x] Query Electricity Maps: 
            - User-provide (lat-long) > Auto-detect (provided by Electricity Maps)
            - https://portal.electricitymaps.com/docs/api#carbon-intensity-latest
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

## [x] User interface
- [x] (SINFONIA) Able to select which matchers to use.
- [x] Able to select from real-time carbon trace OR trace replay (from repository).


## [ ] Addons (optional)
- [ ] Prettified logger.


## [ ] Experiment
- [ ] Geographic simulation.
    - [ ] Latency via `tc`.
    - [ ] Tier-2 server lat-long.
    - [ ]

## [ ] Resolve TODO comments


## Functional requirements

Must-work functionalities in the end-product:

1. User must be able to interface with CarbonEdge as listed in the User interface section.


## Notes

### Configurable environment variables

- CARBONEDGE_CARBON_INTENSITY_QUERY_MODE = "realtime" | "replay" 
    - How to query carbon intensity data.
        - "realtime" means querying live data from Electricity Maps.
        - "replay" means going through carbon trace.

- CARBONEDGE_CONFIG = Path
    - Path to CarbonEdge config file (for now only YAML supported)

- CARBON_TRACE_URI = url | local path
    - Where to locate carbon trace file (must be from Electricity Maps)
    - Either URL or local path.
    - Only active if CARBON_INTENSITY_QUERY_MODE == "replay".

## CarbonEdge config template

```
coordinate:  # Amherst, MA
  latitude: 42.3732
  longitude: 72.5199

carbon_intensity_query_mode: 'REALTIME'

realtime_config:
  electricity_maps_auth_token: 'ABCXYZ'

replay_config:
    carbon_intensity_uri: 'XYZABC'
```


## Questions

- What happens in "replay" mode when you finish running through the entire trace file?
