# Pickers

Drop-in replacements for the pickers in `@ocelescope/core`
(`packages/core/src/components/pickers/`), written so they can be moved there.

- Same file layout, names, props and behaviour as core. Everything added is
  an optional prop whose default keeps core's behaviour, so replacing core's
  pickers with these breaks no caller.
- Two layers, like core: presentational pickers get their items handed in
  (`NamePicker`); one wrapper per endpoint fetches them (`ActivityPicker`, ...).
- Imports only public packages (`@ocelescope/core`, `@ocelescope/api-base`,
  `@r4pm/components`, Mantine), never anything from this module's routes.

Additions over core:

| Picker | Addition |
| --- | --- |
| `NamePicker` and all wrappers | `variant="dropdown"`: a compact r4pm `Combobox` instead of the list |
| `EventAttributePicker`, `ObjectAttributePicker` | `valueTypes` filter; names carried by several types are listed once |
| `E2ORelationPicker` (new) | the object types an activity relates to, per qualifier, as r4pm `CardSelector` cards |
| `RelatedAttributePicker` (new) | an activity's event attributes plus those of its related object types |

When moving to core: replace `useCurrentOcel` from `@ocelescope/core` in
`internal/useOcelId.ts` with core's relative import.
