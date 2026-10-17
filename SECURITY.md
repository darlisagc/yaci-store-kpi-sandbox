# Security Policy

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions or Discord.**

Report them privately using GitHub's **"Report a vulnerability"** button on this
repository's [Security tab](../../security/advisories/new) (GitHub private vulnerability reporting).

Please include:

- the affected version(s) and module(s) (e.g. `yaci-store-utxo`, `applications:all`)
- a description of the issue and its impact
- steps to reproduce or a proof of concept, if available

## What to expect

| Step | Commitment |
| --- | --- |
| Acknowledgement of your report | within **3 business days** |
| Initial assessment (valid / not valid, severity) | within **10 business days** |
| Fix or mitigation for high/critical issues | target **30 days** from confirmation |
| Public disclosure | coordinated with the reporter once a fix is released |

We will keep you informed of progress and credit you in the advisory unless you prefer to remain anonymous.

## Supported versions

Security fixes are provided for the versions listed in [SUPPORT.md](SUPPORT.md).

## Dependency vulnerabilities

Third-party (upstream) dependency vulnerabilities are tracked automatically with
OSV-Scanner on every push and weekly (see `.github/workflows/sbom-osv.yml`).
Findings that are not applicable, or that need more than 30 days to fix, are documented
with a reason and review date in [`osv-scanner.toml`](osv-scanner.toml).
