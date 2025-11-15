#!/usr/bin/env python
"""Simple CLI wrapper around the business calculator."""

import argparse
import os
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_management.settings')

import django  # noqa: E402

django.setup()

from business_management.calculator import (  # noqa: E402
    DEFAULT_DAYS_IN_MONTH,
    DEFAULT_MARGIN_PERCENT,
    DEFAULT_MONTHLY_PROFIT,
    calculate_business_plan,
    parse_decimal_input,
    parse_margin_percent,
    parse_positive_int,
)


def spaced_money(value: Decimal) -> str:
    return f"{value:,.2f}".replace(',', ' ').rstrip('0').rstrip('.')


def print_tax_rows(rows):
    if not rows:
        print('\nНалоговые режимы недоступны для выбранной ОПФ.')
        return
    print('\nНалоговые режимы:')
    for row in rows:
        rate_percent = row.get('rate_percent') or 0
        print(
            f"- {row['title']}: выручка {spaced_money(row['monthly_revenue'])} ₽/мес, "
            f"налоги {spaced_money(row['tax_monthly'])} ₽/мес (ставка {rate_percent:.2f}% )"
        )


def print_sales_breakdown(rows):
    print('\nДекомпозиция продаж:')
    for row in rows:
        print(
            f"- {row['sales_per_day']} продаж/день → {spaced_money(row['profit_per_sale'])} ₽ чистой прибыли с продажи, "
            f"{row['monthly_sales']} продаж/мес"
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description='Быстрый расчёт декомпозиции прибыли и налоговой нагрузки.'
    )
    parser.add_argument('--monthly-profit', default=str(DEFAULT_MONTHLY_PROFIT))
    parser.add_argument('--days-in-month', default=str(DEFAULT_DAYS_IN_MONTH))
    parser.add_argument('--margin-percent', default=str(DEFAULT_MARGIN_PERCENT))
    parser.add_argument('--opf', dest='opf_code', default=None)
    parser.add_argument('--tax-system', dest='tax_system_code', default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    monthly_profit = parse_decimal_input(args.monthly_profit, DEFAULT_MONTHLY_PROFIT)
    days_in_month = parse_positive_int(args.days_in_month, DEFAULT_DAYS_IN_MONTH)
    margin_percent = parse_margin_percent(args.margin_percent)

    context = calculate_business_plan(
        monthly_profit,
        days_in_month,
        margin_percent,
        args.opf_code,
        args.tax_system_code,
    )

    print('=== Ключевые показатели ===')
    print(f"Желаемая прибыль в месяц: {spaced_money(context['monthly_profit'])} ₽")
    print(f"Прибыль в день: {spaced_money(context['daily_profit_target'])} ₽")
    print(f"Расходы в день: {spaced_money(context['daily_operational_cost'])} ₽")
    print(
        f"База (прибыль + расходы) в месяц: {spaced_money(context['pre_tax_monthly_base'])} ₽"
    )

    selected_opf = context['selected_opf']
    print('\nВыбранная ОПФ:', selected_opf.get('title') if selected_opf else 'не выбрана')
    if context['selected_tax_system']:
        print('Система налогообложения:', context['selected_tax_system'].get('title'))

    print_tax_rows(context['tax_rows'])
    print_sales_breakdown(context['sales_breakdown'])


if __name__ == '__main__':
    main()
