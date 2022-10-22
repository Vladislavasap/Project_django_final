from datetime import date


def year(request):
    """Добавляет переменную с текущим годом."""
    a = date.today().year
    return {'year': a}
