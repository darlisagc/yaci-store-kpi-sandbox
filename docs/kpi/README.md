# KPI checks — how they work

This folder explains the automated evidence behind the BloxBean **Goals 2027** KPIs
(G2 Evolve, G3 Resilience). Every check is read-only and produces evidence you can link
in the monthly report and the quarterly Leapsome update.

| KPI | What it asks | How it is checked | Where to see the result |
| --- | --- | --- | --- |
| G3-KR1 | SBOM on every stable release | `./gradlew cyclonedxBom` (CycloneDX plugin in `build.gradle`); `release.yml` attaches `yaci-store-<version>.cdx.json` to the GitHub release | Release assets; `sbom-osv.yml` validates components + digests |
| G3-KR2 | Scorecard ≥ 7, Maintained / Code-Review / Vulnerabilities ≥ 8 | `.github/workflows/scorecard.yml` (weekly) publishes to api.scorecard.dev | `https://api.scorecard.dev/projects/github.com/<owner>/<repo>`, Security tab |
| G3-KR2-I1 | SECURITY.md with channel + acknowledgement time | `scripts/kpi/kpi_check.py` | KPI report |
| G3-KR2-I2 | User guide, build from source, defect reporting, support scope | `scripts/kpi/kpi_check.py` (README, CONTRIBUTING, SUPPORT.md) | KPI report |
| G3-KR2-I3 | 0 high/critical vulns older than 30 days | `.github/workflows/sbom-osv.yml` scans the SBOM + npm lockfiles with OSV-Scanner weekly; exceptions in `osv-scanner.toml` | Workflow Summary tab, `osv-report` artifact |
| G2-KR2 / G2-KR2-I1 | ≥ 1 stable/beta release; release notes on every stable release | `scripts/kpi/kpi_check.py` (GitHub Releases API) | KPI report |

## OpenSSF Scorecard in 3 sentences

Scorecard runs 18 automated checks (security policy, pinned dependencies, token permissions,
code review, known vulnerabilities, …), scores each 0–10 and combines them, weighted by risk,
into one composite score. The public API `api.scorecard.dev` only has results for repos that
run the Scorecard GitHub Action with `publish_results: true` (or are in OpenSSF's weekly crawl) —
that is why yaci-store returned 404 before this change. To run it locally:
`GITHUB_AUTH_TOKEN=$(gh auth token) scorecard --repo=github.com/bloxbean/yaci-store`.

## Why Scorecard's "Vulnerabilities" is not enough for Java

Scorecard's Vulnerabilities check reads **lockfiles**. Gradle projects have none by default,
so Scorecard only sees the npm lockfiles (docs site, admin UI) and is blind to the Java
runtime dependencies. Scanning the **SBOM** with OSV-Scanner fills the gap — this is the
"upstream check": most findings live in libraries we depend on (Spring Boot, Netty, Tomcat,
Bouncy Castle via cardano-client-lib), and the fix is usually an upgrade.

## Triage workflow (G3-KR2-I3)

1. Weekly `sbom-osv.yml` lists findings with the fixed version.
2. For each high/critical: upgrade, **or** record it in `osv-scanner.toml` as
   `NOT-APPLICABLE` (false positive) or `ACCEPTED` (mitigation + plan), with an `ignoreUntil` date.
3. Quarterly review: count high/critical findings older than 30 days that are neither fixed
   nor documented. Target: 0.

## Running the KPI report

```bash
export GITHUB_TOKEN=$(gh auth token)
python3 scripts/kpi/kpi_check.py bloxbean/yaci-store bloxbean/cardano-client-lib --since 2027-01-01
```

Or run the **KPI report** workflow from the Actions tab (it also runs on the 1st of each month).
