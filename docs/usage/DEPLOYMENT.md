# Deployment

FraudWar Room is designed for local review first.

## Docker Compose

```bash
docker compose up --build
```

Services:

- API: http://localhost:8000
- Dashboard: http://localhost:3000

The API healthcheck waits on:

```text
GET /health
```

Generated local data is mounted into the API container at `/app/data`.

## Local Production Check

```bash
cd frontend
npm run build
npm run start
```

## GitHub Pages

GitHub Pages serves the frontend as a static export. It does not run the FastAPI service,
background jobs, or SQLite writes. The hosted page uses bundled synthetic demo data. Run the
API locally when you want scenario jobs and benchmark jobs.

The workflow is in `.github/workflows/pages.yml`. It builds the Next.js app with:

```bash
GITHUB_PAGES=true npm run build
```

Expected public URL after Pages is enabled:

```text
https://msaule.github.io/fraudwar-room/
```

To enable it in GitHub:

1. Make the repository public, or use a GitHub plan that supports Pages from private repos.
2. Open repository settings.
3. Go to Pages.
4. Set Source to GitHub Actions.
5. Run the `pages` workflow from the Actions tab if it has not run yet.

## Safety Notes

Do not deploy with real customer, payment, platform, credential, or fraud-case data. The
project is a synthetic defensive simulator only.
