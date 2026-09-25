
from legacy_module import calculate_price, get_legacy_status


def build_price_notification(base_price: float, customer_type: str = "regular") -> str:
    """Construye el mensaje de precio para una notificación."""
    price = calculate_price(base_price, customer_type)
    return f"Precio final: ${price:.2f}"


def build_legacy_notification() -> str:
    """Construye un mensaje usando el estado del sistema legacy."""
    status = get_legacy_status()
    return f"Estado del sistema: {status}"
