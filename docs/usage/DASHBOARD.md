# Dashboard

The dashboard is a Next.js app backed by generated demo data.

```bash
python scripts/seed_demo_data.py
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

The first screen shows loss, recall, queue pressure, graph evidence, ring activity, the case
queue, defense results, and the run memo. The scenario selector summarizes the implemented
benchmark questions, and graph nodes or case rows can be opened into an evidence drawer for
linked accounts, merchants, alerts, recent events, exposure, and review notes.

When the FastAPI service is running, the dashboard also starts scenario jobs, polls job
status, loads the completed run from SQLite, shows persisted run history, and can launch a
multi-seed benchmark report. If the API is not reachable, it keeps showing the bundled demo
run.

To use live API mode locally:

```powershell
cd frontend
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm run dev
```
