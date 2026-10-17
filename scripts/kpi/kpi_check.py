#!/usr/bin/env python3
"""KPI evidence check for the BloxBean Java tools (Goals 2027, G2/G3).

Read-only: uses only the public GitHub REST API and api.scorecard.dev, so it can
check any repository without cloning it.

Usage:
    python3 scripts/kpi/kpi_check.py bloxbean/yaci-store [bloxbean/cardano-client-lib ...]
        [--since 2027-01-01] [--sbom-since 2027-04-01] [--json out.json]

Set GITHUB_TOKEN to avoid the 60 requests/hour anonymous rate limit.
Writes a Markdown report to stdout (and to $GITHUB_STEP_SUMMARY when set).
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

SCORECARD_COMPOSITE_MIN = 7.0
SCORECARD_CHECKS_MIN = {"Maintained": 8, "Code-Review": 8, "Vulnerabilities": 8}
SBOM_ASSET = re.compile(r"(\.cdx\.(json|xml)|\.spdx(\.json)?|bom\.(json|xml)|sbom)", re.I)


def get(url, token=None):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "bloxbean-kpi-check"})
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def file_text(repo, path, token):
    d = get(f"https://api.github.com/repos/{repo}/contents/{path}", token)
    if not d or isinstance(d, list) or "content" not in d:
        return None
    return base64.b64decode(d["content"]).decode("utf-8", "replace")


def readme_text(repo, token):
    d = get(f"https://api.github.com/repos/{repo}/readme", token)
    return base64.b64decode(d["content"]).decode("utf-8", "replace") if d else ""


def check_security_md(repo, token):
    """G3-KR2-I1: SECURITY.md with a reporting channel and an acknowledgement commitment."""
    text = None
    for p in ("SECURITY.md", ".github/SECURITY.md", "docs/SECURITY.md"):
        text = file_text(repo, p, token)
        if text:
            break
    if not text:
        return [("G3-KR2-I1", "SECURITY.md present", False, "not found")]
    channel = re.search(r"advisories/new|report a vulnerability|security@|mailto:", text, re.I)
    ack = re.search(r"acknowledg\w*[^\n]{0,80}?\d+\s*(business\s+)?(days|hours)", text, re.I | re.S)
    return [
        ("G3-KR2-I1", "SECURITY.md present", True, "found"),
        ("G3-KR2-I1", "SECURITY.md: reporting channel", bool(channel), channel.group(0) if channel else "none found"),
        ("G3-KR2-I1", "SECURITY.md: acknowledgement commitment", bool(ack),
         ack.group(0).replace("\n", " ")[:60] if ack else "no time-bound acknowledgement"),
    ]


def check_docs(repo, token):
    """G3-KR2-I2: OSPS Baseline documentation checklist (presence checks + where found)."""
    readme = readme_text(repo, token)
    contributing = file_text(repo, "CONTRIBUTING.md", token) or ""
    support = file_text(repo, "SUPPORT.md", token) or file_text(repo, ".github/SUPPORT.md", token) or ""
    rows = []
    guide = re.search(r"\b(documentation|user guide|getting started|docs?)\b[^\n]*\]\((https?://[^)]+)\)", readme, re.I)
    rows.append(("G3-KR2-I2", "User guide linked", bool(guide), guide.group(2) if guide else "no docs link in README"))
    build = re.search(r"build(ing)? from source|gradlew[^\n]*build|mvn[^\n]*(install|package)", readme + contributing, re.I)
    rows.append(("G3-KR2-I2", "Build from source", bool(build), build.group(0)[:50] if build else "not found"))
    defects = re.search(r"/issues|report (a )?bug", readme + contributing, re.I)
    rows.append(("G3-KR2-I2", "Defect reporting guide", bool(defects), defects.group(0) if defects else "not found"))
    scope = support or ""
    eol = re.search(r"end of life|security (fixes|updates) until|supported (versions|release lines)", scope, re.I)
    if support and "TBD" not in support:
        rows.append(("G3-KR2-I2", "Support scope + duration", bool(eol), "SUPPORT.md"))
    elif support:
        rows.append(("G3-KR2-I2", "Support scope + duration", False, "SUPPORT.md has TBD placeholders"))
    else:
        rows.append(("G3-KR2-I2", "Support scope + duration", False, "no SUPPORT.md"))
    return rows


def releases(repo, token):
    out, page = [], 1
    while page <= 5:
        d = get(f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}", token) or []
        out += d
        if len(d) < 100:
            break
        page += 1
    return [r for r in out if not r.get("draft")]


def check_releases(repo, token, since, sbom_since):
    """G2-KR2 (>=1 stable/beta), G2-KR2-I1 (release notes), G3-KR1 (SBOM asset)."""
    rel = [r for r in releases(repo, token) if (r.get("published_at") or "") >= since]
    stable = [r for r in rel if not r["prerelease"]]
    rows = [("G2-KR2", f"Releases since {since}", bool(rel),
             f"{len(rel)} total, {len(stable)} stable" + (f", latest {rel[0]['tag_name']}" if rel else ""))]
    no_notes = [r["tag_name"] for r in stable if not (r.get("body") or "").strip()]
    rows.append(("G2-KR2-I1", "Stable releases with release notes", not no_notes and bool(stable),
                 f"{len(stable) - len(no_notes)}/{len(stable)}" + (f"; empty: {', '.join(no_notes[:5])}" if no_notes else "")))
    sb = [r for r in stable if (r.get("published_at") or "") >= sbom_since]
    with_sbom = [r for r in sb if any(SBOM_ASSET.search(a["name"]) for a in r.get("assets", []))]
    rows.append(("G3-KR1", f"Stable releases since {sbom_since} with SBOM asset", bool(sb) and len(with_sbom) == len(sb),
                 f"{len(with_sbom)}/{len(sb)}" + ("" if sb else " (no stable releases in window)")))
    return rows


def check_scorecard(repo):
    """G3-KR2: OpenSSF Scorecard composite >= 7 and named checks >= 8 (from api.scorecard.dev)."""
    d = get(f"https://api.scorecard.dev/projects/github.com/{repo}")
    if not d:
        return [("G3-KR2", "Scorecard published", False,
                 "no result on api.scorecard.dev - add .github/workflows/scorecard.yml with publish_results: true")]
    checks = {c["name"]: c["score"] for c in d.get("checks", [])}
    rows = [("G3-KR2", f"Scorecard composite >= {SCORECARD_COMPOSITE_MIN}", d["score"] >= SCORECARD_COMPOSITE_MIN,
             f"{d['score']} (run {d['date'][:10]}, scorecard {d.get('scorecard', {}).get('version', '?')})")]
    for name, minimum in SCORECARD_CHECKS_MIN.items():
        s = checks.get(name, -1)
        rows.append(("G3-KR2", f"Scorecard {name} >= {minimum}", s >= minimum, str(s)))
    low = sorted((s, n) for n, s in checks.items() if 0 <= s < 5)
    if low:
        rows.append(("G3-KR2", "Lowest checks (info)", None, ", ".join(f"{n} {s}" for s, n in low)))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repos", nargs="+", help="owner/repo")
    ap.add_argument("--since", default="2027-01-01", help="release window start (YYYY-MM-DD)")
    ap.add_argument("--sbom-since", default="2027-04-01", help="SBOM requirement start (YYYY-MM-DD)")
    ap.add_argument("--json", help="also write results to this JSON file")
    a = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    mark = {True: "PASS", False: "FAIL", None: "info"}
    lines, results = [], {}
    for repo in a.repos:
        rows = (check_security_md(repo, token) + check_docs(repo, token)
                + check_releases(repo, token, a.since, a.sbom_since) + check_scorecard(repo))
        results[repo] = [dict(kpi=k, check=c, ok=ok, evidence=e) for k, c, ok, e in rows]
        passed = sum(1 for r in rows if r[2] is True)
        total = sum(1 for r in rows if r[2] is not None)
        lines += [f"## {repo} - {passed}/{total} checks pass", "",
                  "| KPI | Check | Result | Evidence |", "| --- | --- | --- | --- |"]
        lines += [f"| {k} | {c} | {mark[ok]} | {str(e).replace('|', '/')} |" for k, c, ok, e in rows]
        lines.append("")
    report = "\n".join(["# BloxBean KPI check", ""] + lines)
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(report + "\n")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    sys.exit(main())
