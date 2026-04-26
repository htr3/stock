# TODO

The original LiveDataFetcher fix (replace `paper` with `self.paper`, hoist
`logging.basicConfig` to module level) is complete in
[scripts/live_data_fetcher.py](scripts/live_data_fetcher.py).

Current focus: see the Phase 0 cleanup plan
(`.cursor/plans/stocks_repo_cleanup_*.plan.md`) for the active workstream.

Next planned phases (deferred):
- Validation + cost overhaul (triple-barrier labels, walk-forward CV with
  purge/embargo, cost model, net-of-cost Sharpe as the model promotion gate).
- Simons-lite feature upgrade (microstructure, cross-sectional residualization,
  regime conditioning, IC-based feature selection).
