from django.shortcuts import render

from .calculator import (
    DEFAULT_DAYS_IN_MONTH,
    DEFAULT_MARGIN_PERCENT,
    DEFAULT_MONTHLY_PROFIT,
    calculate_business_plan,
    parse_decimal_input,
    parse_margin_percent,
    parse_positive_int,
)


def landing(request):
    return render(request, 'landing.html')


def business_calculator(request):
    monthly_profit = parse_decimal_input(
        request.GET.get('monthly_profit'), DEFAULT_MONTHLY_PROFIT
    )
    days_in_month = parse_positive_int(
        request.GET.get('days_in_month'), DEFAULT_DAYS_IN_MONTH
    )
    margin_percent = parse_margin_percent(request.GET.get('margin_percent'))

    context = calculate_business_plan(
        monthly_profit,
        days_in_month,
        margin_percent,
        request.GET.get('opf_code'),
        request.GET.get('tax_system_code'),
    )

    return render(request, 'business_calculator.html', context)
