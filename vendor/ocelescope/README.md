# Vendored Ocelescope frontend packages

`@ocelescope/core`, `@ocelescope/api-base`, `@ocelescope/management` and
`@ocelescope/resources` from the branch `feat/ocel-extensions` of
promi4s/ocelescope (commit 78e3624), which is 0.10.1 plus OCEL extensions and
the new pickers and charts. They are the packages that differ from the
published 0.10.1; everything else comes from npm. `pnpm-workspace.yaml` maps
them in through `overrides`.

Tarballs instead of a link to the checkout, so that the packages install with
this workspace's own React and Mantine: a linked package would resolve them
from the other repository, and two copies of React break hooks.

To refresh after a change on the branch, in a checkout of it:

```bash
pnpm build:frontend
for p in packages/core packages/api/base packages/resources modules/management; do
  (cd src/frontend/$p && pnpm pack --pack-destination <this folder>)
done
```

then `pnpm install` here. Remove this folder and the `overrides` once a release
includes the extensions.
