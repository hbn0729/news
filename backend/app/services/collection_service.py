from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.manager import CollectorManager


class CollectionService:
    def __init__(self, db: AsyncSession, *, log_session_maker=None):
        self._db = db
        self._log_session_maker = log_session_maker

    async def trigger(self, *, source: str | None) -> dict:
        manager = CollectorManager(self._db, log_session_maker=self._log_session_maker)

        if source:
            articles = await manager.collect_from(source)
            return {"source": source, "new_articles": len(articles)}

        results = await manager.collect_all()
        return {source_name: len(articles) for source_name, articles in results.items()}
