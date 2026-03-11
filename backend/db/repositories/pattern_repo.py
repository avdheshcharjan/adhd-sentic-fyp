from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from db.models import BehavioralPattern, InterventionHistory
from .base import BaseRepository

class PatternRepository(BaseRepository[BehavioralPattern]):
    def __init__(self):
        super().__init__(BehavioralPattern)

    async def get_recent_patterns(
        self, db: AsyncSession, limit: int = 10
    ) -> List[BehavioralPattern]:
        """Fetch the most recently detected behavioral patterns."""
        stmt = (
            select(self.model)
            .order_by(desc(self.model.detected_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
        
    async def get_patterns_by_type(
        self, db: AsyncSession, pattern_type: str, limit: int = 10
    ) -> List[BehavioralPattern]:
        """Fetch patterns filtering by type."""
        stmt = (
            select(self.model)
            .where(self.model.pattern_type == pattern_type)
            .order_by(desc(self.model.detected_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
        
    async def get_intervention_history(
        self, db: AsyncSession, limit: int = 20, intervention_type: Optional[str] = None
    ) -> List[InterventionHistory]:
        """Fetch history of interventions and user responses."""
        stmt = select(InterventionHistory)
        
        if intervention_type:
            stmt = stmt.where(InterventionHistory.intervention_type == intervention_type)
            
        stmt = stmt.order_by(desc(InterventionHistory.timestamp)).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

# Singleton instance
pattern_repo = PatternRepository()
