# To do

## sOCEL builder: containment

The builder does not fill `socel_containedin` yet: a built sOCEL keeps the
containment its source log holds, which for a plain log is none. Nested
metering (a plant meter that includes hall, line and machine meters) can
therefore not be expressed.

What a solution has to respect, from the attempts so far:

- One rule per flow, never a choice per object: logs have hundreds of
  thousands of objects.
- A real hierarchy is several kinds of relations, one per pair of types
  (machine in line, line in hall, hall in plant), so rules must combine.
- The sOCEL model only defines the table and that it is acyclic. Where the
  containment comes from (object-to-object relations, an attribute, a file) is
  our choice and should be shown as such.
- The records can check a rule: an object around others should read at least
  their sum in every interval.
- The interface has to be understandable without symbols and badges: plain
  labels, and a picture of what lies inside what.
