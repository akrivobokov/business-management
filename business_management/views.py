import json
import logging
import os
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from orders.models import Banner, FIELD_HEIGHT_CELLS, FIELD_WIDTH_CELLS, Invoice, InvoiceSequence, PixelOrder

from .regulations import (
    build_tax_projection,
    build_tax_rows,
    load_regulatory_snapshot,
)

DEFAULT_MONTHLY_PROFIT = Decimal('150000')
DEFAULT_DAYS_IN_MONTH = 30
DEFAULT_MARGIN_PERCENT = Decimal('30')
CELL_SIZE = 10

INVOICE_REQUISITES = {
    'Наименование': 'Индивидуальный предприниматель Кривобоков Алексей Сергеевич',
    'ИНН': '5617097233',
    'ОГРНИП': '326565800008967',
    'Расчётный счёт': '4080281062000893693',
    'Наименование банка': 'ООО "Банк Точка"',
    'БИК банка': '044525104',
    'ИНН банка': '9721194461',
    'Корреспондентский счёт': '30101810745374525104',
    'Юридический адрес банка': '109044, Российская Федерация, г. Москва, вн.тер.г. муниципальный округ Южнопортовый, пер. 3-й Крутицкий, д.11, помещ. 7Н',
}


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


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    normalized = str(value).strip().lower()
    return normalized in {'1', 'true', 'yes', 'on'}


def _parse_required_int(payload, field_name):
    value = _parse_positive_int(payload.get(field_name), 0)
    if value <= 0:
        raise ValueError(field_name)
    return value


def _parse_non_negative_int(payload, field_name):
    value = payload.get(field_name)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(field_name) from None
    if parsed < 0:
        raise ValueError(field_name)
    return parsed


def _calculate_cells_price(cell_count):
    if cell_count <= 20:
        return cell_count * 5000
    if cell_count <= 50:
        return cell_count * 3000
    return cell_count * 1500


def _send_to_telegram(order):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_GROUP_CHAT_ID')
    if not token or not chat_id:
        return False, 'missing_token_or_chat'

    lines = [
        'Новая заявка «На пикселе»',
        f'ID: {order.id}',
        f'Тип: {order.get_buyer_type_display()}',
        f'Ячеек: {order.cell_count}',
        f'Сумма: {order.total_amount} ₽',
        f'Баннер: {order.banner_image_url}',
        f'Ссылка: {order.banner_target_url}',
    ]
    if order.buyer_type == PixelOrder.INDIVIDUAL:
        lines.extend([
            f'ФИО: {order.full_name}',
            f'Telegram: {order.telegram_nick}',
            f'Телефон: {order.phone}',
        ])
    else:
        lines.extend([
            f'Организация/ИП: {order.organization_name}',
            f'ИНН: {order.inn}',
            f'Email: {order.email}',
            f'Telegram: {order.telegram_nick}',
            f'Телефон: {order.phone}',
        ])

    payload = urlencode({'chat_id': chat_id, 'text': '\n'.join(lines)})
    request = Request(
        f'https://api.telegram.org/bot{token}/sendMessage',
        data=payload.encode('utf-8'),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    try:
        with urlopen(request, timeout=10):
            return True, ''
    except Exception as exc:  # noqa: BLE001 - логируем для последующего ретрая
        logger.warning('Telegram send failed for order %s: %s', order.id, exc)
        return False, str(exc)


def landing(request):
    banners = list(
        Banner.objects.filter(is_active=True, is_compliant=True).values(
            'id', 'title', 'image_url', 'target_url', 'cells', 'placement_x', 'placement_y', 'placement_width', 'placement_height'
        )
    )
    return render(
        request,
        'landing.html',
        {
            'banners': banners,
            'field_width': FIELD_WIDTH_CELLS * CELL_SIZE,
            'field_height': FIELD_HEIGHT_CELLS * CELL_SIZE,
            'cell_size': CELL_SIZE,
            'total_cells': FIELD_WIDTH_CELLS * FIELD_HEIGHT_CELLS,
            'field_width_cells': FIELD_WIDTH_CELLS,
            'field_height_cells': FIELD_HEIGHT_CELLS,
        },
    )


@csrf_exempt
def create_pixel_order(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        payload = request.POST.dict()

    buyer_type = payload.get('buyer_type')
    if buyer_type not in (PixelOrder.INDIVIDUAL, PixelOrder.LEGAL):
        return JsonResponse({'error': 'Некорректный тип покупателя'}, status=400)

    try:
        placement_x = _parse_non_negative_int(payload, 'placement_x')
        placement_y = _parse_non_negative_int(payload, 'placement_y')
        placement_width = _parse_required_int(payload, 'placement_width')
        placement_height = _parse_required_int(payload, 'placement_height')
    except ValueError as exc:
        return JsonResponse({'error': f'Укажите корректное значение поля {exc.args[0]}'}, status=400)

    if placement_x + placement_width > FIELD_WIDTH_CELLS:
        return JsonResponse({'error': 'Баннер выходит за пределы поля по ширине.'}, status=400)
    if placement_y + placement_height > FIELD_HEIGHT_CELLS:
        return JsonResponse({'error': 'Баннер выходит за пределы поля по высоте.'}, status=400)

    cell_count = _parse_positive_int(payload.get('cell_count'), placement_width * placement_height)
    if cell_count <= 0:
        return JsonResponse({'error': 'Укажите корректное количество ячеек'}, status=400)
    if cell_count != placement_width * placement_height:
        return JsonResponse({'error': 'Количество ячеек должно совпадать с площадью баннера.'}, status=400)

    consent = _parse_bool(payload.get('personal_data_consent'))
    if not consent:
        return JsonResponse({'error': 'Необходимо согласие на обработку персональных данных'}, status=400)

    common = {
        'buyer_type': buyer_type,
        'telegram_nick': payload.get('telegram_nick', '').strip(),
        'phone': payload.get('phone', '').strip(),
        'banner_image_url': payload.get('banner_image_url', '').strip(),
        'banner_target_url': payload.get('banner_target_url', '').strip(),
        'cell_count': cell_count,
        'placement_x': placement_x,
        'placement_y': placement_y,
        'placement_width': placement_width,
        'placement_height': placement_height,
        'personal_data_consent': consent,
        'total_amount': _calculate_cells_price(cell_count),
    }

    required = ['telegram_nick', 'phone', 'banner_image_url', 'banner_target_url']
    if buyer_type == PixelOrder.INDIVIDUAL:
        common['full_name'] = payload.get('full_name', '').strip()
        required.append('full_name')
    else:
        common['organization_name'] = payload.get('organization_name', '').strip()
        common['inn'] = payload.get('inn', '').strip()
        common['email'] = payload.get('email', '').strip()
        required.extend(['organization_name', 'inn', 'email'])

    missing = [field for field in required if not common.get(field)]
    if missing:
        return JsonResponse({'error': f'Заполните обязательные поля: {", ".join(missing)}'}, status=400)

    order = PixelOrder.objects.create(**common)
    order.telegram_attempts = 1
    sent, error = _send_to_telegram(order)
    if sent:
        order.telegram_status = 'sent'
        order.telegram_error = ''
    else:
        order.telegram_status = 'failed'
        order.telegram_error = error
    order.save(update_fields=['telegram_attempts', 'telegram_status', 'telegram_error'])

    response = {
        'ok': True,
        'order_id': order.id,
        'amount': order.total_amount,
        'donation_note': '10% от продаж команда «На пикселе» направляет на благотворительность.',
    }

    if buyer_type == PixelOrder.INDIVIDUAL:
        response['payment'] = {
            'type': 'online',
            'methods': ['ЮMoney', 'СБП'],
            'title': 'Выберите способ оплаты',
        }
    else:
        invoice = Invoice.objects.create(order=order, number=InvoiceSequence.next_number())
        response['payment'] = {
            'type': 'invoice',
            'invoice_number': invoice.number,
            'buyer_name': order.organization_name,
            'requisites': INVOICE_REQUISITES,
        }

    return JsonResponse(response)


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
logger = logging.getLogger(__name__)
