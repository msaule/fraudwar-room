# Deployment

FraudWar Room is designed for local demo and private portfolio review first.

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

## Safety Notes

Do not deploy with real customer, payment, platform, credential, or fraud-case data. The
project is a synthetic defensive simulator only.
