from decimal import Decimal

from django.test import SimpleTestCase

from business_management.calculator import (
    DEFAULT_DAYS_IN_MONTH,
    DEFAULT_MARGIN_PERCENT,
    DEFAULT_MONTHLY_PROFIT,
    calculate_business_plan,
    parse_decimal_input,
    parse_margin_percent,
    parse_positive_int,
)


class CalculatorHelpersTest(SimpleTestCase):
    def test_parse_decimal_input_handles_spaces(self):
        result = parse_decimal_input(' 200 000,50 ', Decimal('1'))
        self.assertEqual(result, Decimal('200000.50'))

    def test_parse_margin_percent_caps_upper_bound(self):
        result = parse_margin_percent('250')
        self.assertEqual(result, Decimal('99.9'))

    def test_parse_positive_int_fallback(self):
        self.assertEqual(parse_positive_int('-2', 30), 30)

    def test_calculate_business_plan_defaults(self):
        context = calculate_business_plan(
            DEFAULT_MONTHLY_PROFIT,
            DEFAULT_DAYS_IN_MONTH,
            DEFAULT_MARGIN_PERCENT,
        )
        self.assertEqual(context['daily_profit_target'], Decimal('5000'))
        self.assertEqual(
            context['monthly_operational_cost'].quantize(Decimal('1')),
            Decimal('350000'),
        )
        self.assertEqual(context['selected_opf']['code'], 'IP')
        self.assertEqual(len(context['sales_breakdown']), 10)
        self.assertTrue(context['tax_rows'])
