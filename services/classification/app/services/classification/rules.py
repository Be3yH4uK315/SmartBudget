import logging
import re
from datetime import datetime
from typing import Any

from app.core.config import settings
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
            cls._instance.update_interval_seconds = settings.APP.RULES_RELOAD_INTERVAL_SECONDS
            cls._instance._rules_signature = None
            
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
        if (now - self.last_check).total_seconds() < self.update_interval_seconds:
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
                    if not rule["pattern"]:
                        logger.error("Exact rule %s skipped because pattern is empty.", rule["rule_id"])
                        continue
                    pat = rule["pattern"].lower().strip()
                    if pat not in new_exact:
                        new_exact[pat] = rule
                        
                elif pt in ["regex", "contains"]:
                    if not rule["pattern"]:
                        logger.error("%s rule %s skipped because pattern is empty.", pt, rule["rule_id"])
                        continue
                    if pt == "regex":
                        try:
                            rule["compiled_regex"] = re.compile(rule["pattern"], re.IGNORECASE)
                        except re.error as e:
                            logger.error(f"Invalid regex rule {rule['rule_id']}: {e}")
                            continue
                    new_complex.append(rule)

            new_complex.sort(key=lambda r: r["priority"])
            new_signature = self._make_rules_signature(new_mcc, new_exact, new_complex)

            self._mcc_rules = new_mcc
            self._exact_rules = new_exact
            self._complex_rules = new_complex
            self.last_check = now

            if new_signature != self._rules_signature:
                self._rules_signature = new_signature
                count = len(new_mcc) + len(new_exact) + len(new_complex)
                logger.info(
                    "Rules reloaded. Total: %s (MCC: %s, Exact: %s, Complex: %s)",
                    count,
                    len(new_mcc),
                    len(new_exact),
                    len(new_complex),
                )
            else:
                logger.debug("Rules checked. No changes.")
            
        except Exception as e:
            self.last_check = now
            logger.error(f"Error updating rules: {e}")

    @staticmethod
    def _make_rules_signature(
        mcc_rules: dict[int, dict[str, Any]],
        exact_rules: dict[str, dict[str, Any]],
        complex_rules: list[dict[str, Any]],
    ) -> tuple:
        return (
            tuple(sorted((mcc, rule["rule_id"], rule["category_id"]) for mcc, rule in mcc_rules.items())),
            tuple(sorted((pattern, rule["rule_id"], rule["category_id"]) for pattern, rule in exact_rules.items())),
            tuple((rule["rule_id"], rule["category_id"], rule["priority"], rule["pattern"]) for rule in complex_rules),
        )

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
