# Support

> **DRAFT — to be confirmed by the maintainers.** Dates and durations below are
> placeholders proposed for the OSPS Baseline "support scope" item (KPI G3-KR2-I2).

## Getting help

- 📚 Documentation and user guide: https://store.yaci.xyz/
- 💡 Questions and ideas: [GitHub Discussions](https://github.com/bloxbean/yaci-store/discussions)
- 💬 Community chat: [Discord](https://discord.gg/JtQ54MSw6p)
- 🐛 Bugs and feature requests: [GitHub Issues](https://github.com/bloxbean/yaci-store/issues)
- 🔒 Security issues: see [SECURITY.md](SECURITY.md) — never in public issues

## Supported release lines

| Line | Branch | Status | Bug fixes | Security fixes until |
| --- | --- | --- | --- | --- |
| 3.0.x | `main` | Pre-release (beta) | Yes | Ongoing |
| 2.0.x | `release/2.0.x` | Stable | Yes | _TBD by maintainers_ (proposal: 6 months after 3.0.0 GA) |
| < 2.0 | — | End of life | No | No |

When a line reaches end of life it no longer receives security updates; users should upgrade
to the latest stable line.

## Scope of support

Support covers the published release artifacts (JARs, distribution zips, Docker images
`bloxbean/yaci-store*`) running on the documented Java version and databases
(PostgreSQL, MySQL, H2). Custom plugins and forks are supported on a best-effort basis.
