# ConfigMaster CLI

## Specification

**Tetteh Abraham Nartey**
GenKey Internship
September 18, 2026

## Purpose

GenKey deploys the same services in different settings and has been experiencing
missing-key failures in production due to manual JSON configuration management.

ConfigMaster is a command-line program that loads JSON configuration layers in
order, deep-merges them, validates the merged result against GenKey's schema,
and outputs the combined JSON so it can be piped directly into deploy scripts.
It is suitable for use inside a deployment pipeline because stdout contains pure
JSON while logs are written to stderr.

## Scope

### In scope for v1

- Loading JSON config files in the order given on the command line
  (defaults, then environment overlay, then an optional local override)
- Deep-merging the loaded layers into one effective document
- Field-level merge behavior read from the schema at runtime:
  `append_list` for fields like `app.features`,
  `fail_on_conflict` for fields like `app.region`,
  and `override` (later layer wins) as the default for everything else
- Validating the effective document against the required fields and types
  defined in `config/client-spec.json`
- Three commands: `validate`, `merge`, and `show`, all of which load and merge
  the given files before acting

### Out of scope for v1

- YAML or any format other than JSON
- Remote or HTTP-based configuration sources
- Encryption of secrets
- A graphical interface

## Command-line interface

### Usage

```text
configmaster validate|merge|show [--spec path] file.json [file.json ...]
```

The spec file defaults to `config/client-spec.json` and can be overridden with
`--spec` or the `CONFIGMASTER_SPEC` environment variable.

All three commands accept one or more files and merge them from left to right.
`validate` does not require a single file; it validates the merged result of
everything supplied.

## Acceptance criteria

### `validate`

- Loads and merges the given files, then runs the schema check against the
  result
- Exits `0` when the merge produced no conflicts and the schema check found no
  issues
- Exits `1` and reports every issue when merge conflicts or schema violations
  exist
- Exits `2` with a usage message when no command, no files, or an unknown
  command is given

### `merge` and `show`

- Run the same load, merge, and validate pipeline as `validate`
- On success, print the merged document as JSON to stdout and exit `0`
- On any issue, print the issue list to stderr and exit `1` without printing
  JSON
- As implemented today, `merge` and `show` are functionally identical; there is
  no behavioral split between them yet

## Stream integrity

- A pipe or redirect, for example:

  ```text
  configmaster show base.json prod.json > effective.json
  ```

  produces a file containing only JSON and no log text mixed in
- All logging, including files loaded, spec used, and issue counts, goes to
  stderr on every run

## Adopting a new client spec JSON

**File path:** `config/client-spec.json`, overridable via `--spec` or
`CONFIGMASTER_SPEC`

**Ownership:** the GenKey platform engineering team maintains and updates this
file.

The CLI parses the specification on every invocation of `validate`, `merge`, or
`show`. Field names, types, and required properties are read at runtime, so
adopting a schema change means replacing the specification file without adding
those field names to the Java implementation.
