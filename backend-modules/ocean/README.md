# OCEAn backend module

Object-centric emission analysis, ported from the original OCEAn to work
directly on Ocelescope's `OCEL` (polars). Mounted at `/modules/ocean/v1`.

```
src/ocelescope_module_ocean/
├── module.py            Ocean(Module): builds the FastAPI app
├── domain/
│   ├── models/            immutable data only: rules, factors, results, config
│   ├── services/          OCEAn's computations as pure functions on that data
│   └── exceptions.py
├── application/
│   ├── ports/             interfaces the use cases need (e.g. EmissionsRepository)
│   └── use_cases/         one file per action: its Command, the use case, its result
├── infrastructure/      adapters implementing the ports (e.g. session storage)
├── api/
│   ├── dependencies.py    composition root: builds use cases with their adapters
│   ├── schema.py          ApiModel: camelCase base of all request/response models
│   ├── exception_handlers.py  domain errors -> HTTP status codes
│   └── routes/            endpoints; request/response models live next to their route
├── ocel_utils/          generic OCEL helpers (e.g. attribute values at event time)
└── ocel_graph/          object graph + nearest-target search (rustworkx)
                         ocel_utils and ocel_graph are independent of OCEAn -
                         candidates for Ocelescope core
```

## Rules

- Dependencies point inwards: `api` -> `application` -> `domain`.
- `domain` and `application` never import `fastapi` or `ocelescope_backend`.
- Domain models carry data, no logic: they cannot import the OCEL or a service.
- Logic that encodes OCEAn's rules is a function in `domain/services/`; logic
  useful for any OCEL analysis goes to `ocel_utils/` or `ocel_graph/`, which
  import nothing from OCEAn.
- Routes never import adapters; they get use cases from `api/dependencies.py`.
- An endpoint only builds a command, runs its use case and maps the result.
- Domain results are collected polars frames, never lazy: the request's OCEL is
  closed when the request ends.

`pnpm run check:backend` (repository root) runs ruff, pyright and
import-linter; the rules above are import-linter contracts in `pyproject.toml`.

## Adding an endpoint

1. New data in `domain/models/`, new computation as functions in `domain/services/`.
2. `application/use_cases/<action>.py`: `<Action>Command`, the use case class
   with `execute(...)`, and its result model.
3. A port in `application/ports/` if the use case needs something from outside.
   Its adapter goes in `infrastructure/`.
4. `api/dependencies.py`: a `get_<action>` function building the use case.
5. `api/routes/<feature>.py`: request/response models (`ApiModel`) and the
   route with a stable `operation_id` (it names the generated frontend hook).
6. `pnpm --filter @instance/ocean-module build` regenerates the frontend client.
