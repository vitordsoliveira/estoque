from decimal import Decimal, InvalidOperation


def parse_decimal_input(raw_value):
    if raw_value is None:
        return None

    value = str(raw_value).strip().replace(' ', '')
    if not value:
        return None

    normalized = value

    if ',' in normalized and '.' in normalized:
        if normalized.rfind(',') > normalized.rfind('.'):
            normalized = normalized.replace('.', '').replace(',', '.')
        else:
            normalized = normalized.replace(',', '')
    elif ',' in normalized:
        normalized = normalized.replace(',', '.')
    elif normalized.count('.') > 1:
        parts = normalized.split('.')
        normalized = ''.join(parts[:-1]) + '.' + parts[-1]

    try:
        return float(Decimal(normalized))
    except InvalidOperation as exc:
        raise ValueError('Valor numérico inválido.') from exc


def parse_scaled_input(raw_value):
    if raw_value is None:
        return None

    value = str(raw_value).strip().replace(' ', '')
    if not value:
        return None

    if value.isdigit():
        return float(Decimal(value) / Decimal('1000'))

    return parse_decimal_input(value)