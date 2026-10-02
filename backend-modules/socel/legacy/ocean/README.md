# OCEAn (parked)

OCEAn, the object-centric emission analysis adapted from works by Raimund Hensen,
as it was before the sOCEL module was rebuilt. Kept for reference, not in use:
not packaged, not mounted and excluded from ruff, pyright and import-linter.

`ocelescope_module_socel/` keeps the package layout the code had in `src/`:

- `ocean/` - the slice (domain, application, infrastructure, api; its routes
  were mounted under `/ocean`)
- `ocel_graph/`, `ocel_utils/` - its helpers (object graph via rustworkx,
  attribute values at event time)
- `api_schema.py` - a copy of the `ApiModel` base it imports

To revive it, copy these back into `src/ocelescope_module_socel/`, mount
`ocean.api.router` in `module.py`, add `rustworkx` to the dependencies and the
slice to the import-linter contracts. The frontend counterpart is in
`frontend-modules/socel/legacy/ocean/`.
