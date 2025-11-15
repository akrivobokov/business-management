from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from django.conf import settings

DEFAULT_REGULATORY_DATA = {
    "checked_at": None,
    "opf": [
        {
            "code": "IP",
            "title": "Индивидуальный предприниматель",
            "source_url": "https://www.nalog.gov.ru/opendata/7707329152-egrip/",
            "tax_systems": ["USN_6", "USN_15", "PSN", "AUSN", "OSN_IP"],
        },
        {
            "code": "OOO",
            "title": "Общество с ограниченной ответственностью",
            "source_url": "https://www.nalog.gov.ru/opendata/7707329152-egrul/",
            "tax_systems": ["USN_6", "USN_15", "OSN_OOO"],
        },
    ],
    "tax_systems": {
        "OSN_OOO": {
            "code": "OSN_OOO",
            "title": "ОСНО для ООО",
            "effective_rate": "0.20",
            "law_reference": "ст. 284 НК РФ",
            "basis": "profit",
            "source_url": "https://www.nalog.gov.ru/opendata/7707329152-taxprofit/",
            "note": "20% налог на прибыль организаций",
        },
        "OSN_IP": {
            "code": "OSN_IP",
            "title": "ОСНО для ИП",
            "effective_rate": "0.13",
            "law_reference": "ст. 224 НК РФ",
            "basis": "income",
            "source_url": "https://www.nalog.gov.ru/opendata/7707329152-ndfl/",
            "note": "13% НДФЛ от чистой прибыли",
        },
        "USN_6": {
            "code": "USN_6",
            "title": "УСН «Доходы»",
            "effective_rate": "0.06",
            "law_reference": "ст. 346.20 НК РФ",
            "basis": "revenue",
            "source_url": "https://www.nalog.gov.ru/opendata/7707329152-usn/",
            "note": "6% с выручки",
        },
        "USN_15": {
            "code": "USN_15",
            "title": "УСН «Доходы минус расходы»",
            "effective_rate": "0.15",
            "law_reference": "ст. 346.20 НК РФ",
            "basis": "profit",
            "source_url": "https://www.nalog.gov.ru/opendata/7707329152-usn/",
            "note": "15% от прибыли",
        },
        "PSN": {
            "code": "PSN",
            "title": "Патентная система",
            "effective_rate": "0.06",
            "law_reference": "ст. 346.50 НК РФ",
            "basis": "patent",
            "source_url": "https://www.nalog.gov.ru/opendata/7707329152-psn/",
            "note": "Ставка рассчитывается от потенциального дохода",
        },
        "AUSN": {
            "code": "AUSN",
            "title": "Автоматизированная УСН",
            "effective_rate": "0.08",
            "law_reference": "Федеральный закон № 17-ФЗ",
            "basis": "revenue",
            "source_url": "https://www.nalog.gov.ru/opendata/7707329152-ausn/",
            "note": "8% с выручки",
        },
    },
}


@dataclass
class RegulatorySnapshot:
    payload: Dict

    def __post_init__(self):
        self.payload = self._normalize(self.payload)

    def _normalize(self, payload: Dict) -> Dict:
        normalized = {
            "checked_at": payload.get("checked_at") or payload.get("fetched_at"),
            "opf": payload.get("opf") or DEFAULT_REGULATORY_DATA["opf"],
            "tax_systems": {},
        }

        raw_tax_systems = payload.get("tax_systems") or payload.get("tax_regimes")
        if isinstance(raw_tax_systems, dict):
            source_items = raw_tax_systems.values()
        else:
            source_items = raw_tax_systems or []

        for item in source_items:
            code = item.get("code") or item.get("tax_code") or item.get("id")
            if not code:
                continue
            normalized["tax_systems"][code] = {
                "code": code,
                "title": item.get("title") or item.get("name") or DEFAULT_REGULATORY_DATA["tax_systems"].get(code, {}).get("title", code),
                "effective_rate": str(item.get("effective_rate") or item.get("rate") or item.get("tax_rate") or DEFAULT_REGULATORY_DATA["tax_systems"].get(code, {}).get("effective_rate", "0")),
                "law_reference": item.get("law_reference") or DEFAULT_REGULATORY_DATA["tax_systems"].get(code, {}).get("law_reference"),
                "basis": item.get("basis") or DEFAULT_REGULATORY_DATA["tax_systems"].get(code, {}).get("basis", "revenue"),
                "source_url": item.get("source_url") or DEFAULT_REGULATORY_DATA["tax_systems"].get(code, {}).get("source_url"),
                "note": item.get("note") or DEFAULT_REGULATORY_DATA["tax_systems"].get(code, {}).get("note"),
            }

        for code, defaults in DEFAULT_REGULATORY_DATA["tax_systems"].items():
            normalized["tax_systems"].setdefault(code, defaults)

        normalized.setdefault("default_opf", payload.get("default_opf") or DEFAULT_REGULATORY_DATA["opf"][0]["code"])
        normalized.setdefault("sources", getattr(settings, "REGULATORY_SOURCES", {}))
        return normalized

    @property
    def opf(self) -> List[Dict]:
        return self.payload["opf"]

    @property
    def tax_systems(self) -> Dict[str, Dict]:
        return self.payload["tax_systems"]

    @property
    def checked_at(self) -> Optional[str]:
        return self.payload.get("checked_at")

    @property
    def sources(self) -> Dict:
        return self.payload.get("sources", {})

    def get_opf(self, code: Optional[str]) -> Dict:
        if not self.opf:
            return {}
        if not code:
            return self.opf[0]
        for item in self.opf:
            if item.get("code") == code:
                return item
        return self.opf[0]

    def get_tax_system(self, code: Optional[str]) -> Optional[Dict]:
        if not code:
            return None
        return self.tax_systems.get(code)


def get_regulatory_cache_path() -> Path:
    cache_path = getattr(settings, "REGULATORY_CACHE_FILE", None)
    if cache_path:
        return Path(cache_path)
    return Path(settings.BASE_DIR) / "regulations_cache.json"


def load_regulatory_snapshot() -> RegulatorySnapshot:
    cache_path = get_regulatory_cache_path()
    if cache_path.exists():
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return RegulatorySnapshot(payload)
        except json.JSONDecodeError:
            pass
    return RegulatorySnapshot(DEFAULT_REGULATORY_DATA)


def _safe_decimal(value: str, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def build_tax_projection(
    daily_net_profit: Decimal,
    daily_operational_cost: Decimal,
    days_in_month: int,
    tax_info: Dict,
) -> Dict:
    if not tax_info:
        return {}
    rate = _safe_decimal(tax_info.get("effective_rate"), "0")
    if rate >= Decimal("1"):
        rate = Decimal("0.99")
    if rate < Decimal("0"):
        rate = Decimal("0")

    basis = (tax_info.get("basis") or "revenue").lower()
    divisor = Decimal("1") - rate if rate < Decimal("1") else Decimal("0.01")

    if basis == "revenue" or basis == "patent":
        base_without_tax = daily_net_profit + daily_operational_cost
        daily_revenue = base_without_tax / divisor
        tax_daily = daily_revenue * rate
    else:  # profit / income
        profit_before_tax = daily_net_profit / divisor
        daily_revenue = daily_operational_cost + profit_before_tax
        tax_daily = profit_before_tax * rate

    monthly_revenue = daily_revenue * Decimal(days_in_month)
    yearly_revenue = daily_revenue * Decimal(days_in_month) * Decimal(12)
    return {
        "rate": rate,
        "rate_percent": rate * Decimal(100),
        "tax_daily": tax_daily,
        "daily_revenue": daily_revenue,
        "monthly_revenue": monthly_revenue,
        "yearly_revenue": yearly_revenue,
        "tax_monthly": tax_daily * Decimal(days_in_month),
        "tax_yearly": tax_daily * Decimal(days_in_month) * Decimal(12),
    }


def build_tax_rows(
    daily_net_profit: Decimal,
    daily_operational_cost: Decimal,
    days_in_month: int,
    tax_system_codes: Iterable[str],
    snapshot: RegulatorySnapshot,
) -> List[Dict]:
    rows = []
    for code in tax_system_codes:
        info = snapshot.get_tax_system(code)
        if not info:
            continue
        projection = build_tax_projection(daily_net_profit, daily_operational_cost, days_in_month, info)
        rows.append(
            {
                "code": code,
                "title": info.get("title", code),
                "law_reference": info.get("law_reference"),
                "source_url": info.get("source_url"),
                "note": info.get("note"),
                "rate": projection.get("rate"),
                "rate_percent": projection.get("rate_percent"),
                "tax_daily": projection.get("tax_daily"),
                "tax_monthly": projection.get("tax_monthly"),
                "tax_yearly": projection.get("tax_yearly"),
                "daily_revenue": projection.get("daily_revenue"),
                "monthly_revenue": projection.get("monthly_revenue"),
                "yearly_revenue": projection.get("yearly_revenue"),
            }
        )
    return rows
