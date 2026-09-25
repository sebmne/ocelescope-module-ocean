# sOCEL

The OCEL for sustainability analysis: an OCEL 2.0 log with additional tables.

This package is the data standard only. It depends on the `ocelescope` library
(the OCEL), not on the Ocelescope backend, its modules or OCEAn; an
import-linter contract in `pyproject.toml` enforces that.

`pnpm run check:socel` (repository root) runs ruff, pyright and import-linter;
`pnpm run format` formats it along with the rest.
