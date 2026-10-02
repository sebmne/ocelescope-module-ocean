# OCEAn page (parked)

The OCEAn page as it was before the sOCEL module was rebuilt. Kept for
reference, not in use: not built, not routed and excluded from tsc, biome and
dependency-cruiser.

`src/` keeps the layout the code had in the module's `src/`: `routes/OceanPage.tsx`,
`features/ocean/`, `data/ocean/` and `model/ocean/`, plus what only this page
used: in `ui/`, the components the module no longer has (ChoiceCards,
ClickableRow, EmptyState, Field, FieldGroup, InfoTip, Notice, NumberField, Panel,
ProportionBar, SideSheet, StatusBadge, SwitchField) and the fuller `Section`
(step, status, actions, footer) and `Stat` (highlight) it relied on; in
`lib/format.ts`, the mass and share formatters. Its imports still point at the
module's `ui/` index, `components/pickers/`, `lib/` and the generated `api/`,
relative to that layout.

To revive it, move these back into the module's `src/` (the two fuller
components replace the module's trimmed ones), export them and the Radix pieces
it uses (Button, Heading, Strong, Table, VisuallyHidden) from `ui/index.ts`
again, add the route to `src/index.ts` and regenerate the API client once the
backend slice is mounted again (see `backend-modules/socel/legacy/ocean/`).
