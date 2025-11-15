from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template

register = template.Library()


def _build_quantize(decimals: int) -> Decimal:
    if decimals <= 0:
        return Decimal('1')
    return Decimal('1').scaleb(-decimals)


@register.filter(name='spaced_number')
def spaced_number(value, decimals=0):
    """Format numeric values with a space-separated thousands grouping."""
    if value in (None, ''):
        return ''

    try:
        decimals = int(decimals)
    except (TypeError, ValueError):
        decimals = 0

    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return value

    quantize_to = _build_quantize(decimals)
    number = number.quantize(quantize_to, rounding=ROUND_HALF_UP)

    if decimals > 0:
        formatted = f"{number:,.{decimals}f}"
    else:
        formatted = f"{number:,.0f}"

    return formatted.replace(',', ' ')

