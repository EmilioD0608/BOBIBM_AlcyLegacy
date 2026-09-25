
from legacy_module import calculate_price


def calculate_customer_price(base_price: float, customer_type: str = "regular") -> float:
    """Calcula el precio usando la lógica del módulo legacy."""
    return calculate_price(base_price, customer_type)


def calculate_bulk_price(base_price: float, quantity: int) -> float:
    """Calcula un precio para compras por volumen."""
    total = base_price * quantity
    if quantity >= 10:
        total *= 0.95
    return round(total, 2)
