from decimal import Decimal, InvalidOperation

from django.shortcuts import render

from .regulations import (
    build_tax_projection,
    build_tax_rows,
    load_regulatory_snapshot,
)

DEFAULT_MONTHLY_PROFIT = Decimal('150000')
DEFAULT_DAYS_IN_MONTH = 30
DEFAULT_MARGIN_PERCENT = Decimal('30')


def _parse_decimal(value, default):
    if value in (None, ''):
        return default
    try:
        normalized = str(value).replace(' ', '').replace(',', '.')
        parsed = Decimal(normalized)
        if parsed <= 0:
            return default
        return parsed
    except (InvalidOperation, TypeError, ValueError):
        return default


def _parse_positive_int(value, default):
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _parse_margin_percent(value):
    margin = _parse_decimal(value, DEFAULT_MARGIN_PERCENT)
    if margin <= 0:
        return DEFAULT_MARGIN_PERCENT
    if margin >= Decimal('99.9'):
        return Decimal('99.9')
    return margin


def landing(request):
    return render(request, 'landing.html')


def business_calculator(request):
    monthly_profit = _parse_decimal(request.GET.get('monthly_profit'), DEFAULT_MONTHLY_PROFIT)
    days_in_month = _parse_positive_int(request.GET.get('days_in_month'), DEFAULT_DAYS_IN_MONTH)
    margin_percent = _parse_margin_percent(request.GET.get('margin_percent'))
    margin_ratio = margin_percent / Decimal('100')

    regulatory_snapshot = load_regulatory_snapshot()
    selected_opf = regulatory_snapshot.get_opf(request.GET.get('opf_code'))
    available_tax_codes = selected_opf.get('tax_systems') or list(regulatory_snapshot.tax_systems.keys())
    available_tax_systems = [
        regulatory_snapshot.get_tax_system(code)
        for code in available_tax_codes
        if regulatory_snapshot.get_tax_system(code)
    ]
    selected_tax_code = request.GET.get('tax_system_code')
    if selected_tax_code not in [tax['code'] for tax in available_tax_systems] and available_tax_systems:
        selected_tax_code = available_tax_systems[0]['code']
    selected_tax_system = regulatory_snapshot.get_tax_system(selected_tax_code)

    daily_profit_target = monthly_profit / Decimal(days_in_month)
    monthly_operational_cost = monthly_profit * ((Decimal('1') / margin_ratio) - Decimal('1'))
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
                'sales_per_day': sales_per_day,
                'profit_per_sale': profit_per_sale,
                'monthly_sales': monthly_sales,
                'yearly_sales': yearly_sales,
            }
        )

    profitability_rows = []
    for margin in range(10, 85, 5):
        margin_decimal = Decimal(margin) / Decimal(100)
        monthly_revenue = monthly_profit / margin_decimal
        yearly_revenue = monthly_revenue * Decimal(12)
        profitability_rows.append(
            {
                'margin': margin,
                'monthly_revenue': monthly_revenue,
                'yearly_revenue': yearly_revenue,
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
        regulatory_snapshot,
    )
    tax_rate_percent = tax_projection.get('rate_percent') if tax_projection else None

    context = {
        'monthly_profit': monthly_profit,
        'days_in_month': days_in_month,
        'margin_percent': margin_percent,
        'margin_ratio': margin_ratio,
        'daily_profit_target': daily_profit_target,
        'daily_operational_cost': daily_operational_cost,
        'yearly_profit_goal': yearly_profit_goal,
        'monthly_operational_cost': monthly_operational_cost,
        'pre_tax_monthly_base': pre_tax_monthly_base,
        'pre_tax_daily_base': pre_tax_daily_base,
        'sales_breakdown': sales_breakdown,
        'profitability_rows': profitability_rows,
        'regulatory_snapshot': regulatory_snapshot,
        'opf_list': regulatory_snapshot.opf,
        'selected_opf': selected_opf,
        'selected_tax_system': selected_tax_system,
        'selected_tax_code': selected_tax_code,
        'available_tax_codes': available_tax_codes,
        'available_tax_systems': available_tax_systems,
        'tax_projection': tax_projection,
        'tax_rate_percent': tax_rate_percent,
        'tax_rows': tax_rows,
    }

    return render(request, 'business_calculator.html', context)
