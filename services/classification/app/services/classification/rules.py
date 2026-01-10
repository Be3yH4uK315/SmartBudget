import logging
import re
from datetime import datetime
from app.infrastructure.db.uow import UnitOfWork

logger = logging.getLogger(__name__)

class RuleManager:
    """
    Singleton для управления правилами.
    Реализует оптимизированный поиск (HashMap для точных совпадений).
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RuleManager, cls).__new__(cls)
            cls._instance.last_check = datetime.min
            cls._instance.update_interval_seconds = 30
            
            cls._instance._mcc_rules = {}
            cls._instance._exact_rules = {}
            cls._instance._complex_rules = []
        return cls._instance

    def get_rules(self):
        """Возвращает текущие правила."""
        return {
            "mcc": self._mcc_rules,
            "exact": self._exact_rules,
            "complex": self._complex_rules
        }

    async def check_for_updates(self, db_session_maker):
        """Проверяет и обновляет правила, если прошло достаточно времени."""
        now = datetime.now()
        if (now - self.last_check).total_seconds() < self.update_interval_seconds and self._mcc_rules:
            return

        try:
            uow = UnitOfWork(db_session_maker)
            async with uow:
                raw_rules = await uow.rules.get_all_active_rules()
            
            new_mcc = {}
            new_exact = {}
            new_complex = []

            for rule in raw_rules:
                pt = rule["pattern_type"]
                
                if pt == "mcc" and rule["mcc"]:
                    if rule["mcc"] not in new_mcc:
                        new_mcc[rule["mcc"]] = rule
                        
                elif pt == "exact":
                    pat = rule["pattern"].lower().strip()
                    if pat not in new_exact:
                        new_exact[pat] = rule
                        
                elif pt in ["regex", "contains"]:
                    if pt == "regex":
                        try:
                            rule["compiled_regex"] = re.compile(rule["pattern"], re.IGNORECASE)
                        except re.error as e:
                            logger.error(f"Invalid regex rule {rule['rule_id']}: {e}")
                            continue
                    new_complex.append(rule)

            new_complex.sort(key=lambda r: r["priority"])

            self._mcc_rules = new_mcc
            self._exact_rules = new_exact
            self._complex_rules = new_complex
            self.last_check = now
            
            count = len(new_mcc) + len(new_exact) + len(new_complex)
            logger.info(f"Rules reloaded. Total: {count} (MCC: {len(new_mcc)}, Exact: {len(new_exact)}, Complex: {len(new_complex)})")
            
        except Exception as e:
            logger.error(f"Error updating rules: {e}")

    def find_match(self, merchant: str, mcc: int | None, description: str) -> tuple[int | None, str | None, str | None]:
        """Ищет подходящее правило."""
        text = f"{merchant} {description}".lower().strip()

        if text in self._exact_rules:
            rule = self._exact_rules[text]
            return rule["category_id"], rule["category_name"], "exact"

        for rule in self._complex_rules:
            pt = rule["pattern_type"]
            pat = rule["pattern"].lower()
            is_match = False

            if pt == "contains" and pat in text:
                is_match = True
            elif pt == "regex" and "compiled_regex" in rule:
                if rule["compiled_regex"].search(text):
                    is_match = True
            
            if is_match:
                return rule["category_id"], rule["category_name"], pt

        if mcc in self._mcc_rules:
            rule = self._mcc_rules[mcc]
            return rule["category_id"], rule["category_name"], "mcc"

        return None, None, None

ruleManager = RuleManager()