import asyncio
import logging
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.infrastructure.db import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DANGEROUS_KEYWORDS = {
    "shop",
    "market",
    "store",
    "pay",
    "payment",
    "transfer",
    "card",
    "bank",
    "mobile",
    "service",
    "retail",
    "group",
    "google",
    "apple",
    "yandex",
    "amazon",
    "uber",
    "internet",
    "metro",
}

REGEX_RULES_LIST = [
    (17, r"apple\W*com\W*bill", 10),
    (17, r"itunes", 10),
    (5, r"apple\s*store", 10),
    (5, r"\bre:?store\b", 10),
    (21, r"\b(yandex|яндекс|ya)\W*(taxi|go|такси|го)\b", 10),
    (21, r"\b(uber|убер)\b", 10),
    (3, r"\b(yandex|яндекс|ya)\W*(eda|food|еда)\b", 10),
    (2, r"\b(yandex|яндекс|ya)\W*(lavka|лавка)\b", 10),
    (21, r"\b(yandex|яндекс|ya)\W*(drive|драйв)\b", 10),
    (19, r"\b(yandex|яндекс|ya|ym)\W*(market|маркет)\b", 10),
    (17, r"\b(yandex|яндекс|ya)\W*(plus|плюс)\b", 10),
    (2, r"\bsber\W*market\b|\bсбер\W*маркет\b", 10),
    (19, r"\bsber\W*mega\W*market\b|\bсбер\W*мега\W*маркет\b", 10),
    (17, r"\bsber\W*prime\b|\bсбер\W*прайм\b", 10),
    (24, r"\b(sberbank|сбербанк|tinkoff|тинькофф|vtb|втб)\b", 10),
    (24, r"\b(сбп|sbp|card2card|c2c|перевод|p2p)\b", 10),
    (24, r"\b(зарплата|salary|cashback|кешбек|кэшбек|процент[ы]?)\b", 10),
    (24, r"\b(наличные|cash\W*withdrawal|atm|банкомат|комисси[яи])\b", 10),
    (23, r"\b(mts|мтс)\W*(mobile|мобайл|связь)?\b", 20),
    (24, r"\b(mts|мтс)\W*(bank|банк)\b", 10),
    (8, r"\b(magnit|магнит)\W*(cosmetic|косметик)\b", 10),
    (2, r"\b(magnit|магнит)\b", 30),
    (20, r"\b(mosmetro|мосметро|тройка|troika|metro\W*pass|метро\W*москва)\b", 10),
    (2, r"\bmetro\W*(cc|cash|c\W*c)\b", 10),
    (21, r"\b(delimobil|делимобиль|belkacar|citydrive|ситидрайв)\b", 10),
    (21, r"\b(whoosh|urent|юрент)\b", 10),
    (19, r"\b(wb|wildberries|вайлдберриз)\b", 10),
    (19, r"\b(ozon|озон|aliexpress|алиэкспресс)\b", 10),
]

CATEGORY_KEYWORDS = {
    2: [
        "пятерочка", "пятёрочка", "5ka", "pyaterochka", "перекресток",
        "перекрёсток", "perekrestok", "лента", "lenta", "ашан", "auchan",
        "дикси", "dixy", "вкусвилл", "vkusvill", "самокат", "sbermarket",
        "bristol", "бристоль", "winelab", "красное белое", "grocery",
    ],
    3: [
        "додо", "dodo", "kfc", "burger king", "mcdonalds", "вкусно и точка",
        "starbucks", "кофе", "coffee", "кафе", "cafe", "ресторан",
        "restaurant", "суши", "yakitoriya", "tanuki", "subway", "теремок",
        "шоколадница", "еда",
    ],
    4: [
        "zara", "hm", "h m", "uniqlo", "lamoda", "asos", "ostin", "befree",
        "gloria jeans", "mango", "reserved", "colins", "adidas", "nike",
        "reebok", "rendez vous", "одежда", "обувь", "sneakers",
    ],
    5: [
        "мвидео", "mvideo", "эльдорадо", "eldorado", "dns", "днс",
        "citilink", "ситилинк", "restore", "re store", "samsung", "xiaomi",
        "huawei", "связной", "technopark", "техника", "electronics",
    ],
    6: [
        "леруа", "leroy merlin", "obi", "оби", "castorama", "касторама",
        "petrovich", "петрович", "maxidom", "максидом", "строй", "stroy",
        "ремонт", "строительство", "инструменты",
    ],
    7: [
        "fix price", "фикс прайс", "galamart", "гала март", "посуда",
        "posuda", "domovoy", "домовой", "hoff", "икеа", "ikea", "togas",
        "kuchenland", "товары для дома",
    ],
    8: [
        "letu", "летуаль", "rive gauche", "рив гош", "золотое яблоко",
        "gold apple", "sephora", "ile de beaute", "косметика", "kosmetika",
        "салон", "salon", "barbershop", "маникюр", "manicure",
    ],
    9: [
        "4 лапы", "4lapy", "bethoven", "бетховен", "petshop", "зоомагазин",
        "zoo", "le murr", "лемурр", "заповедник", "корм", "ветклиника",
    ],
    10: [
        "читай город", "chitai gorod", "labirint", "лабиринт", "bookvoed",
        "буквоед", "litres", "литрес", "respublica", "республика", "книга",
        "books", "канцтовары", "stationery",
    ],
    11: [
        "аптека", "apteka", "rigla", "ригла", "36 6", "горздрав",
        "gorzdrav", "планета здоровья", "planetazdorovo", "eapteka",
        "столички", "vita", "pharmacy",
    ],
    12: [
        "invitro", "инвитро", "gemotest", "гемотест", "helix", "хеликс",
        "medsi", "медси", "sm clinic", "см клиника", "cmd", "стоматология",
        "dentist", "clinic", "doctor", "медицина",
    ],
    13: [
        "lukoil", "лукойл", "gazpromneft", "газпромнефть", "rosneft",
        "роснефть", "tatneft", "татнефть", "bashneft", "башнефть", "bp",
        "shell", "teboil", "азс", "fuel", "oil",
    ],
    14: [
        "rolf", "рольф", "major", "fit service", "автосервис",
        "autoservice", "шиномонтаж", "car wash", "мойка", "moika",
        "техобслуживание", "то авто",
    ],
    15: [
        "exist", "экзист", "autodoc", "автодок", "emex", "емекс",
        "kolesa darom", "колеса даром", "autoparts", "запчасти",
        "автозапчасти",
    ],
    16: [
        "parking", "парковка", "mos ru", "моспаркинг", "гибдд", "gibdd",
        "штраф", "shtraf", "tsodd", "цодд", "ampc", "ам пп", "госуслуги",
    ],
    17: [
        "netflix", "spotify", "youtube premium", "yandex plus", "яндекс плюс",
        "ivi", "иви", "okko", "окко", "kinopoisk", "кинопоиск", "start",
        "amediateka", "premier", "more tv", "подписка", "subscription",
    ],
    18: [
        "steam", "стим", "playstation", "psn", "xbox", "nintendo",
        "blizzard", "gog", "epic games", "wargaming", "my games",
        "donationalerts", "game", "игры",
    ],
    19: [
        "ozon", "озон", "wildberries", "вайлдберриз", "wb retail",
        "aliexpress", "алиэкспресс", "yandex market", "яндекс маркет",
        "kazanexpress", "sbermegamarket", "мегамаркет", "маркетплейс",
    ],
    20: [
        "mosmetro", "мосметро", "тройка", "troika", "strelka", "стрелка",
        "rzd", "ржд", "аэроэкспресс", "aeroexpress", "metro pass",
        "автобус", "транспорт",
    ],
    21: [
        "yandex taxi", "яндекс такси", "yandex go", "uber", "gettaxi",
        "citymobil", "ситимобил", "delimobil", "делимобиль", "belkacar",
        "youdrive", "citidrive", "maxim", "indriver", "taxi", "такси",
    ],
    22: [
        "жкх", "квартплата", "mosenergosbyt", "мосэнергосбыт", "епд",
        "zhku", "газпром межрегионгаз", "dom ru", "дом ру", "rostelecom",
        "ростелеком", "mgts", "мгтс", "erc", "тсж", "управляющая компания",
    ],
    23: [
        "mts", "мтс", "beeline", "билайн", "megafon", "мегафон", "tele2",
        "теле2", "yota", "йота", "tinkoff mobile", "sbermobile",
        "skylink", "мобильная связь", "интернет",
    ],
    24: [
        "tinkoff", "тинькофф", "sberbank", "сбербанк", "vtb", "втб",
        "alfabank", "альфа банк", "raiffeisen", "райффайзен", "gazprombank",
        "открытие", "sovcombank", "комиссия", "commission", "сбп",
        "перевод", "пополнение", "cashback", "кэшбек", "зарплата", "salary",
    ],
    25: [
        "skyeng", "skillbox", "geekbrains", "netology", "coursera", "udemy",
        "stepik", "яндекс практикум", "школа", "school", "university",
        "университет", "обучение", "курс",
    ],
    26: [
        "кино", "kino", "cinema", "theater", "театр", "kassir", "кассир",
        "ticketland", "afisha", "афиша", "concert", "концерт", "karofilm",
        "formula kino", "развлечения",
    ],
    27: [
        "world class", "x fit", "alex fitness", "ddx", "spirit", "sportmaster",
        "спортмастер", "decathlon", "декатлон", "fitness", "фитнес", "gym",
        "спортзал", "бассейн",
    ],
    28: [
        "aeroflot", "аэрофлот", "s7", "pobeda", "победа", "utair",
        "ural airlines", "turkish airlines", "booking", "airbnb", "aviasales",
        "tutu", "onetwotrip", "ostrovok", "hotel", "отель", "travel", "tour",
    ],
    29: [
        "podari zhizn", "подари жизнь", "rusfond", "русфонд", "wwf",
        "greenpeace", "нужна помощь", "nuzhna pomosh", "charity",
        "благотворительность", "donation", "пожертвование",
    ],
    30: [
        "flowwow", "florist", "flowers", "цветы", "tsveti", "букет",
        "buket", "подарок", "gift", "подарки", "шары", "balloons",
    ],
}

MCC_RULES = {
    2: [5411, 5422, 5441, 5451, 5462, 5499],
    3: [5812, 5813, 5814],
    4: [5621, 5631, 5651, 5661, 5691],
    5: [5045, 5722, 5732, 5734],
    6: [5211, 5231, 5251, 5261, 5713],
    7: [5200, 5712, 5714, 5719],
    8: [5977, 7230, 7298],
    9: [742, 5995],
    10: [5192, 5942, 5943],
    11: [5122, 5912],
    12: [8011, 8021, 8031, 8043, 8062, 8071, 8099],
    13: [5541, 5542],
    14: [7531, 7534, 7538, 7542, 7549],
    15: [5532, 5533],
    16: [7523, 9222, 9399],
    18: [5816, 7994],
    19: [5311, 5331, 5399, 5964, 5999],
    20: [4111, 4112, 4131, 4789],
    21: [4121, 7512],
    22: [4900],
    23: [4812, 4814, 4816, 4899],
    24: [4829, 6010, 6011, 6012, 6051, 6211, 6300],
    25: [8211, 8220, 8241, 8299],
    26: [7832, 7922, 7929, 7991],
    27: [5941, 7941, 7997, 7999],
    28: [3000, 3001, 3501, 4511, 4722, 7011],
    29: [8398, 8641, 8651, 8661],
    30: [5947, 5992],
}


def _rule_key(pattern_type, pattern: str, mcc: int | None) -> tuple[str, str, int | None]:
    return pattern_type.value, pattern.casefold().strip(), mcc


def _add_rule(
    session,
    seen: set[tuple[str, str, int | None]],
    *,
    category_id: int,
    name: str,
    pattern: str,
    pattern_type,
    priority: int,
    mcc: int | None = None,
) -> int:
    key = _rule_key(pattern_type, pattern, mcc)
    if key in seen:
        return 0

    seen.add(key)
    session.add(
        models.Rule(
            category_id=category_id,
            name=name[:255],
            pattern=pattern,
            pattern_type=pattern_type,
            priority=priority,
            mcc=mcc,
        ),
    )

    return 1

async def _populate_rules(session) -> int:
    total_rules = 0
    seen: set[tuple[str, str, int | None]] = set()

    logger.info("Generating Regex Rules...")
    for category_id, pattern, priority in REGEX_RULES_LIST:
        total_rules += _add_rule(
            session,
            seen,
            category_id=category_id,
            name=f"RX: {pattern[:20]}",
            pattern=pattern,
            pattern_type=models.RulePatternType.REGEX,
            priority=priority,
        )

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

            total_rules += _add_rule(
                session,
                seen,
                category_id=category.category_id,
                name=f"KW: {keyword_clean}",
                pattern=keyword_clean,
                pattern_type=models.RulePatternType.CONTAINS,
                priority=45,
            )

    logger.info("Generating Extended Keyword Rules...")
    for category_id, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            keyword_clean = keyword.lower().strip()
            if len(keyword_clean) < 3:
                continue

            total_rules += _add_rule(
                session,
                seen,
                category_id=category_id,
                name=f"KW+: {keyword_clean}",
                pattern=keyword_clean,
                pattern_type=models.RulePatternType.CONTAINS,
                priority=40,
            )

    logger.info("Generating MCC Rules...")
    for category_id, codes in MCC_RULES.items():
        for code in codes:
            total_rules += _add_rule(
                session,
                seen,
                category_id=category_id,
                name=f"MCC: {code}",
                pattern=str(code),
                pattern_type=models.RulePatternType.MCC,
                priority=70,
                mcc=code,
            )

    return total_rules


async def seed_rules_if_empty(session_factory=None) -> int:
    """Создаёт дефолтные правила, только если таблица rules пустая."""
    owns_engine = session_factory is None
    engine = None
    if session_factory is None:
        engine = create_async_engine(settings.DB.DB_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            result = await session.execute(select(func.count()).select_from(models.Rule))
            rules_count = result.scalar_one()
            if rules_count:
                logger.info("Classification rules already initialized: %s", rules_count)
                return 0

            logger.info("Classification rules table is empty. Seeding default rules...")
            total_rules = await _populate_rules(session)
            await session.commit()
            logger.info("Created %s default classification rules.", total_rules)
            return total_rules
    finally:
        if owns_engine and engine is not None:
            await engine.dispose()


async def init_all_rules():
    """Полностью пересоздаёт правила в БД. Используется как ручной скрипт."""
    engine = create_async_engine(settings.DB.DB_URL)
    db_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with db_session_maker() as session:
        logger.info("--- STARTING RULES RE-INITIALIZATION ---")

        logger.info("Cleaning existing rules...")
        await session.execute(delete(models.Rule))
        await session.commit()

        total_rules = await _populate_rules(session)
        await session.commit()
        logger.info(f"--- SUCCESS: Created {total_rules} high-quality rules. ---")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_all_rules())
