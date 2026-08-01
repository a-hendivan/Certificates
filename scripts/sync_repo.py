"""
Pulls PDF certificates from your GitHub repo into ./certificates and
scaffolds metadata.json with sensible defaults for any new PDFs found,
so you only have to fill in the details (title, issuer, date, skills)
once per certificate.

Usage:
    python scripts/sync_repo.py --repo yourname/your-certs-repo
    python scripts/sync_repo.py --repo yourname/your-certs-repo --path certs/  # subfolder in the repo
    python scripts/sync_repo.py --repo yourname/your-certs-repo --token ghp_xxx  # for private repos

Requires only the standard library + `requests` (installed with the
other requirements). Does not require git to be installed.
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CERT_DIR = BASE_DIR / "certificates"
METADATA_PATH = BASE_DIR / "metadata.json"


def gh_api(url: str, token: str | None):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def list_pdfs(repo: str, path: str, token: str | None):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    try:
        entries = gh_api(url, token)
    except urllib.error.HTTPError as e:
        print(f"GitHub API error ({e.code}) fetching {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)

    pdfs = []
    for entry in entries:
        if entry["type"] == "file" and entry["name"].lower().endswith(".pdf"):
            pdfs.append(entry)
        elif entry["type"] == "dir":
            pdfs.extend(list_pdfs(repo, entry["path"], token))
    return pdfs


def download(url: str, dest: Path, token: str | None):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "certificate"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--repo", required=True, help="owner/repo, e.g. jsmith/certifications")
    parser.add_argument("--path", default="", help="subfolder within the repo to scan (default: repo root)")
    parser.add_argument("--token", default=None, help="GitHub token, needed for private repos or to avoid rate limits")
    args = parser.parse_args()

    CERT_DIR.mkdir(exist_ok=True)

    print(f"Scanning {args.repo}/{args.path or '(root)'} for PDFs...")
    pdfs = list_pdfs(args.repo, args.path, args.token)
    print(f"Found {len(pdfs)} PDF(s).")

    existing = []
    if METADATA_PATH.exists():
        existing = json.loads(METADATA_PATH.read_text())
    existing_by_filename = {e["filename"]: e for e in existing}
    used_ids = {e["id"] for e in existing}

    new_count = 0
    for entry in pdfs:
        filename = entry["name"]
        dest = CERT_DIR / filename
        print(f"  downloading {filename}...")
        download(entry["download_url"], dest, args.token)

        if filename in existing_by_filename:
            continue  # already have metadata for this file

        base_id = slugify(filename.rsplit(".", 1)[0])
        cert_id = base_id
        n = 2
        while cert_id in used_ids:
            cert_id = f"{base_id}-{n}"
            n += 1
        used_ids.add(cert_id)

        existing.append({
            "id": cert_id,
            "title": filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title(),
            "issuer": "TODO: fill in issuer",
            "date": "2025-01",
            "category": "General",
            "filename": filename,
            "credential_id": None,
            "credential_url": None,
            "skills": [],
        })
        new_count += 1

    METADATA_PATH.write_text(json.dumps(existing, indent=2))
    print(f"\nDone. {new_count} new certificate(s) added to metadata.json.")
    if new_count:
        print("Open metadata.json and fill in the TODO fields (title, issuer, date, skills) for the new entries.")


if __name__ == "__main__":
    main()
