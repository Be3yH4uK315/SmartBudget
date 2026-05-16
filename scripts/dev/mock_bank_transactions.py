#!/usr/bin/env python3
"""Local mock bank client for SmartBudget transaction API flows."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPCookieProcessor, Request, build_opener


DEFAULT_BASE_URL = "http://localhost"
DEFAULT_COOKIE_JAR = Path(tempfile.gettempdir()) / "smartbudget_mock_bank_cookies.txt"

LOGIN_ENDPOINT = "/api/v1/auth/login"
CREATE_ENDPOINT = "/api/v1/transactions/manual"
IMPORT_ENDPOINT = "/api/v1/transactions/import/mock"

TRANSACTION_TYPES = {"income", "expense"}
IMPORT_STATUSES = {"pending", "confirmed", "rejected"}

CATEGORIES = [
    (1, "Прочее"),
    (2, "Продукты"),
    (3, "Кафе и рестораны"),
    (4, "Одежда и обувь"),
    (5, "Электроника"),
    (6, "Строительство и ремонт"),
    (7, "Товары для дома"),
    (8, "Красота и уход"),
    (9, "Зоотовары"),
    (10, "Книги и канцелярия"),
    (11, "Аптеки"),
    (12, "Медицинские услуги"),
    (13, "Топливо"),
    (14, "Автосервисы"),
    (15, "Автозапчасти"),
    (16, "Парковки и штрафы"),
    (17, "Подписки"),
    (18, "Игры"),
    (19, "Маркетплейсы"),
    (20, "Общественный транспорт"),
    (21, "Такси и каршеринг"),
    (22, "ЖКХ"),
    (23, "Связь"),
    (24, "Финансы"),
    (25, "Образование"),
    (26, "Развлечения"),
    (27, "Спорт"),
    (28, "Путешествия"),
    (29, "Благотворительность"),
    (30, "Цветы и подарки"),
]

CATEGORY_FIXTURES = [
    {"category_id": 2, "merchant": "Perekrestok", "mcc": 5411, "description": "Grocery purchase"},
    {"category_id": 3, "merchant": "Dodo Pizza", "mcc": 5812, "description": "Cafe order"},
    {"category_id": 5, "merchant": "DNS", "mcc": 5732, "description": "Electronics purchase"},
    {"category_id": 11, "merchant": "Gorzdrav", "mcc": 5912, "description": "Pharmacy purchase"},
    {"category_id": 13, "merchant": "Lukoil", "mcc": 5541, "description": "Fuel station"},
    {"category_id": 17, "merchant": "Yandex Plus", "mcc": 4899, "description": "Subscription payment"},
    {"category_id": 19, "merchant": "Ozon", "mcc": 5399, "description": "Marketplace order"},
    {"category_id": 20, "merchant": "Mosmetro", "mcc": 4111, "description": "Public transport"},
    {"category_id": 21, "merchant": "Yandex Taxi", "mcc": 4121, "description": "Taxi ride"},
    {"category_id": 23, "merchant": "MTS", "mcc": 4814, "description": "Mobile service"},
    {"category_id": 24, "merchant": "Tinkoff Bank", "mcc": 6012, "description": "Bank operation"},
    {"category_id": 28, "merchant": "Aeroflot", "mcc": 4511, "description": "Travel purchase"},
]


class CommandError(Exception):
    """Expected CLI error."""


@dataclass(frozen=True)
class HttpResult:
    status: int
    headers: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json_or_text(self) -> Any:
        if not self.body:
            return None
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return self.text


class SmartBudgetClient:
    def __init__(
        self,
        base_url: str,
        cookie_jar_path: Path,
        token: str | None = None,
        verbose: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.cookie_jar_path = cookie_jar_path
        self.token = token
        self.verbose = verbose
        self.cookie_jar = MozillaCookieJar(str(cookie_jar_path))
        if cookie_jar_path.exists():
            self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
        self.opener = build_opener(HTTPCookieProcessor(self.cookie_jar))

    def save_cookies(self) -> None:
        self.cookie_jar_path.parent.mkdir(parents=True, exist_ok=True)
        self.cookie_jar.save(ignore_discard=True, ignore_expires=True)

    def cookie_names(self) -> list[str]:
        return sorted(cookie.name for cookie in self.cookie_jar)

    def request_json(self, method: str, endpoint: str, payload: Any | None) -> HttpResult:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "User-Agent": "smartbudget-mock-bank/1.0",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            headers["Cookie"] = f"access_token={self.token}"

        url = urljoin(self.base_url, endpoint.lstrip("/"))
        if self.verbose:
            safe_headers = dict(headers)
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "Bearer ***"
            if "Cookie" in safe_headers:
                safe_headers["Cookie"] = "access_token=***"
            print(f"HTTP {method} {url}", file=sys.stderr)
            print(f"Headers: {safe_headers}", file=sys.stderr)

        request = Request(url=url, data=body, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=30) as response:
                result = HttpResult(
                    status=response.status,
                    headers=dict(response.headers.items()),
                    body=response.read(),
                )
        except HTTPError as exc:
            result = HttpResult(
                status=exc.code,
                headers=dict(exc.headers.items()),
                body=exc.read(),
            )
        except URLError as exc:
            raise CommandError(f"Request failed: {exc.reason}") from exc

        return result


def env_or_default(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def resolved_base_url(args: argparse.Namespace) -> str:
    return args.base_url or env_or_default("SMARTBUDGET_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL


def resolved_cookie_jar(args: argparse.Namespace) -> Path:
    raw_path = getattr(args, "cookie_jar", None) or str(DEFAULT_COOKIE_JAR)
    return Path(raw_path).expanduser()


def resolved_token(args: argparse.Namespace) -> str | None:
    return getattr(args, "token", None) or env_or_default("SMARTBUDGET_ACCESS_TOKEN")


def print_json(value: Any, pretty: bool) -> None:
    if isinstance(value, str):
        print(value)
        return
    if pretty:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def print_response(result: HttpResult, pretty: bool) -> None:
    print(f"Response status: {result.status}")
    print("Response body:")
    print_json(result.json_or_text(), pretty=pretty)


def ensure_success(result: HttpResult) -> None:
    if result.status < 200 or result.status >= 300:
        raise CommandError(f"HTTP request failed with status {result.status}")


def parse_positive_decimal(raw_value: str) -> str:
    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise CommandError("--amount must be a decimal number") from exc
    if value <= 0:
        raise CommandError("--amount must be greater than 0")
    return str(value.quantize(Decimal("0.01")))


def parse_date(raw_value: str) -> str:
    if raw_value == "now":
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    normalized = raw_value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CommandError("--date must be 'now' or an ISO-8601 datetime") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_uuid(raw_value: str | None, arg_name: str) -> str | None:
    if not raw_value:
        return None
    try:
        return str(uuid.UUID(raw_value))
    except ValueError as exc:
        raise CommandError(f"{arg_name} must be a valid UUID") from exc


def create_client(args: argparse.Namespace) -> SmartBudgetClient:
    return SmartBudgetClient(
        base_url=resolved_base_url(args),
        cookie_jar_path=resolved_cookie_jar(args),
        token=resolved_token(args),
        verbose=args.verbose,
    )


def command_login(args: argparse.Namespace) -> int:
    email = args.username or env_or_default("SMARTBUDGET_USERNAME")
    password = args.password or env_or_default("SMARTBUDGET_PASSWORD")
    if not email:
        raise CommandError("--username/--email or SMARTBUDGET_USERNAME is required")
    if not password:
        raise CommandError("--password or SMARTBUDGET_PASSWORD is required")

    client = create_client(args)
    endpoint = LOGIN_ENDPOINT
    payload = {"email": email, "password": password}

    print(f"Endpoint: {urljoin(client.base_url, endpoint.lstrip('/'))}")
    result = client.request_json("POST", endpoint, payload)
    print_response(result, pretty=args.pretty)
    ensure_success(result)
    cookie_names = client.cookie_names()
    if "access_token" not in cookie_names:
        raise CommandError(
            "Login succeeded, but access_token cookie was not saved. "
            "Check auth service cookie settings and gateway base URL.",
        )
    client.save_cookies()

    print(f"Cookie jar: {client.cookie_jar_path}")
    print(f"Saved cookies: {', '.join(cookie_names) if cookie_names else 'none'}")
    return 0


def build_create_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.type not in TRANSACTION_TYPES:
        raise CommandError("--type must be one of: income, expense")

    transaction_id = (
        validate_uuid(args.transaction_id, "--transaction-id")
        if args.transaction_id
        else str(uuid.uuid4())
    )

    payload: dict[str, Any] = {
        "transactionId": transaction_id,
        "amount": parse_positive_decimal(args.amount),
        "transactionType": args.type,
        "date": parse_date(args.date),
        "description": args.description,
    }

    if args.category_id is not None:
        if args.category_id <= 0:
            raise CommandError("--category-id must be positive")
        payload["categoryId"] = args.category_id

    if args.merchant is not None:
        payload["merchant"] = args.merchant

    account_id = validate_uuid(args.account_id, "--account-id")
    if account_id is not None:
        payload["accountId"] = account_id

    return payload


def command_create(args: argparse.Namespace) -> int:
    client = create_client(args)
    endpoint = CREATE_ENDPOINT
    payload = build_create_payload(args)

    print(f"Endpoint: {urljoin(client.base_url, endpoint.lstrip('/'))}")
    print("Request payload:")
    print_json(payload, pretty=args.pretty)

    if args.dry_run:
        print("Dry run: request was not sent.")
        return 0

    result = client.request_json("POST", endpoint, payload)
    print_response(result, pretty=args.pretty)
    ensure_success(result)
    return 0


def load_import_payload(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise CommandError(f"Import file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CommandError(f"Import file is not valid JSON: {exc}") from exc


def detected_transaction_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        return 1
    raise CommandError("Import JSON must be an object or an array of objects")


def command_import_json(args: argparse.Namespace) -> int:
    client = create_client(args)
    endpoint = IMPORT_ENDPOINT
    file_path = Path(args.file).expanduser()
    payload = load_import_payload(file_path)
    count = detected_transaction_count(payload)

    print(f"Endpoint: {urljoin(client.base_url, endpoint.lstrip('/'))}")
    print(f"File: {file_path}")
    print(f"Transactions detected: {count}")

    if args.verbose or args.dry_run:
        print("Request payload:")
        print_json(payload, pretty=args.pretty)

    if args.dry_run:
        print("Dry run: request was not sent.")
        return 0

    result = client.request_json("POST", endpoint, payload)
    print_response(result, pretty=args.pretty)
    ensure_success(result)
    return 0


def sample_uuid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def sample_amount(rng: random.Random, transaction_type: str) -> str:
    if transaction_type == "income":
        cents = rng.randint(2_500_000, 18_000_000)
    else:
        cents = rng.randint(15_000, 1_500_000)
    value = Decimal(cents) / Decimal("100")
    return str(value.quantize(Decimal("0.01")))


def generate_transactions(
    count: int,
    seed: int | None,
    include_category_id: bool,
) -> list[dict[str, Any]]:
    if count < 1:
        raise CommandError("--count must be greater than 0")

    rng = random.Random(seed)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    transactions: list[dict[str, Any]] = []

    for index in range(count):
        transaction_type = "income" if rng.random() < 0.15 else "expense"
        fixture = {"category_id": 24, "merchant": "Employer", "mcc": 6012, "description": "Salary payment"}
        if transaction_type == "expense":
            fixture = rng.choice(CATEGORY_FIXTURES)

        date = now - timedelta(
            days=rng.randint(0, 30),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        description = f"{fixture['description']} #{index + 1}"
        transaction = {
            "transactionId": sample_uuid(rng),
            "date": date.isoformat().replace("+00:00", "Z"),
            "amount": sample_amount(rng, transaction_type),
            "transactionType": transaction_type,
            "status": rng.choice(["pending", "confirmed"]),
            "merchant": fixture["merchant"],
            "mcc": fixture["mcc"],
            "description": description,
        }
        if include_category_id:
            transaction["categoryId"] = fixture["category_id"]
        transactions.append(transaction)

    return transactions


def command_generate_sample(args: argparse.Namespace) -> int:
    output = Path(args.output).expanduser()
    payload = generate_transactions(
        count=args.count,
        seed=args.seed,
        include_category_id=args.include_category_id,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        if args.compact:
            json.dump(payload, file, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print(f"Generated: {output}")
    print(f"Transactions: {len(payload)}")
    return 0


def command_categories(args: argparse.Namespace) -> int:
    if args.json:
        print_json(
            [{"categoryId": category_id, "name": name} for category_id, name in CATEGORIES],
            pretty=args.pretty,
        )
        return 0

    for category_id, name in CATEGORIES:
        print(f"{category_id:>2}  {name}")
    return 0


def add_common_http_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", help="API Gateway base URL. Defaults to SMARTBUDGET_BASE_URL or http://localhost.")
    parser.add_argument("--cookie-jar", help=f"Cookie jar path. Defaults to {DEFAULT_COOKIE_JAR}.")
    parser.add_argument("--token", help="Access token. Also read from SMARTBUDGET_ACCESS_TOKEN.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostic request details with masked secrets.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mock bank client for local SmartBudget transaction API testing.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    login_parser = subparsers.add_parser("login", help="Authenticate through API Gateway.")
    add_common_http_args(login_parser)
    login_parser.add_argument("--username", "--email", dest="username", help="Auth email. Also read from SMARTBUDGET_USERNAME.")
    login_parser.add_argument("--password", help="Auth password. Also read from SMARTBUDGET_PASSWORD.")
    login_parser.set_defaults(handler=command_login)

    create_parser = subparsers.add_parser("create", help="Create one transaction through API Gateway.")
    add_common_http_args(create_parser)
    create_parser.add_argument("--amount", required=True, help="Positive transaction amount.")
    create_parser.add_argument(
        "--transaction-id",
        help="External bank transaction UUID. Auto-generated if omitted.",
    )
    create_parser.add_argument("--type", required=True, choices=sorted(TRANSACTION_TYPES), help="Transaction type.")
    create_parser.add_argument("--date", default="now", help="'now' or ISO-8601 datetime. Defaults to now.")
    create_parser.add_argument(
        "--category-id",
        type=int,
        help="Optional debugging override; omitted by default so classification can assign a category.",
    )
    create_parser.add_argument("--description", default="Test transaction from mock bank", help="Transaction description.")
    create_parser.add_argument("--merchant", help="Merchant name.")
    create_parser.add_argument("--account-id", help="Optional account UUID.")
    create_parser.add_argument("--dry-run", action="store_true", help="Print request without sending it.")
    create_parser.set_defaults(handler=command_create)

    import_parser = subparsers.add_parser("import-json", help="Import JSON through the real mock import endpoint.")
    add_common_http_args(import_parser)
    import_parser.add_argument("--file", required=True, help="JSON file containing one transaction object or an array.")
    import_parser.add_argument("--dry-run", action="store_true", help="Print request without sending it.")
    import_parser.set_defaults(handler=command_import_json)

    sample_parser = subparsers.add_parser("generate-sample", help="Generate sample import JSON.")
    sample_parser.add_argument("--output", required=True, help="Output JSON file path.")
    sample_parser.add_argument("--count", type=int, default=20, help="Number of transactions to generate.")
    sample_parser.add_argument("--seed", type=int, help="Random seed for deterministic output.")
    sample_parser.add_argument(
        "--include-category-id",
        action="store_true",
        help="Include categoryId in generated import JSON for debugging only.",
    )
    sample_parser.add_argument("--compact", action="store_true", help="Write compact JSON instead of pretty JSON.")
    sample_parser.set_defaults(handler=command_generate_sample)

    categories_parser = subparsers.add_parser("categories", help="Print classification category IDs and names.")
    categories_parser.add_argument("--json", action="store_true", help="Print categories as JSON.")
    categories_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output with --json.")
    categories_parser.set_defaults(handler=command_categories)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except CommandError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
