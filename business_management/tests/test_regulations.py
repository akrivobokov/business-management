from decimal import Decimal

from django.test import SimpleTestCase

from business_management import regulations


class RegulatoryHelpersTest(SimpleTestCase):
    def test_safe_decimal_happy_path(self):
        self.assertEqual(regulations._safe_decimal('12.34'), Decimal('12.34'))
        self.assertEqual(regulations._safe_decimal('5'), Decimal('5'))
        self.assertEqual(regulations._safe_decimal('-0.5'), Decimal('-0.5'))

    def test_safe_decimal_invalid_value(self):
        self.assertEqual(regulations._safe_decimal('abc'), Decimal('0'))
        self.assertEqual(regulations._safe_decimal(''), Decimal('0'))
        self.assertEqual(regulations._safe_decimal(None), Decimal('0'))

    def test_safe_decimal_custom_default(self):
        self.assertEqual(regulations._safe_decimal('abc', default='1.5'), Decimal('1.5'))
        self.assertEqual(regulations._safe_decimal(None, default='-1'), Decimal('-1'))

    def test_build_tax_projection_revenue_basis(self):
        tax_info = {
            'code': 'TEST',
            'effective_rate': '0.20',
            'basis': 'revenue',
        }
        projection = regulations.build_tax_projection(Decimal('5000'), Decimal('3000'), 30, tax_info)
        self.assertEqual(projection['rate_percent'], Decimal('20'))
        self.assertEqual(projection['daily_revenue'], Decimal('10000'))
        self.assertEqual(projection['tax_daily'], Decimal('2000'))

    def test_build_tax_projection_profit_basis(self):
        tax_info = {
            'code': 'TEST',
            'effective_rate': '0.20',
            'basis': 'profit',
        }
        projection = regulations.build_tax_projection(Decimal('5000'), Decimal('3000'), 30, tax_info)
        self.assertEqual(projection['daily_revenue'], Decimal('9250'))
        self.assertEqual(projection['tax_daily'], Decimal('1250'))

    def test_build_tax_rows_keeps_rate_percent(self):
        snapshot = regulations.RegulatorySnapshot(regulations.DEFAULT_REGULATORY_DATA)
        rows = regulations.build_tax_rows(Decimal('5000'), Decimal('3000'), 30, ['USN_6'], snapshot)
        self.assertEqual(rows[0]['rate_percent'], Decimal('6'))
