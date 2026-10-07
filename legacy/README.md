# Legacy

Code that is kept for reference but no longer used. Nothing here is part of the
uv or pnpm workspace, so it is not installed, built, mounted or checked.

## OCEAn

OCEAn, the object-centric emission analysis adapted from works by Raimund Hensen,
as a self-contained Ocelescope module - the same layout as the live module, one
level down:

```
legacy/
├── backend-modules/ocean/     ocelescope-module-ocean (pyproject.toml, src/ocelescope_module_ocean)
└── frontend-modules/ocean/    @instance/ocean-module (package.json, src/)
    └── ../tsconfig.base.json  the base its tsconfig.json extends
```

The code is OCEAn as it last ran, at commit `dbf49a5`, when it was one page of
the sOCEL module. It is laid out here as the module of its own it started as
(commit `0ff49d6`): its own package name, module key (`ocean`), entry, theme, UI
components and pickers. The backend's own import contracts (`lint-imports` in
`backend-modules/ocean`) hold; each README inside describes its half.

It was written against Ocelescope 0.8 and has not been ported since. To run it
again:

1. Move the two `ocean` folders next to the live module (`backend-modules/`,
   `frontend-modules/`); the workspace globs then pick them up.
2. Add `ocelescope-module-ocean` to the root `pyproject.toml` (dependency and a
   `{ workspace = true }` source) and the module to `app/ocelescope.config.ts`.
3. Port it to the Ocelescope version in use: since 0.10 a backend module's
   `create_app` is an instance method, the OCEL API changed, and core has its
   own pickers, which can replace `src/components/pickers`.
4. `pnpm --filter @instance/ocean-module build` generates the API client
   (`src/api/ocean.ts`, not in git) and builds the module.
