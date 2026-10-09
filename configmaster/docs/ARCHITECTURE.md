# ConfigMaster CLI Architecture

**Tetteh Abraham Nartey**  
GenKey Internship

## Overview

ConfigMaster is a Java 21 command-line tool for loading, merging, and validating layered JSON configuration files.

The application reads one or more configuration files in the order they are supplied, combines them into one effective configuration, checks the result against a client specification, and either prints the merged JSON or reports any issues it finds.

The rules that control validation and merging come from `config/client-spec.json`. This keeps field names and client-specific behavior out of the Java code as much as possible.

## Component Flow

```text
Command-line arguments
        |
        v
ConfigMasterCli
        |
        v
Loader
   |            |
   |            +--> ClientSpec
   |                   |
   |                   +--> schemaVersion check
   |
   +--> ConfigDocument layers
        |
        v
Merger
        |
        v
SchemaValidator
        |
        v
Result
   |
   +--> stdout: merged JSON
   |
   +--> stderr: logs, validation issues, merge issues, and errors
```

## Main Components

### ConfigMasterCli

`ConfigMasterCli` is the entry point of the application.

It handles:

- command-line arguments;
- selecting `validate`, `merge`, or `show`;
- resolving the client spec path;
- loading the client specification;
- checking the specification version;
- loading configuration files;
- running the merge;
- running schema validation;
- printing output to stdout or stderr;
- returning the correct exit code.

The default client specification is:

```text
config/client-spec.json
```

It can also be overridden with:

```text
--spec path
```

or the `CONFIGMASTER_SPEC` environment variable.

### Loader

`Loader` is responsible for JSON input and output.

It uses Jackson to:

- read JSON configuration files into `Map<String, Object>`;
- wrap them in `ConfigDocument`;
- load `config/client-spec.json` into `ClientSpec`;
- convert the merged configuration back to formatted JSON.

If the root JSON value is `null`, ConfigMaster treats it as an empty configuration.

ConfigMaster currently supports JSON only.

### ClientSpec

`ClientSpec` represents the client-defined rules used by ConfigMaster.

It contains:

- `schemaVersion`
- `client`
- `requiredFields`
- `fieldTypes`
- `mergeStrategies`
- `defaultMergeStrategy`

The current scaffold includes values such as:

```json
{
  "schemaVersion": "1.0.0",
  "client": "Northwind Platform",
  "requiredFields": ["app.name", "app.port"],
  "fieldTypes": {
    "app.name": "string",
    "app.port": "integer",
    "app.region": "string",
    "app.features": "array"
  },
  "mergeStrategies": {
    "app.features": "append_list",
    "app.region": "fail_on_conflict"
  },
  "defaultMergeStrategy": "override"
}
```

These values are loaded at runtime, so the application does not need Java code changes every time a client field name changes.

## Why This Extension

For Week 6, I chose to add validation for `schemaVersion`.

The current client brief is JSON-only and explicitly lists YAML as out of scope, so adding YAML would not match the current requirement. The brief also already defines the merge behavior it needs: append feature lists, fail on protected conflicts such as `app.region`, and use override for everything else. Adding another merge strategy would therefore introduce behavior that the current client has not asked for.

The client specification already contains a `schemaVersion` field and is expected to change over time. Before this change, ConfigMaster loaded that value but did not check it. The Week 6 extension adds a compatibility check so ConfigMaster can reject malformed or incompatible specification versions before it starts processing configuration files.

## Schema Version Compatibility

ConfigMaster currently accepts client specification versions in the `1.x.x` range.

Examples that are accepted:

```text
1.0.0
1.2.3
1.10.4
```

A version is rejected if it:

- is missing;
- is blank;
- does not follow `major.minor.patch`;
- uses an unsupported major version.

Examples that are rejected:

```text
2.0.0
1.0
abc
```

The version check runs immediately after the client specification is loaded.

## Merger

`Merger` combines configuration layers from left to right.

For example:

```text
defaults.json
      +
environment.json
      +
local.json
      =
effective configuration
```

Later layers can change earlier values depending on the merge strategy for that field.

Nested objects are merged recursively.

The result is returned as a `MergeResult`, which contains:

- the merged `ConfigDocument`;
- any merge issues.

## Merge Strategies

Merge behavior is controlled by `mergeStrategies` in the client specification.

### override

`override` is the default behavior.

A later value replaces an earlier one.

Example:

```json
{
  "app": {
    "port": 8080
  }
}
```

merged with:

```json
{
  "app": {
    "port": 9090
  }
}
```

produces:

```json
{
  "app": {
    "port": 9090
  }
}
```

### append_list

`append_list` combines arrays instead of replacing them.

Example:

```json
{
  "app": {
    "features": ["metrics"]
  }
}
```

merged with:

```json
{
  "app": {
    "features": ["tracing"]
  }
}
```

produces:

```json
{
  "app": {
    "features": ["metrics", "tracing"]
  }
}
```

If either side is not an array, ConfigMaster records an issue.

### fail_on_conflict

`fail_on_conflict` prevents different values from being silently replaced.

For example, if one layer contains:

```json
{
  "app": {
    "region": "eu-west"
  }
}
```

and another contains:

```json
{
  "app": {
    "region": "us-east"
  }
}
```

ConfigMaster records a conflict.

If both values are the same, no issue is recorded.

## How Strategy Selection Works

`ClientSpec.strategyFor(path)` decides which strategy applies to a dotted path.

For example:

```text
app.features
```

can resolve to:

```text
append_list
```

while:

```text
app.region
```

can resolve to:

```text
fail_on_conflict
```

If no strategy is defined for a field, ConfigMaster uses `defaultMergeStrategy`.

If the default is missing, it falls back to:

```text
override
```

This keeps merge rules data-driven instead of hard-coding field names into the Java implementation.

## Strategy Extension Model

ConfigMaster does not currently have a separate plugin framework.

Its main extension mechanism is the client specification plus the merge strategy names understood by `Merger`.

The flow is:

```text
client-spec.json
      |
      v
ClientSpec.strategyFor(path)
      |
      v
Merger
      |
      +--> override
      +--> append_list
      +--> fail_on_conflict
```

Existing strategies can be assigned to new fields without changing Java code.

Adding a completely new strategy would require:

1. adding the strategy name to `client-spec.json`;
2. implementing the matching behavior in `Merger`.

## SchemaValidator

`SchemaValidator` checks the final merged configuration.

Validation is driven by the client specification.

### Required fields

Fields listed in `requiredFields` must exist in the effective configuration.

Dotted paths are supported, for example:

```text
app.name
app.port
app.database.host
```

### Field types

`fieldTypes` defines the expected type for configured fields.

Supported types are:

```text
string
integer
number
boolean
array
object
```

Optional typed fields are ignored if they are not present.

Validation issues are collected so ConfigMaster can report more than one problem at a time.

## Maps Utility

`Maps` provides helper methods for nested configuration data.

It is used for tasks such as:

- resolving dotted paths;
- deep-copying nested maps.

These helpers are shared by components including `Merger` and `SchemaValidator`.

## Model Records

ConfigMaster uses small records to pass data between components.

### ConfigDocument

Wraps the configuration tree stored as:

```java
Map<String, Object>
```

### MergeResult

Contains:

- the merged `ConfigDocument`;
- merge issues.

### ValidationIssue

Represents a problem using:

- a configuration path;
- an explanatory message.

## Trust Boundaries

ConfigMaster processes files and values that come from outside the Java application, so they should be treated as untrusted input.

### Configuration files

Configuration files can contain:

- missing fields;
- wrong types;
- malformed JSON;
- conflicting values.

Malformed JSON fails during loading before merge or schema validation continues.

### Client specification

`config/client-spec.json` controls validation and merge behavior at runtime.

Because it changes how ConfigMaster behaves, it is also a trust boundary.

The Week 6 `schemaVersion` check adds a basic compatibility guard before the rest of the configuration is processed.

### Local filesystem

ConfigMaster currently works with local files only.

It does not load configuration from:

- HTTP services;
- remote APIs;
- databases;
- cloud configuration services.

### Secrets

ConfigMaster does not encrypt secrets.

Sensitive values should not be committed to source control or stored in unprotected files.

Secret management is outside the current scope.

## Output Boundary

ConfigMaster keeps machine-readable output separate from diagnostics.

### stdout

`merge` and `show` print valid merged JSON to stdout when processing succeeds.

This allows output to be redirected safely, for example:

```text
configmaster show base.json production.json > effective.json
```

### stderr

stderr is used for:

- files-loaded messages;
- specification information;
- validation issues;
- merge conflicts;
- usage errors;
- loading errors.

Keeping these messages out of stdout helps preserve clean JSON output for scripts and pipelines.

## Exit Codes

| Exit code | Meaning |
|-----------|---------|
| `0` | Operation completed successfully |
| `1` | Validation or merge issues were found |
| `2` | Usage, loading, or another execution error |

## Current Extension Points

ConfigMaster can be extended in a few places.

### Client specification

New field paths can be added to:

- `requiredFields`
- `fieldTypes`
- `mergeStrategies`

without hard-coding those names in Java.

### Merge strategies

New merge behavior can be added to `Merger` and selected by name from the client specification.

### Schema versions

The Week 6 version check provides a clear boundary for future specification formats.

If a future spec introduces incompatible behavior, support for the new major version can be added deliberately instead of accepting it silently.

### Loaders

More input formats could be added later if a future client actually needs them.

YAML is not implemented because it is outside the current brief.

## Current Limitations

The current architecture does not include:

- YAML configuration;
- remote or HTTP configuration sources;
- encrypted secret management;
- a graphical interface;
- a general-purpose plugin framework.

These should only be added when there is a clear client requirement for them.

## Week 6 Client Extension

The Week 6 extension adds compatibility checking for `schemaVersion`.

Before this change, ConfigMaster loaded `schemaVersion` but did not use it.

The new validation:

1. requires `schemaVersion` to be present;
2. requires `major.minor.patch` format;
3. accepts supported `1.x.x` versions;
4. rejects unsupported major versions before configuration processing begins.

The extension is covered by tests for:

- `1.0.0`;
- compatible minor and patch versions;
- unsupported major versions;
- malformed versions;
- incomplete versions;
- blank versions;
- missing versions.

This keeps the extension small, matches the existing configuration model, and adds a useful safeguard without introducing behavior that the current client did not request.
