#!/usr/bin/env python
"""Re-verify all FBbt mappings, and follow up FBbt term requests, when a new FBbt release is out.

Reads the FBbt release last verified from `checks/fbbt_last_checked.json` and asks
OLS for the current FBbt release. If it is the same, exits 0 without checking terms.
If it is new (or nothing is recorded), runs `verify_mappings.verify` for every project
with mappings; when every term is current, non-obsolete and still carries its recorded
label, the record is updated to the new release. If any term fails, the record is NOT
updated (so the next run re-checks) and the exit code is 1.

Pending FBbt new-term requests are listed in `checks/pending_fbbt_requests.json`
(the FBbt GitHub issue, the requested labels, the clusters waiting on them). On a new
release, any request whose FBbt issue was closed on or before the release date is
assumed to be in that release: a reminder issue is opened in this repo listing the
clusters to re-map (with the new term ids where the requested labels are found in
the release), and the request is marked `released` so it is reported only once.
An entry with `"kind": "review"` is an FBbt issue we are waiting on but did not
request (e.g. a review of a group of terms): its reminder lists the mappings to
revisit instead of requested terms.

Usage:
    uv run python scripts/check_fbbt_release.py [--force]
Writes `checked`, `updated` and `changed` (any file under checks/ changed) to
$GITHUB_OUTPUT when set. Reminder issues are opened with the `gh` CLI in
$GITHUB_REPOSITORY (default VirtualFlyBrain/vfb-scRNAseq); with --dry-run they are
only printed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD = REPO_ROOT / "checks" / "fbbt_last_checked.json"
PENDING = REPO_ROOT / "checks" / "pending_fbbt_requests.json"
OLS_FBBT = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt"
OLS_SEARCH = "https://www.ebi.ac.uk/ols4/api/search"


def current_release() -> dict:
    req = urllib.request.Request(OLS_FBBT, headers={"User-Agent": "vfb-scrnaseq/0.0"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        cfg = json.load(r)["config"]
    return {"version": cfg.get("version"), "version_iri": cfg.get("versionIri")}


def _get_json(url: str, token: str | None = None) -> dict:
    headers = {"User-Agent": "vfb-scrnaseq/0.0", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:  # noqa: S310
        return json.load(r)


def fbbt_issue(ref: str) -> dict:
    """GitHub issue `owner/repo#N` -> {state, state_reason, closed_at, html_url}."""
    repo, num = ref.split("#")
    d = _get_json(f"https://api.github.com/repos/{repo}/issues/{num}", os.environ.get("GITHUB_TOKEN"))
    return {k: d.get(k) for k in ("state", "state_reason", "closed_at", "html_url")}


def find_term(label: str) -> str | None:
    """FBbt id whose label (or an exact synonym) is exactly `label`, else None."""
    q = urllib.parse.urlencode({"q": label, "ontology": "fbbt", "exact": "true", "rows": 5,
                                "queryFields": "label,synonym", "fieldList": "obo_id,label,is_obsolete"})
    for d in _get_json(f"{OLS_SEARCH}?{q}").get("response", {}).get("docs", []):
        if not d.get("is_obsolete"):
            return d.get("obo_id")
    return None


def open_issue(title: str, body: str, dry_run: bool) -> str:
    if dry_run:
        print(f"[dry-run] would open issue: {title}\n{body}")
        return "(dry-run)"
    repo = os.environ.get("GITHUB_REPOSITORY", "VirtualFlyBrain/vfb-scRNAseq")
    r = subprocess.run(["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body],
                       capture_output=True, text=True, check=True)
    return r.stdout.strip().splitlines()[-1]


def check_pending(release: dict, dry_run: bool = False) -> bool:
    """Open a reminder for each pending request closed on/before this release's date.
    Returns True if the pending file changed."""
    if not PENDING.exists():
        return False
    reqs = json.loads(PENDING.read_text())
    release_end = dt.datetime.fromisoformat(release["version"]).replace(
        tzinfo=dt.timezone.utc) + dt.timedelta(days=1)          # closed on or before the release date
    changed = False
    for req in reqs:
        if req.get("status") != "pending":
            continue
        issue = fbbt_issue(req["fbbt_issue"])
        if issue["state"] != "closed" or not issue["closed_at"]:
            print(f"  request {req['fbbt_issue']}: still open")
            continue
        closed = dt.datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
        if closed >= release_end:
            print(f"  request {req['fbbt_issue']}: closed {issue['closed_at']}, after FBbt {release['version']}; next release")
            continue
        if req.get("kind") == "review":
            # an FBbt issue we are waiting on (not our term request): revisit mappings
            lines = [f"FBbt issue {issue['html_url']} ({req.get('topic', 'review')}) was closed on "
                     f"{issue['closed_at'][:10]}, before FBbt release {release['version']} "
                     f"({release['version_iri']}).", "", "**Mappings to revisit:**"]
            lines += [f"- `{proj}`: " + ", ".join(f"`{c}`" for c in clusters)
                      for proj, clusters in req["clusters"].items()]
            lines += ["", f"Why: {req.get('reason', '')}".rstrip(),
                      "", "_Opened automatically by the weekly FBbt release check._"]
            title = f"Revisit mappings: FBbt {release['version']} closes {req['fbbt_issue']} ({req.get('topic', 'review')})"
            url = open_issue(title, "\n".join(lines), dry_run)
            print(f"  review {req['fbbt_issue']}: closed before FBbt {release['version']} -> {url}")
            if not dry_run:
                req.update(status="released", fbbt_release=release["version"], reminder_issue=url,
                           closed_at=issue["closed_at"])
                changed = True
            continue
        terms = {lab: find_term(lab) for lab in req["labels"]}
        lines = [f"FBbt request {issue['html_url']} was closed on {issue['closed_at'][:10]}"
                 f"{' (as ' + issue['state_reason'] + ')' if issue.get('state_reason') else ''}, "
                 f"before FBbt release {release['version']} ({release['version_iri']}), "
                 f"so the requested terms should now be available.", "", "**Requested terms in this release:**"]
        lines += [f"- {lab}: {tid or 'not found by exact label - check the FBbt issue for the name used'}"
                  for lab, tid in terms.items()]
        lines += ["", "**Clusters to re-map:**"]
        lines += [f"- `{proj}`: " + ", ".join(f"`{c}`" for c in clusters)
                  for proj, clusters in req["clusters"].items()]
        lines += ["", f"Requested for: {req.get('reason', '')}".rstrip(),
                  "", "_Opened automatically by the weekly FBbt release check._"]
        title = f"Re-map clusters: FBbt {release['version']} closes {req['fbbt_issue']} ({', '.join(req['labels'])})"
        url = open_issue(title, "\n".join(lines), dry_run)
        print(f"  request {req['fbbt_issue']}: closed before FBbt {release['version']} -> {url}")
        if not dry_run:
            req.update(status="released", fbbt_release=release["version"], reminder_issue=url,
                       terms_found=terms, closed_at=issue["closed_at"])
            changed = True
    if changed:
        PENDING.write_text(json.dumps(reqs, indent=2) + "\n")
    return changed


def _verify_module():
    spec = importlib.util.spec_from_file_location(
        "verify_mappings", REPO_ROOT / "scripts" / "verify_mappings.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _output(**kv) -> None:
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            fh.writelines(f"{k}={str(v).lower()}\n" for k, v in kv.items())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="verify even if the release is unchanged")
    ap.add_argument("--dry-run", action="store_true", help="print reminder issues instead of opening them")
    args = ap.parse_args()

    record = json.loads(RECORD.read_text()) if RECORD.exists() else {}
    rel = current_release()
    if not rel["version"]:
        print("could not read the current FBbt version from OLS")
        return 1
    if rel["version"] == record.get("version") and not args.force:
        print(f"FBbt {rel['version']} already verified on {record.get('checked_at')}; nothing to do")
        _output(checked=False, updated=False, changed=False)
        return 0

    print(f"Pending FBbt term requests vs FBbt {rel['version']}:")
    pending_changed = check_pending(rel, dry_run=args.dry_run)

    print(f"FBbt {rel['version']} (last verified: {record.get('version') or 'never'}) — verifying all mappings")
    verify = _verify_module().verify
    projects = sorted(p.parent.name for p in (REPO_ROOT / "projects").glob("*/mapping"))
    results, failed = {}, False
    for project in projects:
        terms, problems = verify(project)
        results[project] = {"terms": len(terms), "problems": len(problems)}
        print(f"  {project}: {len(terms)} terms, {len(problems)} problem(s)")
        for fid, msg, info in problems:
            ex = ", ".join(info["clusters"][:6]) + ("..." if len(info["clusters"]) > 6 else "")
            print(f"    {fid}: {msg}  [used by: {ex}]")
        failed |= bool(problems)

    if failed:
        print("\nSome FBbt terms need attention; record not updated (next run re-checks).")
        _output(checked=True, updated=False, changed=pending_changed)
        return 1

    RECORD.parent.mkdir(exist_ok=True)
    RECORD.write_text(json.dumps({
        "version": rel["version"],
        "version_iri": rel["version_iri"],
        "checked_at": dt.date.today().isoformat(),
        "source": OLS_FBBT,
        "projects": results,
    }, indent=2) + "\n")
    print(f"\nAll terms OK; recorded FBbt {rel['version']} in {RECORD}")
    _output(checked=True, updated=True, changed=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
