"""Reusable business calculator helpers for views and CLI scripts."""

from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple

from .regulations import (
    RegulatorySnapshot,
    build_tax_projection,
    build_tax_rows,
    load_regulatory_snapshot,
)

DEFAULT_MONTHLY_PROFIT = Decimal("150000")
DEFAULT_DAYS_IN_MONTH = 30
DEFAULT_MARGIN_PERCENT = Decimal("30")


def parse_decimal_input(value, default: Decimal) -> Decimal:
    """Parse a decimal number that may include spaces or commas."""

    if value in (None, ""):
        return default
    try:
        normalized = str(value).replace(" ", "").replace(",", ".")
        parsed = Decimal(normalized)
    except (InvalidOperation, TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def parse_positive_int(value, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def parse_margin_percent(value) -> Decimal:
    margin = parse_decimal_input(value, DEFAULT_MARGIN_PERCENT)
    if margin <= 0:
        return DEFAULT_MARGIN_PERCENT
    if margin >= Decimal("99.9"):
        return Decimal("99.9")
    return margin


def _resolve_tax_systems(
    snapshot: RegulatorySnapshot, opf: Dict, preferred_tax_code: Optional[str]
) -> Tuple[List[str], List[Dict], Optional[str], Optional[Dict]]:
    available_tax_codes = opf.get("tax_systems") or list(snapshot.tax_systems.keys())
    available_tax_systems = [
        snapshot.get_tax_system(code)
        for code in available_tax_codes
        if snapshot.get_tax_system(code)
    ]
    selected_code = (
        preferred_tax_code
        if preferred_tax_code in [tax["code"] for tax in available_tax_systems]
        else None
    )
    if not selected_code and available_tax_systems:
        selected_code = available_tax_systems[0]["code"]
    selected_system = snapshot.get_tax_system(selected_code) if selected_code else None
    return available_tax_codes, available_tax_systems, selected_code, selected_system


def calculate_business_plan(
    monthly_profit: Decimal,
    days_in_month: int,
    margin_percent: Decimal,
    opf_code: Optional[str] = None,
    tax_system_code: Optional[str] = None,
) -> Dict:
    """Return a dictionary with all calculator metrics."""

    margin_ratio = margin_percent / Decimal("100")
    snapshot = load_regulatory_snapshot()
    selected_opf = snapshot.get_opf(opf_code)
    (
        available_tax_codes,
        available_tax_systems,
        selected_tax_code,
        selected_tax_system,
    ) = _resolve_tax_systems(
        snapshot, selected_opf, tax_system_code
    )

    daily_profit_target = monthly_profit / Decimal(days_in_month)
    monthly_operational_cost = monthly_profit * (
        (Decimal("1") / margin_ratio) - Decimal("1")
    )
    daily_operational_cost = monthly_operational_cost / Decimal(days_in_month)
    pre_tax_monthly_base = monthly_profit + monthly_operational_cost
    pre_tax_daily_base = daily_profit_target + daily_operational_cost
    yearly_profit_goal = monthly_profit * Decimal(12)

    sales_breakdown = []
    for sales_per_day in range(1, 11):
        profit_per_sale = daily_profit_target / Decimal(sales_per_day)
        monthly_sales = sales_per_day * days_in_month
        yearly_sales = monthly_sales * 12
        sales_breakdown.append(
            {
                "sales_per_day": sales_per_day,
                "profit_per_sale": profit_per_sale,
                "monthly_sales": monthly_sales,
                "yearly_sales": yearly_sales,
            }
        )

    profitability_rows = []
    for margin in range(10, 85, 5):
        margin_decimal = Decimal(margin) / Decimal(100)
        monthly_revenue = monthly_profit / margin_decimal
        yearly_revenue = monthly_revenue * Decimal(12)
        profitability_rows.append(
            {
                "margin": margin,
                "monthly_revenue": monthly_revenue,
                "yearly_revenue": yearly_revenue,
            }
        )

    tax_projection = build_tax_projection(
        daily_profit_target,
        daily_operational_cost,
        days_in_month,
        selected_tax_system,
    )
    tax_rows = build_tax_rows(
        daily_profit_target,
        daily_operational_cost,
        days_in_month,
        available_tax_codes,
        snapshot,
    )
    tax_rate_percent = tax_projection.get("rate_percent") if tax_projection else None

    return {
        "monthly_profit": monthly_profit,
        "days_in_month": days_in_month,
        "margin_percent": margin_percent,
        "margin_ratio": margin_ratio,
        "daily_profit_target": daily_profit_target,
        "daily_operational_cost": daily_operational_cost,
        "yearly_profit_goal": yearly_profit_goal,
        "monthly_operational_cost": monthly_operational_cost,
        "pre_tax_monthly_base": pre_tax_monthly_base,
        "pre_tax_daily_base": pre_tax_daily_base,
        "sales_breakdown": sales_breakdown,
        "profitability_rows": profitability_rows,
        "regulatory_snapshot": snapshot,
        "opf_list": snapshot.opf,
        "selected_opf": selected_opf,
        "selected_tax_system": selected_tax_system,
        "selected_tax_code": selected_tax_code,
        "available_tax_codes": available_tax_codes,
        "available_tax_systems": available_tax_systems,
        "tax_projection": tax_projection,
        "tax_rate_percent": tax_rate_percent,
        "tax_rows": tax_rows,
    }


__all__ = [
    "DEFAULT_DAYS_IN_MONTH",
    "DEFAULT_MARGIN_PERCENT",
    "DEFAULT_MONTHLY_PROFIT",
    "calculate_business_plan",
    "parse_decimal_input",
    "parse_margin_percent",
    "parse_positive_int",
]
