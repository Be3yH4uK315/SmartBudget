import logging
import re
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.infrastructure.db.uow import UnitOfWork

logger = logging.getLogger(__name__)

RULE_TYPE_MCC = "mcc"
RULE_TYPE_EXACT = "exact"
RULE_TYPE_REGEX = "regex"
RULE_TYPE_CONTAINS = "contains"


def normalize_rule_text(value: str | None) -> str:
    """Нормализует текст merchant/description для rule-based поиска."""
    if not value:
        return ""

    normalized = value.casefold().replace("ё", "е")
    normalized = re.sub(r"[^0-9a-zа-я]+", " ", normalized)

    return re.sub(r"\s+", " ", normalized).strip()


class RuleManager:
    """
    Singleton manager для правил классификации.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RuleManager, cls).__new__(cls)
            cls._instance.last_check = datetime.min
            cls._instance.update_interval_seconds = (
                settings.APP.RULES_RELOAD_INTERVAL_SECONDS
            )
            cls._instance._rules_signature = None

            cls._instance._mcc_rules = {}
            cls._instance._exact_rules = {}
            cls._instance._complex_rules = []

        return cls._instance

    def get_rules(self) -> dict[str, Any]:
        """Возвращает текущие правила классификации."""
        return {
            "mcc": self._mcc_rules,
            "exact": self._exact_rules,
            "complex": self._complex_rules,
        }

    async def check_for_updates(self, db_session_maker) -> None:
        """Обновляет правила, если прошел reload interval."""
        now = datetime.now()
        if (now - self.last_check).total_seconds() < self.update_interval_seconds:
            return

        try:
            raw_rules = await self._load_rules(db_session_maker)
            mcc_rules, exact_rules, complex_rules = self._build_indexes(raw_rules)

            new_signature = self._make_rules_signature(
                mcc_rules=mcc_rules,
                exact_rules=exact_rules,
                complex_rules=complex_rules,
            )

            self._mcc_rules = mcc_rules
            self._exact_rules = exact_rules
            self._complex_rules = complex_rules
            self.last_check = now

            self._log_reload_if_changed(new_signature)

        except Exception as exc:
            self.last_check = now
            logger.error("Error updating rules: %s", exc, exc_info=True)

    def find_match(
        self,
        merchant: str | None,
        mcc: int | None,
        description: str | None,
    ) -> tuple[int | None, str | None, str | None]:
        """Ищет подходящее правило классификации."""
        raw_text = self._build_raw_search_text(merchant, description)
        normalized_text = normalize_rule_text(raw_text)

        exact_match = self._find_exact_match(normalized_text)
        if exact_match:
            return exact_match

        complex_match = self._find_complex_match(raw_text, normalized_text)
        if complex_match:
            return complex_match

        mcc_match = self._find_mcc_match(mcc)
        if mcc_match:
            return mcc_match

        return None, None, None

    @staticmethod
    async def _load_rules(db_session_maker) -> list[dict[str, Any]]:
        """Загружает правила из БД."""
        uow = UnitOfWork(db_session_maker)
        async with uow:
            return await uow.rules.get_all_active_rules()

    def _build_indexes(
        self,
        raw_rules: list[dict[str, Any]],
    ) -> tuple[dict[int, dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
        """Строит индексы правил для быстрого поиска."""
        mcc_rules: dict[int, dict[str, Any]] = {}
        exact_rules: dict[str, dict[str, Any]] = {}
        complex_rules: list[dict[str, Any]] = []

        for rule in raw_rules:
            pattern_type = rule["pattern_type"]

            if pattern_type == RULE_TYPE_MCC:
                self._add_mcc_rule(rule, mcc_rules)

            elif pattern_type == RULE_TYPE_EXACT:
                self._add_exact_rule(rule, exact_rules)

            elif pattern_type in {RULE_TYPE_REGEX, RULE_TYPE_CONTAINS}:
                self._add_complex_rule(rule, complex_rules)

        complex_rules.sort(
            key=lambda item: (
                item["priority"],
                -item.get("specificity", 0),
                item["rule_id"],
            ),
        )

        return mcc_rules, exact_rules, complex_rules

    @staticmethod
    def _add_mcc_rule(
        rule: dict[str, Any],
        mcc_rules: dict[int, dict[str, Any]],
    ) -> None:
        """Добавляет MCC-правило в индекс."""
        mcc = rule.get("mcc")
        if not mcc:
            return

        existing = mcc_rules.get(mcc)
        if existing is None or (
            rule["priority"],
            rule["rule_id"],
        ) < (
            existing["priority"],
            existing["rule_id"],
        ):
            mcc_rules[mcc] = rule

    @staticmethod
    def _add_exact_rule(
        rule: dict[str, Any],
        exact_rules: dict[str, dict[str, Any]],
    ) -> None:
        """Добавляет exact-правило в индекс."""
        pattern = rule.get("pattern")
        if not pattern:
            logger.error(
                "Exact rule %s skipped because pattern is empty.",
                rule.get("rule_id"),
            )
            return

        normalized_pattern = normalize_rule_text(pattern)
        if normalized_pattern not in exact_rules:
            exact_rules[normalized_pattern] = rule

    @staticmethod
    def _add_complex_rule(
        rule: dict[str, Any],
        complex_rules: list[dict[str, Any]],
    ) -> None:
        """Добавляет regex/contains-правило в индекс."""
        pattern_type = rule["pattern_type"]
        pattern = rule.get("pattern")

        if not pattern:
            logger.error(
                "%s rule %s skipped because pattern is empty.",
                pattern_type,
                rule.get("rule_id"),
            )
            return

        rule["normalized_pattern"] = normalize_rule_text(pattern)
        rule["specificity"] = len(rule["normalized_pattern"] or pattern)

        if pattern_type == RULE_TYPE_REGEX:
            try:
                rule["compiled_regex"] = re.compile(pattern, re.IGNORECASE)
            except re.error as exc:
                logger.error(
                    "Invalid regex rule %s: %s",
                    rule.get("rule_id"),
                    exc,
                    exc_info=True,
                )
                return

        complex_rules.append(rule)

    def _log_reload_if_changed(self, new_signature: tuple) -> None:
        """Логирует перезагрузку правил только при изменении signature."""
        if new_signature == self._rules_signature:
            logger.debug("Rules checked. No changes.")
            return

        self._rules_signature = new_signature
        count = len(self._mcc_rules) + len(self._exact_rules) + len(self._complex_rules)

        logger.info(
            "Rules reloaded. Total: %s (MCC: %s, Exact: %s, Complex: %s)",
            count,
            len(self._mcc_rules),
            len(self._exact_rules),
            len(self._complex_rules),
        )

    @staticmethod
    def _make_rules_signature(
        mcc_rules: dict[int, dict[str, Any]],
        exact_rules: dict[str, dict[str, Any]],
        complex_rules: list[dict[str, Any]],
    ) -> tuple:
        """Создает signature набора правил."""
        return (
            tuple(
                sorted(
                    (
                        mcc,
                        rule["rule_id"],
                        rule["category_id"],
                    )
                    for mcc, rule in mcc_rules.items()
                ),
            ),
            tuple(
                sorted(
                    (
                        pattern,
                        rule["rule_id"],
                        rule["category_id"],
                    )
                    for pattern, rule in exact_rules.items()
                ),
            ),
            tuple(
                (
                    rule["rule_id"],
                    rule["category_id"],
                    rule["priority"],
                    rule["pattern"],
                )
                for rule in complex_rules
            ),
        )

    @staticmethod
    def _build_raw_search_text(merchant: str | None, description: str | None) -> str:
        """Формирует текст для поиска правил."""
        return f"{merchant or ''} {description or ''}".casefold().strip()

    def _find_exact_match(
        self,
        text: str,
    ) -> tuple[int, str, str] | None:
        """Ищет exact match."""
        rule = self._exact_rules.get(text)
        if not rule:
            return None

        return rule["category_id"], rule["category_name"], RULE_TYPE_EXACT

    def _find_complex_match(
        self,
        raw_text: str,
        normalized_text: str,
    ) -> tuple[int, str, str] | None:
        """Ищет regex/contains match."""
        for rule in self._complex_rules:
            pattern_type = rule["pattern_type"]
            pattern = rule.get("normalized_pattern", "")
            is_match = False

            if pattern_type == RULE_TYPE_CONTAINS and pattern and pattern in normalized_text:
                is_match = True

            elif pattern_type == RULE_TYPE_REGEX and "compiled_regex" in rule:
                is_match = bool(
                    rule["compiled_regex"].search(raw_text)
                    or rule["compiled_regex"].search(normalized_text),
                )

            if is_match:
                return rule["category_id"], rule["category_name"], pattern_type

        return None

    def _find_mcc_match(
        self,
        mcc: int | None,
    ) -> tuple[int, str, str] | None:
        """Ищет MCC match."""
        if mcc is None:
            return None

        rule = self._mcc_rules.get(mcc)
        if not rule:
            return None

        return rule["category_id"], rule["category_name"], RULE_TYPE_MCC


ruleManager = RuleManager()
