# Ocelescope instance template

A starter monorepo for running your own [Ocelescope](https://www.ocelescope.org)
instance and building your own modules.

It's a single repo with two workspaces:

- **Frontend** (pnpm) — the Next.js app in `app/`, plus your custom frontend
  modules in `frontend-modules/`.
- **Backend** (uv) — the published `ocelescope-backend` host, plus your custom
  Python modules in `backend-modules/`.

A bundled **example module** (frontend + backend) shows the full wiring,
including a typed API client. Copy it to start your own.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python ≥ 3.11)
- [pnpm](https://pnpm.io/) ≥ 8 and Node ≥ 20

## Getting started

```bash
cp .env.example .env                 # backend config (optional)
cp app/.env.example app/.env.local   # frontend config (optional)

pnpm run sync                        # install backend + frontend
pnpm run dev                         # run everything
```

The backend runs on <http://localhost:8000>, the frontend on
<http://localhost:3000>.

## Scripts

| Script | What it does |
| --- | --- |
| `pnpm run sync` | Full setup: backend then frontend. |
| `pnpm run dev` | Runs the backend and frontend together. |
| `pnpm run dev:modules` | Watch-rebuild local frontend modules while editing them. |
| `pnpm run build:modules` | Builds local frontend modules (regenerates their API clients). |
| `pnpm run format` | Formats everything: Biome for the frontend, ruff for the backend (also sorts imports). |
| `pnpm run check:backend` | ruff lint, pyright, and the import-linter architecture contracts. |
| `pnpm run check:frontend` | Biome lint, the type check, and the dependency-cruiser architecture rules. |

## Adding a module

**Frontend** — create a package in `frontend-modules/` (use
`frontend-modules/ocean` as a reference), then in `app/`:

1. add it to `dependencies` (`"@instance/your-module": "workspace:*"`),
2. add a path alias to its `src/index.ts` in `app/tsconfig.json`,
3. add it to `transpilePackages` in `app/next.config.ts`,
4. register it in `app/ocelescope.config.ts`.

**Backend** (optional) — copy `backend-modules/example`, rename the package and
its entry point in `pyproject.toml`, add it to the root `pyproject.toml`
(`dependencies` + a `[tool.uv.sources]` `{ workspace = true }` entry), then run
`uv sync`. To call it from the frontend, the module needs an Orval setup
(`orval.config.ts`, `src/lib/fetcher.ts` and a `generate:api` script) like the
Ocelescope docs describe.

The frontend layout is described in `frontend-modules/ocean/README.md`. In short:
code used in one place stays there (page-only parts in the route's folder,
page-only hooks too), and code used in several places
goes to `components/` or `hooks/`.

### Dependency versions

Shared versions (Ocelescope, React, Mantine, ...) live in the `catalog:` of
`pnpm-workspace.yaml`, and every package references them with `"catalog:"`.
Upgrade by editing the catalog and running `pnpm install`. Don't pin versions
in individual packages: the app and modules must share one copy of React and
Mantine.
