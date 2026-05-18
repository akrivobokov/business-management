import json

from django.test import TestCase
from django.urls import reverse

from .models import Invoice, InvoiceSequence, PixelOrder


class PixelOrderApiTests(TestCase):
    def test_rejects_false_string_consent(self):
        payload = {
            'buyer_type': PixelOrder.INDIVIDUAL,
            'full_name': 'Иван Иванов',
            'telegram_nick': '@ivan',
            'phone': '+79990000000',
            'banner_image_url': 'https://example.com/banner.jpg',
            'banner_target_url': 'https://example.com',
            'cell_count': 5,
            'placement_x': 1,
            'placement_y': 1,
            'placement_width': 1,
            'placement_height': 5,
            'personal_data_consent': 'false',
        }

        response = self.client.post(
            reverse('create_pixel_order'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(PixelOrder.objects.count(), 0)

    def test_creates_legal_order_and_invoice_sequence(self):
        payload = {
            'buyer_type': PixelOrder.LEGAL,
            'organization_name': 'ООО Тест',
            'inn': '1234567890',
            'email': 'test@example.com',
            'telegram_nick': '@test',
            'phone': '+79990000000',
            'banner_image_url': 'https://example.com/banner.jpg',
            'banner_target_url': 'https://example.com',
            'cell_count': 21,
            'placement_x': 10,
            'placement_y': 10,
            'placement_width': 3,
            'placement_height': 7,
            'personal_data_consent': True,
        }

        response = self.client.post(
            reverse('create_pixel_order'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['amount'], 63000)
        self.assertEqual(body['payment']['invoice_number'], 'НП00001')
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(InvoiceSequence.objects.get(pk=1).last_number, 1)

    def test_rejects_out_of_bounds_placement(self):
        payload = {
            'buyer_type': PixelOrder.INDIVIDUAL,
            'full_name': 'Иван Иванов',
            'telegram_nick': '@ivan',
            'phone': '+79990000000',
            'banner_image_url': 'https://example.com/banner.jpg',
            'banner_target_url': 'https://example.com',
            'cell_count': 4,
            'placement_x': 383,
            'placement_y': 2159,
            'placement_width': 2,
            'placement_height': 2,
            'personal_data_consent': True,
        }

        response = self.client.post(
            reverse('create_pixel_order'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('пределы поля', response.json()['error'])

    def test_rejects_cell_count_mismatch(self):
        payload = {
            'buyer_type': PixelOrder.INDIVIDUAL,
            'full_name': 'Иван Иванов',
            'telegram_nick': '@ivan',
            'phone': '+79990000000',
            'banner_image_url': 'https://example.com/banner.jpg',
            'banner_target_url': 'https://example.com',
            'cell_count': 10,
            'placement_x': 1,
            'placement_y': 1,
            'placement_width': 2,
            'placement_height': 2,
            'personal_data_consent': True,
        }

        response = self.client.post(
            reverse('create_pixel_order'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Количество ячеек', response.json()['error'])
