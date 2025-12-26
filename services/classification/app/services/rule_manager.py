import logging
import re
from datetime import datetime
from app import unit_of_work

logger = logging.getLogger(__name__)

class RuleManager:
    """
    Singleton для управления правилами классификации в памяти.
    Предотвращает нагрузку на БД при каждом запросе.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RuleManager, cls).__new__(cls)
            cls._instance._rules = []
            cls._instance.last_check = datetime.min
            cls._instance.update_interval_seconds = 60
        return cls._instance

    def get_rules(self) -> list[dict]:
        return self._rules

    async def check_for_updates(self, db_session_maker):
        """
        Проверяет и обновляет правила, если прошло достаточно времени.
        """
        now = datetime.now()
        if (now - self.last_check).total_seconds() < self.update_interval_seconds and self._rules:
            return

        try:
            uow = unit_of_work.UnitOfWork(db_session_maker)
            async with uow:
                raw_rules = await uow.rules.get_all_active_rules()
            
            compiled_rules = []
            for rule in raw_rules:
                if rule["pattern_type"] == "regex":
                    try:
                        rule["compiled_regex"] = re.compile(rule["pattern"], re.IGNORECASE)
                    except re.error as e:
                        logger.error(f"Invalid regex in rule {rule['rule_id']}: {e}")
                        continue
                compiled_rules.append(rule)
            
            self._rules = compiled_rules
            self.last_check = now
            logger.info(f"Rules reloaded. Total active rules: {len(self._rules)}")
            
        except Exception as e:
            logger.error(f"Error updating rules: {e}")

ruleManager = RuleManager()