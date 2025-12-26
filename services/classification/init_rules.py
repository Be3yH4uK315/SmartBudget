import asyncio
import logging
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app import settings, models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# БЛОК-ЛИСТ СЛОВ (не используются в генерации по ключевым словам)
# =========================================================
DANGEROUS_KEYWORDS = {
    "shop", "market", "store", "pay", "payment", "transfer", 
    "card", "bank", "mobile", "service", "retail", "group", 
    "google", "apple", "yandex", "amazon", "uber", "internet"
}

# =========================================================
# 1. REGEX ПРАВИЛА (PRIORITY 5 - 15)
# =========================================================
REGEX_RULES_LIST = [
    # --- Экосистема APPLE ---
    # Apple Services (Music, iCloud) -> Подписки (16)
    (17, r"apple\.com/bill"),
    (17, r"itunes\.com"),
    # Apple Store -> Электроника (4)
    (5, r"apple\s*store"),
    (5, r"re:?store"),

    # --- Экосистема YANDEX ---
    # Такси -> Такси (20)
    (21, r"^yandex.*taxi"),
    (21, r"^yandex\.go"),
    (21, r"^uber.*trip"),
    # Еда/Лавка -> Рестораны/Продукты
    (3, r"^yandex.*eda"),
    (2, r"^yandex.*lavka"),
    # Драйв -> Такси/Каршеринг (20)
    (21, r"^yandex.*drive"),
    # Маркет -> Маркетплейсы (18)
    (19, r"^yandex.*market"),
    (19, r"^ym\s*market"),
    # Плюс -> Подписки (16)
    (17, r"^yandex\s*plus"),
    (17, r"^ya\s*plus"),

    # --- Экосистема SBER ---
    # СберМаркет -> Продукты (1)
    (2, r"^sbermarket"),
    # Мегамаркет -> Маркетплейсы (18)
    (19, r"^sbermegamarket"),
    # СберПрайм -> Подписки (16)
    (17, r"^sberprime"),
    
    # --- Каршеринг и Самокаты ---
    (21, r"^delimobil"),
    (21, r"^belkacar"),
    (21, r"^citydrive"),
    (21, r"^whoosh"),
    (21, r"^urent"),

    # --- Маркетплейсы ---
    (19, r"^wb\sretail"),
    (19, r"^wildberries"),
    (19, r"^ozon\.\d+"),
    (19, r"^aliexpress"),

    # --- Магнит ---
    (8, r"magnit\s*cosmetic"), # Красота
    (2, r"magnit"),            # Продукты
]

# =========================================================
# 2. MCC КОДЫ (PRIORITY 50 - 100)
# =========================================================
MCC_SPECIFIC = {
    # Продукты
    2: [5411, 5422, 5441, 5451, 5462],
    # Аптеки
    11: [5912, 5122],
    # АЗС
    13: [5541, 5542],
    # Алкоголь/Бары
    3: [5813],
    # Авиа
    28: [4511, 3000, 3001],
}

MCC_GENERIC = {
    # Разное / Маркетплейсы (очень часто 5999)
    19: [5311, 5331, 5399, 5964], 
    1: [5999], # Misc Specialty Retail -> Прочее
    3: [5812, 5814], # Рестораны/Фастфуд
    2: [5499], # Misc Food
}

async def init_all_rules():
    """Инициализирует все правила в БД."""
    engine = create_async_engine(settings.settings.DB.DB_URL)
    db_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with db_session_maker() as session:
        logger.info("--- STARTING RULES RE-INITIALIZATION ---")

        logger.info("Cleaning existing rules...")
        await session.execute(delete(models.Rule))
        await session.commit()

        total_rules = 0

        # -----------------------------------------------------
        # СЛОЙ 1: REGEX (Самый высокий приоритет: 5-15)
        # -----------------------------------------------------
        logger.info("Generating Regex Rules...")
        for category_id, pattern in REGEX_RULES_LIST:
            rule = models.Rule(
                category_id=category_id,
                name=f"RX: {pattern[:20]}",
                pattern=pattern,
                pattern_type=models.RulePatternType.REGEX,
                priority=10,
                mcc=None
            )
            session.add(rule)
            total_rules += 1

        # -----------------------------------------------------
        # СЛОЙ 2: BRAND KEYWORDS (Средний приоритет: 40)
        # -----------------------------------------------------
        logger.info("Generating Keyword Rules from Categories...")
        result = await session.execute(select(models.Category))
        categories = result.scalars().all()

        for category in categories:
            if not category.keywords:
                continue
            
            for keyword in category.keywords:
                keyword_clean = keyword.lower().strip()

                if len(keyword_clean) < 3: 
                    continue
                if keyword_clean in DANGEROUS_KEYWORDS:
                    logger.warning(f"Skipping dangerous keyword: {keyword_clean}")
                    continue

                rule = models.Rule(
                    category_id=category.category_id,
                    name=f"KW: {keyword_clean}",
                    pattern=keyword_clean,
                    pattern_type=models.RulePatternType.CONTAINS,
                    priority=40,
                    mcc=None
                )
                session.add(rule)
                total_rules += 1

        # -----------------------------------------------------
        # СЛОЙ 3: SPECIFIC MCC (Приоритет: 60)
        # -----------------------------------------------------
        logger.info("Generating Specific MCC Rules...")
        for category_id, codes in MCC_SPECIFIC.items():
            for code in codes:
                rule = models.Rule(
                    category_id=category_id,
                    name=f"MCC (Spec): {code}",
                    pattern=str(code),
                    pattern_type=models.RulePatternType.MCC,
                    priority=60, 
                    mcc=code
                )
                session.add(rule)
                total_rules += 1

        # -----------------------------------------------------
        # СЛОЙ 4: GENERIC MCC (Приоритет: 100)
        # -----------------------------------------------------
        logger.info("Generating Generic MCC Rules...")
        for category_id, codes in MCC_GENERIC.items():
            for code in codes:
                rule = models.Rule(
                    category_id=category_id,
                    name=f"MCC (Gen): {code}",
                    pattern=str(code),
                    pattern_type=models.RulePatternType.MCC,
                    priority=100,
                    mcc=code
                )
                session.add(rule)
                total_rules += 1

        await session.commit()
        logger.info(f"--- SUCCESS: Created {total_rules} high-quality rules. ---")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_all_rules())