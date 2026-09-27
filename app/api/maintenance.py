from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domain.maintenance import (
    MaintenanceJob,
    MaintenanceJobStatus,
    MaintenanceWorker,
    WorkerStatus,
)

router = APIRouter(
    prefix="/api/maintenance",
    tags=["maintenance"],
)


class CreateMaintenanceJobRequest(BaseModel):
    battery_id: str
    reason: str = "Battery unavailable"
    priority: int = Field(default=5, ge=1, le=5)


class MaintenanceJobResponse(BaseModel):
    job_id: str
    battery_id: str
    reason: str
    priority: int
    status: str
    worker_id: str | None = None


# Demo worker registry.
# This module is intentionally self-contained and does not modify
# the existing battery, fleet, grid, storm, or main API modules.
_workers: dict[str, MaintenanceWorker] = {
    "WORKER-001": MaintenanceWorker(
        worker_id="WORKER-001",
        name="Maintenance Team Alpha",
        phone="+1-555-0101",
    ),
    "WORKER-002": MaintenanceWorker(
        worker_id="WORKER-002",
        name="Maintenance Team Beta",
        phone="+1-555-0102",
    ),
    "WORKER-003": MaintenanceWorker(
        worker_id="WORKER-003",
        name="Maintenance Team Gamma",
        phone="+1-555-0103",
    ),
}

_jobs: dict[str, MaintenanceJob] = {}


def _job_response(job: MaintenanceJob) -> MaintenanceJobResponse:
    return MaintenanceJobResponse(
        job_id=job.job_id,
        battery_id=job.battery_id,
        reason=job.reason,
        priority=job.priority,
        status=job.status.value,
        worker_id=job.worker_id,
    )


@router.get("/workers")
def list_workers() -> dict:
    return {
        "count": len(_workers),
        "workers": [
            {
                "worker_id": worker.worker_id,
                "name": worker.name,
                "status": worker.status.value,
                "phone": worker.phone,
                "skills": list(worker.skills),
            }
            for worker in _workers.values()
        ],
    }


@router.get("/jobs")
def list_jobs() -> dict:
    jobs = sorted(
        _jobs.values(),
        key=lambda job: (-job.priority, job.job_id),
    )

    return {
        "count": len(jobs),
        "jobs": [_job_response(job) for job in jobs],
    }


@router.post("/jobs", response_model=MaintenanceJobResponse)
def create_job(request: CreateMaintenanceJobRequest) -> MaintenanceJobResponse:
    job_id = f"MAINT-{len(_jobs) + 1:04d}"

    job = MaintenanceJob(
        job_id=job_id,
        battery_id=request.battery_id,
        reason=request.reason,
        priority=request.priority,
    )

    _jobs[job_id] = job

    return _job_response(job)


@router.post("/jobs/{job_id}/assign", response_model=MaintenanceJobResponse)
def assign_worker(job_id: str) -> MaintenanceJobResponse:
    job = _jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Maintenance job not found.")

    if job.status not in {
        MaintenanceJobStatus.CREATED,
        MaintenanceJobStatus.ASSIGNED,
    }:
        raise HTTPException(
            status_code=409,
            detail=f"Job cannot be assigned while status is {job.status.value}.",
        )

    if job.worker_id:
        worker = _workers.get(job.worker_id)
        if worker:
            return _job_response(job)

    available_worker = next(
        (
            worker
            for worker in _workers.values()
            if worker.is_available
            and "battery_repair" in worker.skills
        ),
        None,
    )

    if available_worker is None:
        raise HTTPException(
            status_code=409,
            detail="No maintenance worker is currently available.",
        )

    available_worker.status = WorkerStatus.ASSIGNED
    job.worker_id = available_worker.worker_id
    job.status = MaintenanceJobStatus.ASSIGNED

    return _job_response(job)


@router.post("/jobs/{job_id}/start", response_model=MaintenanceJobResponse)
def start_job(job_id: str) -> MaintenanceJobResponse:
    job = _jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Maintenance job not found.")

    if job.status != MaintenanceJobStatus.ASSIGNED:
        raise HTTPException(
            status_code=409,
            detail="A job must be assigned before work can start.",
        )

    job.status = MaintenanceJobStatus.IN_PROGRESS
    return _job_response(job)


@router.post("/jobs/{job_id}/complete", response_model=MaintenanceJobResponse)
def complete_job(job_id: str) -> MaintenanceJobResponse:
    job = _jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Maintenance job not found.")

    if job.status != MaintenanceJobStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail="A job must be in progress before it can be completed.",
        )

    job.status = MaintenanceJobStatus.COMPLETED

    if job.worker_id:
        worker = _workers.get(job.worker_id)
        if worker:
            worker.status = WorkerStatus.AVAILABLE

    return _job_response(job)
