# sOCEL backend refactoring plan

Date: 14 October 2026  
Scope: the sOCEL backend module, `backend-modules/socel/src/ocelescope_module_socel/`.  
Status: proposed; nothing has been changed yet.

## 1. Direction

The module is already hexagonal. It has domain, application, infrastructure and api layers, `Protocol` ports, a composition root in `api/dependencies.py`, and three import-linter contracts. This plan refines that structure; it does not migrate to a new one.

- **The `socel` library stays its own package.** It is developed in the sibling `sOCEL` folder, with its own tests, and is copied into `packages/sOCEL`. The library owns the sOCEL format: schema, conformance rules, taxonomy, analysis kernels, and the `SOCEL` extension class. The module owns use cases, adapters and HTTP. The module does not edit the library; what it needs from the library is listed in section 6 as requests.
- **Functional core, imperative shell.** Keep pure Python for rules that really are pure: impact policy, validating a change set, flow edits, taxonomy membership. Log-wide checks and aggregates stay in SQL (logs have about 200k events and 700k objects). SQL is the implementation, not a second copy of a Python rule. It is tested against small DuckDB fixtures; DuckDB runs in-process, so these tests are fast.
- **Layer-first, one path for every operation.** The top level stays `domain/`, `application/`, `infrastructure/` and `api/`. Every operation, read or write, goes from endpoint to use case to port to adapter, even when the use case only forwards one call. Consistency is worth the thin files.
- **One concern per file.** Every port, adapter, use case, rule and endpoint has its own file. Files are never merged to lower the file count.
- **One client.** The frontend's API client is generated in this repository. Routes change together with the client in one commit, with no aliases, deprecated operations or versioned contract.

Out of scope: merging the library into the module, ETag/If-Match concurrency control, compatibility routes, background jobs, changing sustainability formulas, and changing upload retention.

## 2. Target layout

```text
ocelescope_module_socel/
├── module.py                     # registers the module and the SOCEL extension
├── domain/
│   ├── models/                   # frozen dataclasses with their own invariants
│   ├── services/                 # pure rules spanning several models, one per file
│   │   ├── impact.py             # directional impact policy (step 2)
│   │   ├── check_classes.py      # step 3
│   │   ├── check_flow_edits.py
│   │   └── check_flow_definitions.py
│   └── errors.py                 # with a stable `code` per error
├── application/
│   ├── use_cases/                # one module per operation, as now
│   ├── workflows/
│   │   └── apply_socel_changes.py
│   ├── changes/                  # socel_changes.py, records_to_import.py
│   ├── results/                  # counts, pages, previews (projections, not domain)
│   └── ports/                    # including the opaque log handle (step 4)
├── infrastructure/
│   ├── duckdb/                   # the current duckdb_* adapters
│   └── ocelescope/               # session log store, workspace, uploads, validation cache
└── api/
    ├── router.py                 # includes the resource routers
    ├── dependencies.py           # composition root
    ├── errors.py                 # domain/application errors -> problem+json
    ├── shared/                   # only DTOs that several endpoints really share
    ├── logs/                     # one file per endpoint: route + its Request/Response
    ├── flows/
    ├── records/
    ├── analysis/
    └── taxonomy/
```

## 3. Dependency rules

- Domain imports only the standard library and the pure parts of `socel`: `socel.taxonomy` and `socel.domain`.
- Application imports domain and its own ports. It does not import `ocelescope`, `duckdb`, `socel.socel`, `socel.managers`, `socel.schema`, `socel.validation`, or `socel.analysis`.
- Infrastructure may use all of the library. Only `api/dependencies.py` and `module.py` know concrete adapters.

To enforce rules about library submodules, `socel` must be a root package of the import-linter config rather than an external one. External packages can only be forbidden as a whole. Step 4 adds:

```toml
[tool.importlinter]
root_packages = ["ocelescope_module_socel", "socel"]
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Application and domain see no database, host or connection-backed library parts"
type = "forbidden"
source_modules = ["ocelescope_module_socel.application", "ocelescope_module_socel.domain"]
forbidden_modules = [
  "fastapi", "pydantic", "ocelescope", "ocelescope_backend", "duckdb",
  "socel.socel", "socel.managers", "socel.schema", "socel.validation", "socel.analysis",
]
# The thesis' impact function comes from the library (step 2); its module still
# imports SOCEL through allocation (section 6, request 2).
ignore_imports = ["ocelescope_module_socel.domain.services.impact -> socel.analysis.impact"]

[[tool.importlinter.contracts]]
name = "DuckDB and Ocelescope adapters are independent"
type = "independence"
modules = [
  "ocelescope_module_socel.infrastructure.duckdb",
  "ocelescope_module_socel.infrastructure.ocelescope",
]
```

Checked in step 1: with two root packages the three existing contracts still pass. The new forbidden contract fails today, as expected, because application code imports `SOCEL`. Temporary violations go into `ignore_imports` with a comment, not into bridge code. Their number is the remaining work.

Import from submodules, never from the package root. `from socel import DEFAULT_TAXONOMY` imports `socel/__init__.py`, and import-linter follows that through to `socel.socel`, so the contract rejects it. `from socel.taxonomy import DEFAULT_TAXONOMY` passes. At runtime Python still runs `socel/__init__.py`, which imports `SOCEL`, but import-linter does not see that implicit import. The contract keeps the code honest; the runtime import is section 6, request 1.

## 4. Steps

Each step is one reviewable change and leaves the app working.

### Step 1: characterization tests

Write tests that pin down the current behavior before anything moves. The module has no tests today; the library's tests stay in the library.

- Put the tests in `backend-modules/socel/tests/`, add pytest to the dev group, and run it from `check:backend`.
- Fixtures: small logs built in code and written to temporary DuckDB files, and a small record CSV. The fixtures must pass sOCEL validation (for example, V8 rejects an interval record and an event-linked record of one instance that overlap in time).
- Test over HTTP, through the module's own app with a real host `Session` (only `get_session` is overridden). These tests survive steps 2–4 unchanged. In step 5 only `tests/api.py`, which holds the paths, changes.
- Mark known defects as `xfail(strict=True)` with the reason, so a fix shows up as an unexpected pass.
- Cover:
  - Impact: a factor that is absent versus a factor of zero; both directions; shares of a period; records of a nested instance left out.
  - Build versus configure: the filtered source versus the whole log; configure keeps the id and name.
  - Flow edits: rename, delete, conversion, and two flows ending up with the same name.
  - Records: preview counts versus rows actually imported.
  - Failure: a build or configure that fails leaves the old log readable.
- Baselines, recorded 14 October 2026 on the development Mac. Synthetic plant: 200k events, 700k objects, record file with 1.82M rows / 117 MB. The log and records come from `scripts/large_example.py` in git history (`3606593`); its own build step no longer matches the code. Each operation is one HTTP call to the in-process app with a real session:

  | Operation | Time |
  | --- | --- |
  | Upload record file | 0.28 s |
  | Preview record file | 1.10 s |
  | Build sOCEL | 3.77 s |
  | Status, first call (runs validation) | 0.80 s |
  | Status, flows, flow instances page, class counts, classification | 0.02–0.04 s each |
  | Impact per day / per hour | 0.09 s / 0.37 s |
  | Configure (rename a flow) | 1.33 s |
  | Peak memory of the process | 2.4 GB |

Done when: the tests pass on the current code and run in `pnpm run check:backend`.

### Step 2: impact as a pure domain function

- Add `domain/services/impact.py` with the directional policy now in `CalculateImpact.execute()`: one factor per direction, applied to the positive amount; `None` without a factor. The policy is the module's own (it differs from thesis Def. 6.4.1) and is named as such. The thesis function itself still comes from the library (`ImpactFactors`, `impact_quantity`), not rewritten in the module. `socel.analysis.impact` imports `SOCEL` through `allocation`, so this one import is listed in the contract's `ignore_imports` until section 6, request 2 is done.
- `DirectionFactors` checks in `__post_init__` that its factors are finite. The API keeps its own validation for the 422 message.
- `CalculateImpact` gets the quantities through the port and calls the domain function.
- The impact response models use Pydantic `from_attributes`, which replaces the `from_domain()` methods. URL, operation id and response shape stay unchanged.
- Replace the `Model`/`Command` base classes, everywhere at once, with explicit `@dataclass(frozen=True, kw_only=True)`. It is mechanical and only touches a few files.

Done when: the impact tests run without DuckDB, and the OpenAPI schema is unchanged apart from model names that were reviewed.

### Step 3: rules move to their owners

- `can_be_read(mapping)` becomes `ColumnMapping.is_readable`. Use cases stop importing it from the upload use case.
- The checks in `ApplySocelChanges` move to `domain/services/`, one file per rule: `check_classes.py`, `check_flow_edits.py`, `check_flow_definitions.py`. They are functions over plain facts: known activities and object types, known flow ids, the taxonomy. The workflow collects the facts through ports and calls them.
- `SocelChanges` and `RecordsToImport` move to `application/changes/`, one file each. `ApplySocelChanges` moves to `application/workflows/`, and what remains in it is the order of the work: check, classify, edit flows, import records and attributes, set containment, validate.
- Counts, pages and previews move from `domain/models/` to `application/results/`. These are `ClassCounts`, `SocelStatus`, `FlowInstancePage` and `FlowSummary`, plus the preview types in `record_file.py`.
- Every domain error gets a stable `code`, for the problem details in step 5.

Done when: `ApplySocelChanges` holds only orchestration, and the rule tests are plain Python.

### Step 4: log workspace and opaque handle

- Add a port `LogWorkspaces` with `open(source) -> Workspace`, used as a context manager:
  - `Workspace` gives the adapters a working copy.
  - `publish_new(name) -> ocel_id` keeps the copy as a new log; `publish_replacing(ocel_id)` replaces an existing one.
  - Leaving the block without publishing discards the copy and closes its connections.
  - It replaces the context manager in `ApplySocelChanges` together with `LogStore.add/get/replace`.
- The adapter in `infrastructure/ocelescope/` takes over what `SessionLogStore.replace` does today: writing beside the old file, moving the handle, `_drop_filtered()`, deleting the old file, and SSE invalidation, which is sent only after a successful publish. The host-private call stays in this one place.
- Ports take an opaque `LogHandle` defined in `application/ports/`, not `OCEL`/`SOCEL`. Only adapters unwrap it. The host keeps injecting the filtered log (`ApiOcel`, `ocel_as`); the composition root wraps it. Commands do not carry ids just to re-resolve the host's filters.
- Keep one port per file and one adapter per file. `SocelStatistics` and its 400-line adapter currently bundle five unrelated queries; split them into one port and one adapter per query, each used by its own use case.
- Move the validation cache from `api/dependencies.py` to `infrastructure/ocelescope/`. Delete it once the Ocelescope branch validates each log once; `ApiSocel` can then use `ocel_as` again.
- Split `infrastructure/` into `duckdb/` and `ocelescope/`, and add the contracts from section 3.

Done when: application code no longer mentions `OCEL`, `SOCEL`, DuckDB or the host session; the failure tests from step 1 pass; the new contracts pass.

### Step 5: HTTP surface, in one change

- Use one endpoint per file with its own `Request`/`Response`, under `api/<resource>/`. Each resource router sets its prefix and tag once, and `api/router.py` includes the resource routers.
- Operation ids stay the same, so the generated hook names in the frontend stay the same.
- Domain and application errors become `application/problem+json` with their `code`. Domain errors carry no HTTP status.
- Regenerate the client and update frontend calls and query keys in the same commit.

| Now | New | Response |
| --- | --- | --- |
| `GET /taxonomy` | `GET /taxonomy` | `200` |
| `GET /{ocel_id}/status` | `GET /logs/{ocel_id}/summary` | `200` |
| `GET /{ocel_id}/classes` | `GET /logs/{ocel_id}/class-counts` | `200` |
| `GET /{ocel_id}/flows` | `GET /logs/{ocel_id}/flows` | `200` |
| `GET /{ocel_id}/flows/{flow_id}/instances` | `GET /logs/{ocel_id}/flows/{flow_id}/instances` | `200`; unknown flow `404`, no matches an empty page |
| `GET /{ocel_id}/classification` | `GET /logs/{ocel_id}/classification` | `200`, also for plain OCELs |
| `POST /{ocel_id}/socel` | `POST /logs` (source log in the body) | `201` with the new id |
| `PUT /{ocel_id}/socel` | `PATCH /logs/{ocel_id}/socel` | `204`; published atomically |
| `POST /{ocel_id}/flow-records` | `POST /logs/{ocel_id}/record-uploads` | `201` with the upload id |
| `POST /{ocel_id}/flow-records/{upload_id}/preview` | `POST /logs/{ocel_id}/record-uploads/{upload_id}/preview` | `200`, changes nothing |
| `POST /{ocel_id}/impact` | `POST /logs/{ocel_id}/impact` | `200`, computed and not stored |

The PATCH body keeps the current semantics, which the endpoint documents: types not named keep their class, `None` removes a class, flow edits are applied before records are added.

Done when: the frontend builds and type-checks, and the builder, the config page and the overview work in the running app.

## 5. Verification

| Where | Evidence |
| --- | --- |
| Domain | Impact examples (absent versus zero factor, both directions), finite factors, flow-edit and class rules, `ColumnMapping.is_readable` |
| Use cases and DuckDB | Build versus configure, filtered versus whole log, flow edits, imported rows matching the preview, pagination past the last page |
| Workspace | A failure before publishing leaves the old log readable, connections and temporary files are released, invalidation is sent only after publishing |
| HTTP | Status codes and bodies per route, problem details, unchanged operation ids |
| Scale | Large-log timings within reach of the step 1 baselines; no per-instance queries or Python loops over records |

Run `pnpm run check:backend` (ruff, pyright, import-linter, tests) and the frontend build after every step.

## 6. Requests to the library (optional, decided by the library's owner)

1. `socel/__init__.py` imports `SOCEL`, and with it DuckDB and Ocelescope. Importing a pure part such as `socel.taxonomy` therefore loads the connection-backed class. Possible fix: keep the pure modules importable without the root re-exports, or make those exports lazy.
2. `ImpactFactors` and `impact_quantity` (`socel.analysis.impact`) are pure but import `socel.analysis.allocation`, which imports `SOCEL`. Moving the pure values into their own module would remove the one `ignore_imports` entry in section 3.

Neither request blocks the steps above.
