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
- `POST /runs/start`
- `GET /runs`
- `GET /runs/history`
- `GET /runs/{id}`
- `GET /runs/{id}/metrics`
- `GET /runs/{id}/rings`
- `GET /runs/{id}/cases`
- `GET /runs/{id}/graph`
- `GET /runs/{id}/timeline`
- `GET /runs/{id}/report`
- `GET /jobs`
- `GET /jobs/{job_id}`
- `POST /benchmarks/start`
- `GET /benchmarks/latest`
- `GET /rings/{ring_id}`
- `GET /cases/{case_id}`

Run scenario request:

```json
{
  "experiment_id": "static-vs-adaptive",
  "seed": 42,
  "accounts": 900,
  "merchants": 90,
  "transactions": 4500,
  "rings": 5,
  "days": 30
}
```

Benchmark request:

```json
{
  "seeds": [11, 42, 99, 123, 202],
  "experiment_ids": ["static-vs-adaptive", "graph-vs-transaction"],
  "accounts": 600,
  "merchants": 70,
  "transactions": 2400,
  "rings": 5,
  "days": 24
}
```
