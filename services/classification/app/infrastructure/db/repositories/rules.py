from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import Category, Rule
from app.infrastructure.db.repositories.base import BaseRepository

class CategoryRepository(BaseRepository):
    async def get_by_id(self, category_id: int) -> Category | None:
        """Получает категорию по ID."""
        return await self.db.get(Category, category_id)
    
    async def get_by_name(self, name: str) -> Category | None:
        """Получает категорию по имени."""
        stmt = select(Category).where(Category.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

class RuleRepository(BaseRepository):
    async def get_all_active_rules(self) -> list[dict]:
        """
        Загружает все правила и преобразует в список словарей.
        """
        stmt = (
            select(Rule)
            .options(selectinload(Rule.category))
            .order_by(Rule.priority.asc())
        )
        result = await self.db.execute(stmt)
        rules = result.scalars().all()
        
        return [
            {
                "rule_id": str(rule.rule_id),
                "category_id": rule.category_id,
                "category_name": rule.category.name,
                "pattern": rule.pattern,
                "pattern_type": rule.pattern_type.value,
                "mcc": rule.mcc,
                "priority": rule.priority
            }
            for rule in rules
        ]