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
    (16, r"apple\.com/bill"),
    (16, r"itunes\.com"),
    # Apple Store -> Электроника (4)
    (4, r"apple\s*store"),
    (4, r"re:?store"),

    # --- Экосистема YANDEX ---
    # Такси -> Такси (20)
    (20, r"^yandex.*taxi"),
    (20, r"^yandex\.go"),
    (20, r"^uber.*trip"),
    # Еда/Лавка -> Рестораны/Продукты
    (2, r"^yandex.*eda"),
    (1, r"^yandex.*lavka"),
    # Драйв -> Такси/Каршеринг (20)
    (20, r"^yandex.*drive"),
    # Маркет -> Маркетплейсы (18)
    (18, r"^yandex.*market"),
    (18, r"^ym\s*market"),
    # Плюс -> Подписки (16)
    (16, r"^yandex\s*plus"),
    (16, r"^ya\s*plus"),

    # --- Экосистема SBER ---
    # СберМаркет -> Продукты (1)
    (1, r"^sbermarket"),
    # Мегамаркет -> Маркетплейсы (18)
    (18, r"^sbermegamarket"),
    # СберПрайм -> Подписки (16)
    (16, r"^sberprime"),
    
    # --- Каршеринг и Самокаты ---
    (20, r"^delimobil"),
    (20, r"^belkacar"),
    (20, r"^citydrive"),
    (20, r"^whoosh"),
    (20, r"^urent"),

    # --- Маркетплейсы ---
    (18, r"^wb\sretail"),
    (18, r"^wildberries"),
    (18, r"^ozon\.\d+"),
    (18, r"^aliexpress"),

    # --- Магнит ---
    (7, r"magnit\s*cosmetic"), # Красота
    (1, r"magnit"),            # Продукты
]

# =========================================================
# 2. MCC КОДЫ (PRIORITY 50 - 100)
# =========================================================
MCC_SPECIFIC = {
    # Продукты
    1: [5411, 5422, 5441, 5451, 5462],
    # Аптеки
    10: [5912, 5122],
    # АЗС
    12: [5541, 5542],
    # Алкоголь/Бары
    2: [5813],
    # Авиа
    27: [4511, 3000, 3001],
}

MCC_GENERIC = {
    # Разное / Маркетплейсы (очень часто 5999)
    18: [5311, 5331, 5399, 5964], 
    0: [5999], # Misc Specialty Retail -> Прочее
    2: [5812, 5814], # Рестораны/Фастфуд
    1: [5499], # Misc Food
}

async def init_all_rules():
    engine = create_async_engine(settings.settings.db.db_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        logger.info("--- STARTING RULES RE-INITIALIZATION ---")

        logger.info("Cleaning existing rules...")
        await session.execute(delete(models.Rule))
        await session.commit()

        total_rules = 0

        # -----------------------------------------------------
        # СЛОЙ 1: REGEX (Самый высокий приоритет: 5-15)
        # -----------------------------------------------------
        logger.info("Generating Regex Rules...")
        for cat_id, pattern in REGEX_RULES_LIST:
            rule = models.Rule(
                category_id=cat_id,
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

        for cat in categories:
            if not cat.keywords:
                continue
            
            for keyword in cat.keywords:
                kw_clean = keyword.lower().strip()

                if len(kw_clean) < 3: 
                    continue
                if kw_clean in DANGEROUS_KEYWORDS:
                    logger.warning(f"Skipping dangerous keyword: {kw_clean}")
                    continue

                rule = models.Rule(
                    category_id=cat.id,
                    name=f"KW: {kw_clean}",
                    pattern=kw_clean,
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
        for cat_id, codes in MCC_SPECIFIC.items():
            for code in codes:
                rule = models.Rule(
                    category_id=cat_id,
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
        for cat_id, codes in MCC_GENERIC.items():
            for code in codes:
                rule = models.Rule(
                    category_id=cat_id,
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