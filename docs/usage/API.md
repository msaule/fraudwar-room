# API

Start:

```bash
cd backend
uvicorn fraudwar.main:app --reload
```

Endpoints:

- `GET /health`
- `GET /dashboard/summary`
- `GET /experiments`
- `GET /experiments/{id}`
- `POST /experiments/{id}/run`
- `GET /runs`
- `GET /runs/{id}`
- `GET /runs/{id}/metrics`
- `GET /runs/{id}/rings`
- `GET /runs/{id}/cases`
- `GET /runs/{id}/graph`
- `GET /runs/{id}/timeline`
- `GET /runs/{id}/report`
- `GET /rings/{ring_id}`
- `GET /cases/{case_id}`

