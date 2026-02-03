from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cleanup import CleanupLog
from app.repositories.news_repository import NewsRepository
from app.utils.timezone import retention_cutoff_utc


class CleanupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._news_repo = NewsRepository(db)

    async def purge_old_news(self, cutoff_utc: datetime) -> int:
        return await self._news_repo.purge_before(cutoff_utc=cutoff_utc, keep_starred=True)

    async def create_cleanup_log(
        self,
        *,
        started_at: datetime,
        finished_at: datetime | None,
        cutoff_utc: datetime,
        retention_days: int,
        deleted_count: int,
        status: str | None,
        error_message: str | None,
    ) -> CleanupLog:
        log = CleanupLog(
            started_at=started_at,
            finished_at=finished_at,
            cutoff_utc=cutoff_utc,
            retention_days=retention_days,
            deleted_count=deleted_count,
            status=status,
            error_message=error_message,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_cleanup_logs(self, limit: int = 20) -> list[CleanupLog]:
        result = await self.db.execute(
            select(CleanupLog).order_by(CleanupLog.started_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_cleanup_log(self) -> CleanupLog | None:
        result = await self.db.execute(
            select(CleanupLog).order_by(CleanupLog.started_at.desc()).limit(1)
        )
        return result.scalars().first()

    async def get_cleanup_summary(self) -> dict:
        latest = await self.get_latest_cleanup_log()

        total_runs_result = await self.db.execute(select(func.count(CleanupLog.id)))
        total_runs = int(total_runs_result.scalar_one() or 0)

        total_deleted_result = await self.db.execute(
            select(func.coalesce(func.sum(CleanupLog.deleted_count), 0))
        )
        total_deleted = int(total_deleted_result.scalar_one() or 0)

        last_duration_ms = None
        if latest and latest.finished_at:
            last_duration_ms = int(
                (latest.finished_at - latest.started_at).total_seconds() * 1000
            )

        return {
            "latest": latest,
            "total_runs": total_runs,
            "total_deleted": total_deleted,
            "last_duration_ms": last_duration_ms,
        }

    async def run_cleanup(self, *, retention_days: int, tz_name: str) -> dict:
        started_at = datetime.now(timezone.utc)
        deleted = 0
        error_message = None
        status = "success"

        cutoff_utc = retention_cutoff_utc(
            retention_days=retention_days,
            tz_name=tz_name,
        )

        try:
            deleted = await self.purge_old_news(cutoff_utc)
        except Exception as exc:
            status = "failed"
            error_message = str(exc)
            await self.db.rollback()

        finished_at = datetime.now(timezone.utc)
        log = await self.create_cleanup_log(
            started_at=started_at,
            finished_at=finished_at,
            cutoff_utc=cutoff_utc,
            retention_days=retention_days,
            deleted_count=deleted,
            status=status,
            error_message=error_message,
        )

        return {
            "log": log,
            "deleted": deleted,
            "status": status,
        }
