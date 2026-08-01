# Credential Register

A small FastAPI service that turns your GitHub repo of certificate PDFs into:

- A **REST API** (`/api/certificates`, `/api/certificates/{id}`, `/api/certificates/{id}/pdf`, `/api/certificates/{id}/thumbnail`)
- A **recruiter-friendly HTML page** at `/` — a filterable "credential register" with auto-generated thumbnails of each certificate's first page.

Auto-generated interactive API docs are available at `/docs`.

## 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Pull your certificates from GitHub

This downloads every PDF from your repo into `./certificates` and scaffolds
an entry for each new file in `metadata.json`.

```bash
python scripts/sync_repo.py --repo yourname/your-certs-repo
```

Options:
- `--path certs/` — if your PDFs live in a subfolder of the repo
- `--token ghp_xxx` — needed for private repos (a [fine-grained PAT](https://github.com/settings/personal-access-tokens) with read-only Contents access is enough)

Re-run this any time you add new certificates to the repo — it only downloads
files it doesn't already have, and won't overwrite metadata you've already filled in.

## 3. Fill in the details

Open `metadata.json`. For each new entry, replace the `TODO` placeholders:

```json
{
  "id": "aws-solutions-architect",
  "title": "AWS Certified Solutions Architect – Associate",
  "issuer": "Amazon Web Services",
  "date": "2025-03",
  "category": "Cloud",
  "filename": "aws-solutions-architect.pdf",
  "credential_id": "AWS-123456",
  "credential_url": "https://www.credly.com/badges/...",
  "skills": ["AWS", "Cloud Architecture", "IAM"]
}
```

- `category` powers the filter pills on the page (e.g. "Cloud", "Security", "Data").
- If `credential_id` or `credential_url` is set, the card shows a "Verified" seal.
- Entries are shown newest-first by `date`.

## 4. Run it

```bash
uvicorn app.main:app --reload
```

Visit **http://localhost:8000** for the recruiter view, or **http://localhost:8000/docs** for the API.

## Sharing it with a recruiter

For a quick share without deploying anywhere, run the app and tunnel it:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
# in another terminal:
npx localtunnel --port 8000        # or: ssh -R 80:localhost:8000 serveo.net
```

For something more permanent, this same app deploys as-is to Render, Railway,
Fly.io, or a small VPS — just make sure `certificates/`, `thumbnails/`, and
`metadata.json` are included (or regenerated via `sync_repo.py` on deploy).

## Project layout

```
app/
  main.py          FastAPI app: REST endpoints + HTML view
  models.py        Certificate data model
  thumbnails.py    Renders PDF first page -> PNG, cached
templates/
  index.html       Recruiter-facing page (Jinja2)
static/
  style.css        "Credential register" visual design
scripts/
  sync_repo.py     Pulls PDFs from your GitHub repo, scaffolds metadata.json
certificates/      Your PDF files (populated by sync_repo.py)
thumbnails/         Auto-generated page-1 PNGs (gitignore this)
metadata.json      One entry per certificate — the only file you hand-edit
```
