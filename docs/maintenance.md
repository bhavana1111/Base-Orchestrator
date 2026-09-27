# Maintenance Worker API

This is an isolated MVP backend module for storm maintenance orchestration.

## What it provides

- Maintenance worker registry
- Maintenance job creation
- Worker assignment
- Work start
- Work completion
- Worker becomes available again after completion

## Endpoints

```text
GET  /api/maintenance/workers
GET  /api/maintenance/jobs

POST /api/maintenance/jobs
POST /api/maintenance/jobs/{job_id}/assign
POST /api/maintenance/jobs/{job_id}/start
POST /api/maintenance/jobs/{job_id}/complete
```

## Important

This package does **not** modify the existing battery, fleet, grid,
storm orchestrator, or main API files.

To expose the endpoints, add the router in your existing FastAPI
application composition layer:

```python
from app.api.maintenance import router as maintenance_router

app.include_router(maintenance_router)
```

The isolated module can also be integrated through a new API composition
file if you want zero changes to the current API implementation.
