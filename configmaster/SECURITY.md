# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately rather than opening a public GitHub issue.

Private vulnerability reporting is enabled on this repository, please use GitHub's private
reporting feature (Security tab then "Report a vulnerability") to submit your report. If
you are unable to use that feature, contact the maintainer directly at
[@itzyeboiabraham](https://github.com/itzyeboiabraham).

Include enough information to reproduce the issue, such as:

- A description of the vulnerability
- Steps to reproduce it
- The affected command, file, or component
- The potential security impact
- Any relevant logs or proof-of-concept information that does not contain real secrets

Do not include passwords, API keys, private keys, credentials, or other sensitive
information in the report.

An expected response time has not yet been defined for this project; reports will be
acknowledged as soon as possible.

## Client specification files

`config/client-spec.json` is the runtime client specification used by ConfigMaster to
determine required fields, field types, and merge strategies.

Client specification files and configuration overlays must not contain secrets such as
passwords, API keys, private keys, or credentials.

Runtime and local overlay files should be kept outside source control. The repository's
`.gitignore` excludes files under `data/` except `data/.gitkeep`.

The `CONFIGMASTER_SPEC` environment variable can be used to select a local specification
file without changing the default committed specification.

Before committing configuration or specification changes, verify that they do not
contain secrets or other sensitive client information.

## Scope limitations

ConfigMaster is a local configuration management CLI. Version 1 supports local JSON
configuration files and does not provide:

- Secret storage or secret management
- Encryption of secrets
- Remote or HTTP-based configuration sources
- A graphical interface
- YAML configuration

ConfigMaster should therefore not be treated as a secrets manager, remote configuration
service, or production configuration database.

Security controls provided by the project do not replace appropriate credential
management, access control, or secret-management systems.