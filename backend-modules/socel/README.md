# sOCEL backend module

Sustainability analysis of object-centric event logs for Ocelescope, mounted at
`/modules/socel/v1`, using FastAPI and hexagonal architecture. DuckDB performs
bulk data processing; Ocelescope supplies `ApiOcel` and session storage.

The refactor is incremental. [The migration plan](../../migration-plan.md) tracks
the agreed architecture, sequence, and retained capabilities. All operations reuse
Pydantic domain models, wrapped in plain dataclass commands at application entry points. HTTP
pagination and small creation envelopes belong to the API. The retained sOCEL
schema, conformance, host extension, taxonomy, and bulk quantification now live
inside this backend. The standalone `socel` package and its vendored source have
been removed. Attribution, allocation, and product footprints are not active
backend features; their original implementation remains in the separate sOCEL
project.

```text
src/ocelescope_module_socel/
├── module.py                Ocelescope module and extension registration
├── domain/
│   ├── models/              Pydantic values, invariants, and owned behavior
│   ├── services/            Ordinary classes for ownerless business algorithms
│   ├── taxonomies.py         Shared built-in domain definitions
│   └── exceptions.py
├── application/
│   ├── ports/               All external capabilities, including workspaces
│   ├── workflows/           Internal coordination shared by use cases
│   └── use_cases/           Entry operations + dataclass commands
├── infrastructure/
│   ├── adapters/            <technology>_<port>.py, including host workspaces
│   ├── conformance/         V1–V10, prerequisite handling, aggregated diagnostics
│   ├── ocelescope_extension.py  Thin OCEL subtype recognized by the host
│   └── schema.py            Stored extension table/column definitions
└── api/
    ├── dependencies.py      Request context and concrete use-case assembly
    ├── router.py
    ├── exception_handlers.py
    ├── models/              Shared pagination and contextual page wrappers
    ├── schema.py            Base for HTTP functionality schemas
    └── routes/              One endpoint per file; shared resource prefixes
```

## HTTP resources

`api/router.py` composes log resources under `/logs/{ocel_id}` once. Endpoint
files contain one operation and use shared models directly. Operation IDs stay
stable so generated hook names are unchanged.

| Method and path (relative to the module mount) | Result |
| --- | --- |
| GET `/taxonomy` | Class and flow-category trees |
| GET `/logs/{ocel_id}/summary` | Log counts and record time range |
| GET `/logs/{ocel_id}/class-counts` | Full class paths and counts, including unclassified entities; no root-specific flags |
| GET `/logs/{ocel_id}/classification` | Current classes by activity/object type |
| GET `/logs/{ocel_id}/flows` | Flow inventory |
| GET `/logs/{ocel_id}/flows/{flow_id}/instances` | Shared page of domain items plus containment path |
| POST `/logs/{ocel_id}/derivations` | `201`, new log identity and a readable `Location` |
| PATCH `/logs/{ocel_id}/socel` | `204`, apply partial configuration to the original log |
| POST `/logs/{ocel_id}/record-uploads` | `201`, uploaded file identity and metadata |
| POST `/logs/{ocel_id}/record-uploads/{upload_id}/preview` | Completed preview |
| POST `/logs/{ocel_id}/impact` | Completed impact report |

Pages contain `items`, `total`, `offset`, and `limit`; instance pages also carry
`path` breadcrumbs. A page beyond the end keeps the filtered total. A missing
flow returns `404`; a valid flow with no matches returns an empty page.
Pagination defaults to 50 and accepts 1–200 items. The frontend requests 25
items for its instance table. Build still receives the selected view through
`ApiOcel`; configuring an existing log always uses its complete original view.

## The sOCEL extension

The module declares `extensions = [SOCEL]` (`module.py`), using its own thin
`infrastructure/ocelescope_extension.py` type. The host then
recognizes sOCELs among the logs - `SOCEL.from_ocel` runs `SOCEL.validate`, the
declared tables plus the conformance rules - and lists the extension in a log's
metadata, which the frontend reads. The frontend guards its pages with it
(`requiresOcel: ["socel"]`), so they only open on an sOCEL.

Endpoints ask for `ApiSocel` (`api/dependencies.py`) and get the log as a
`SOCEL`; a log that is none is rejected with HTTP 422 and the reason before the
use case is built, so use cases never check for it. The check takes seconds on
a large log, so the module runs it once per log and not on every request: a
session's logs are files that are written once.

The counts of the overview (`status`, `flows`, `classes`) come from aggregate
queries behind the port `SocelStatistics`. The extension installs no
record-by-record manager facade. `flows`
breaks a flow down by object type. Single objects come a page at a time from
`flows/{flow_id}/instances`, filtered by object type, by the object they lie
inside, or by a search in the object id.

An sOCEL is built from any log (`build_socel`): the request's log is read-only,
so the use case works on a copy and adds the result to the session as a new log.

Flow records come from one CSV with the columns `flow`, `object`, `quantity`,
`start_time`, `end_time` and `event`. A row is one of:

- an interval record: `flow`, `object`, `quantity`, `start_time`, `end_time`;
- an event-linked record: `flow`, `object`, `quantity`, `event`, and
  `end_time` if the event has a duration;
- an event's end alone: `event` and `end_time`, nothing else. Events without a
  record of their own get their duration this way.

`object` and `event` are ids of the log, times are ISO 8601 with an offset, and
the quantity is the amount in the interval. The file names the flows; what it
cannot know about a flow is set per flow when building: unit, category and, if
wanted, an external reference. An event's end goes into the event attribute
`socel_end_time`. Rows that do not fit the log are reported and left out, among
them ends before the event's start and two different ends for one event.
`data/flow_records/` holds an example for the built-in log "Automotive
Manufacturing".

The builder can infer flow containment from configured object-type relationships.

Everything a user decides is a rule on the type level (activity, object type,
flow), and no response should grow with the number of events or objects: logs
with hundreds of thousands of each are normal.

Logs use Ocelescope's own download. Populated XML/SQLite round trips preserve
sOCEL data, including classification, event ends, external references, and
containment. The pinned host currently loses extension timestamp types in JSON
and omits empty extension tables in all three formats. Those affected round trips
lose sOCEL recognition. Seven strict expected-failure cases in
[the host integration tests](tests/test_host_integration.py) document these limitations; the
module keeps its full conformance checks.

OCEAn, the earlier object-centric emission analysis, is parked as a module of
its own in the repository's `legacy/` folder (see its README).

## Rules

- The complete backend is independent of the standalone `socel` library.
  Dependencies point inward. Domain models and services contain no FastAPI,
  Ocelescope, DuckDB, or connection-backed `socel` imports. Pydantic is a deliberate
  domain dependency. Every application port and use case has the same
  independence. Domain code never imports application, including its ports.
- Models own their invariants and naturally owned operations. For example,
  `DirectionFactors.apply(...)` distinguishes absent factors from zero,
  `ColumnMapping.is_readable()` owns mapping completeness, and `FlowEdit` owns
  name/unit normalization and valid conversion factors.
- Public domain services are always ordinary classes, stateless or holding
  immutable configuration. `ImpactCalculator.calculate(...)` combines flows and
  periods; `PreparationValidator.prepare(...)` checks supplied log facts, taxonomy
  references, and resulting flow names. Private helper functions remain allowed.
  Internal calculations need no service superclass or port.
- Use cases coordinate ports and domain behavior through `execute(command)`.
  Every command is an ordinary dataclass defined beside its use case, solely
  holding parameters. Commands may hold domain models, such as
  `CalculateImpactCommand(analysis=...)`, but never validate, normalize, inherit
  domain models, or carry live logs, sessions, adapters, or connections.
  Shared internal coordination lives in `application/workflows/`.
- `domain/taxonomies.py` holds one fixed immutable `TAXONOMY`. Construct nested
  `ClassNode(label=..., children=...)` values directly; leaves need only a label.
  Nodes store no full path: `paths(parent_path="")` reconstructs identifiers during
  traversal. The API returns these local-name trees, and frontend options derive
  their selection values. Preparation, API choices, and conformance share the
  same definition, with no custom-taxonomy injection or signature catalog. The
  summary reads `HANDLING_UNIT_ROOT` and `OPERATION_ROOT` from this module; these
  are the same nodes used in the taxonomy, so their labels are defined only once.
- Database conformance uses explicit `Valid()` / `Invalid(issues)` results and an
  ordered pipeline. Success has no payload; `combine` accumulates issues directly. The ten named checks live in `infrastructure/conformance/rules/`,
  accumulating independent issues and skipping checks with failed prerequisites.
- Ports describe external capabilities using structural protocols. Adapters do
  not inherit them. All ports live in `application/ports/`. Adapters live under
  `infrastructure/adapters/` using the technology/port naming convention.
- Routes get assembled use cases from `api/dependencies.py` and reuse domain
  models directly. `api/models/pagination.py` owns `Pagination` and `Page[T]`;
  its shared policy limits HTTP pages to 200 items. Items are domain models.
  The build route composes its preparation fields with a host log name in
  `BuildSocelRequest`. Its use case returns a string; the route owns `CreatedLog`
  and the Location header. Neither HTTP schema is a domain model or command.
- Return completed results during the request. Future job/CLI entry adapters
  resolve fresh context and invoke the same use cases; no job framework is added
  by this migration.
- `SocelWorkspace` owns one lazy working copy. The `ApplySocelChanges` workflow coordinates
  preview, domain preparation, writing, and conformance checks; build/configure
  choose new versus replacement publication. The host owns borrowed source logs.
  Configure explicitly resolves the original log, while build uses `ApiOcel`.
  Registry insertion or replacement handle assignment is the commit point.
  Failed new/replacement writes clean only their tracked files. After commit,
  obsolete-file cleanup and SSE failures are logged without failing publication.
  Deferred file cleanup retries on the next publication using session module
  state. A module lock serializes publication/cleanup; borrowed readers keep
  their snapshot, and replacement rechecks that the host handle still exists.

`pnpm run check:backend` runs ruff, pyright, import-linter, and pytest. Existing
HTTP tests use real DuckDB logs and Ocelescope sessions. Pure domain tests can
run independently of those fixtures from this directory:

```sh
uv run pytest tests/unit --confcutdir=tests/unit -q
```

## Adding an endpoint

1. Define Pydantic domain models with applicable invariants and behavior.
2. For a business algorithm without a natural model owner, add a domain service
   class. For an external capability, add an application port and infrastructure adapter.
3. Add a use case under `application/use_cases/`, with injected dependencies and
   `execute(command)`. Define its plain dataclass command beside it, grouping
   parameters and holding existing domain models without copying their fields.
   Put any shared internal coordination under `application/workflows/`.
4. Assemble the request-bound adapters and use case in `api/dependencies.py`.
5. Add the endpoint under `api/routes/`, reusing the input/report models and a
   stable operation ID. One endpoint per file is welcome; no DTO copy is needed.
6. Run the backend checks and `pnpm --filter @instance/socel-module build` to
   regenerate the frontend client, then type-check affected frontend code.
