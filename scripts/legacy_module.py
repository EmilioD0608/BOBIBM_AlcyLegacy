
def calculate_price(base_price: float, customer_type: str = "regular") -> float:
    """Calcula el precio final aplicando la regla legacy de descuento."""
    if customer_type == "premium":
        return round(base_price * (1 - LEGACY_DISCOUNT), 2)
    return round(base_price, 2)


def get_legacy_status() -> str:
    """Devuelve un estado usado por servicios antiguos."""
    return "legacy-active"
