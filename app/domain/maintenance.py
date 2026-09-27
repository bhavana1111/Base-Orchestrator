from dataclasses import dataclass
from enum import Enum


class WorkerStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    OFFLINE = "offline"


class MaintenanceJobStatus(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class MaintenanceWorker:
    worker_id: str
    name: str
    status: WorkerStatus = WorkerStatus.AVAILABLE
    phone: str | None = None
    skills: tuple[str, ...] = ("battery_repair",)

    @property
    def is_available(self) -> bool:
        return self.status == WorkerStatus.AVAILABLE


@dataclass
class MaintenanceJob:
    job_id: str
    battery_id: str
    reason: str
    priority: int
    status: MaintenanceJobStatus = MaintenanceJobStatus.CREATED
    worker_id: str | None = None
