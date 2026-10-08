# sOCEL backend module

Sustainability analysis of object-centric event logs for Ocelescope, mounted at
`/modules/socel/v1`. The sOCEL model and its computations live in the `socel`
library (`packages/sOCEL`); this module puts them behind an API. It is one hexagon,
organised by resource, not by page: pages are the frontend's concern, and a
page uses whichever resources it needs.

```
src/ocelescope_module_socel/
├── module.py            Socel(Module): builds the FastAPI app, mounts the router
├── domain/
│   ├── models/            immutable data only: what the use cases return;
│   │                      base.py holds Model, the base of them all
│   └── exceptions.py      the module's own errors
├── application/
│   ├── command.py         Command: base of all commands (frozen, keyword-only)
│   ├── ports/             what use cases need from outside, as protocols
│   └── use_cases/         one file per action: the use case and its command
├── infrastructure/        adapters of the ports: SQL on a log, the session's logs
└── api/
    ├── router.py          every resource's routes, under /{ocel_id}/...
    ├── dependencies.py    composition root: ApiSocel, and the use cases with their adapters
    ├── schema.py          ApiModel: camelCase base of all request/response models
    ├── exception_handlers.py  the module's errors as HTTP statuses
    └── routes/            one file per resource; its request/response models next to it
```

Resources of an sOCEL: `status`, `flows`, `classes`. Resources of any log:
`taxonomy` (the classes and flow categories an sOCEL may use), `classification`
(the class per activity and object type), `flow-records` (POST: takes a record
file and says which of its rows fit the log) and `socel` (POST: builds the
log's sOCEL as a new log).

## The sOCEL extension

The module declares `extensions = [SOCEL]` (`module.py`). The host then
recognizes sOCELs among the logs - `SOCEL.from_ocel` runs `SOCEL.validate`, the
declared tables plus the conformance rules - and lists the extension in a log's
metadata, which the frontend reads. Endpoints ask for `ApiSocel`
(`api/dependencies.py`) and get the validated `SOCEL`; a log that is none is
rejected with HTTP 422 and the reason before the use case is built, so use cases
never check for it. The frontend guards its pages the same way
(`requiresOcel: ["socel"]`), so they only open on an sOCEL.

An sOCEL is built from any log (`build_socel`): the request's log is read-only,
so the use case works on a copy and adds the result to the session as a new log.

Flow records come from one CSV, a row per record, with the columns `flow`,
`object`, `quantity` and either `start_time` and `end_time` (an interval
record) or `event` (an event-linked record). `object` and `event` are ids of
the log, times are ISO 8601 with an offset, and the quantity is the amount in
the interval. The file names the flows; unit and category are not in it, they
are set per flow when building. Rows that do not fit the log are reported and
left out. `data/flow_records/` holds an example for the built-in log
"Automotive Manufacturing".

The builder does not set containment yet: a built sOCEL keeps the containment
its source log holds, which for a plain log is none.

Everything a user decides is a rule on the type level (activity, object type,
flow), and no response should grow with the number of events or objects: logs
with hundreds of thousands of each are normal.

A log is downloaded through Ocelescope's own download, which keeps the sOCEL
tables; the module has no export of its own (the request's log is read-only).

OCEAn, the earlier object-centric emission analysis, is parked as a module of
its own in the repository's `legacy/` folder (see its README).

## Rules

- Dependencies point inwards: `module` -> `api` -> `application` -> `domain`.
  A use case that needs something from outside declares a port in
  `application/ports/`; its adapter goes in `infrastructure/`, between `api` and
  `application`.
- `domain` and `application` never import `fastapi`, `ocelescope_backend` or
  `pydantic`: plain dataclasses. A domain model subclasses `Model` and only
  lists its fields: the base makes it a frozen, keyword-only dataclass, as
  `Command` does for commands.
- Routes get their use cases from `api/dependencies.py`, never build them.
- An endpoint only runs its use case and maps the result. A use case gets
  everything it works on - the sOCEL and any input - as one `<Action>Command`,
  defined next to it; its constructor is for ports. A command subclasses
  `Command` and only lists its fields: the base makes it a frozen, keyword-only
  dataclass.
- Computations on an sOCEL belong in the `socel` library, not here.
- Use cases return finished data, nothing lazy: the request's OCEL is closed when
  the request ends.

`pnpm run check:backend` (repository root) runs ruff, pyright and
import-linter; the rules above are import-linter contracts in `pyproject.toml`.

## Adding an endpoint

1. New data in `domain/models/`, as subclasses of `Model`.
2. `application/use_cases/<action>.py`: the `<Action>Command(Command)` (the
   sOCEL plus any input) and the use case class with `execute(command)`. Errors of its own go in
   `domain/exceptions.py`, mapped to HTTP statuses in
   `api/exception_handlers.py`.
3. A port in `application/ports/` if the use case needs something from outside.
   Its adapter goes in `infrastructure/`.
4. `api/dependencies.py`: a `get_<action>` function building the use case.
5. `api/routes/<resource>.py`: request/response models (`ApiModel`) and the
   route with a stable `operation_id` (it names the generated frontend hook);
   a new routes file is included in `api/router.py`.
6. `pnpm --filter @instance/socel-module build` regenerates the frontend client.
