from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CleanupLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    finished_at: datetime | None
    cutoff_utc: datetime
    retention_days: int
    deleted_count: int
    status: str | None
    error_message: str | None


class CleanupStatsResponse(BaseModel):
    last_started_at: datetime | None
    last_finished_at: datetime | None
    last_status: str | None
    last_deleted_count: int
    last_duration_ms: int | None
    last_cutoff_utc: datetime | None
    last_retention_days: int | None
    last_error_message: str | None
    total_runs: int
    total_deleted: int
