"""Tests for scripts/legacy_module.py and consumer integration."""

import pytest
import legacy_module
from legacy_module import calculate_price, get_legacy_status, LEGACY_DISCOUNT
import pricing_utils
import notification_service


def test_legacy_discount_constant():
    """Verify that LEGACY_DISCOUNT is defined as 0.15."""
    assert hasattr(legacy_module, "LEGACY_DISCOUNT")
    assert LEGACY_DISCOUNT == 0.15


def test_calculate_price_regular_customer():
    """calculate_price for regular customer returns undiscounted price."""
    assert calculate_price(100.0, "regular") == 100.0
    assert calculate_price(50.0, "regular") == 50.0
    assert calculate_price(0.0, "regular") == 0.0


def test_calculate_price_default_is_regular():
    """calculate_price defaults to regular customer if customer_type omitted."""
    assert calculate_price(100.0) == 100.0


def test_calculate_price_premium_customer():
    """calculate_price for premium customer returns 15% discounted price."""
    # 100 * (1 - 0.15) = 85.0
    assert calculate_price(100.0, "premium") == 85.0
    # 200 * 0.85 = 170.0
    assert calculate_price(200.0, "premium") == 170.0
    # 49.99 * 0.85 = 42.4915 -> 42.49
    assert calculate_price(49.99, "premium") == 42.49


def test_get_legacy_status():
    """get_legacy_status returns 'legacy-active'."""
    assert get_legacy_status() == "legacy-active"


def test_pricing_utils_integration():
    """Verify that consumer scripts/pricing_utils.py executes without error."""
    assert pricing_utils.calculate_customer_price(100.0, "regular") == 100.0
    assert pricing_utils.calculate_customer_price(100.0, "premium") == 85.0
    assert pricing_utils.calculate_bulk_price(10.0, 5) == 50.0
    assert pricing_utils.calculate_bulk_price(10.0, 10) == 95.0  # 100 * 0.95


def test_notification_service_integration():
    """Verify that consumer scripts/notification_service.py executes without error."""
    reg_msg = notification_service.build_price_notification(100.0, "regular")
    prem_msg = notification_service.build_price_notification(100.0, "premium")
    legacy_msg = notification_service.build_legacy_notification()

    assert reg_msg == "Precio final: $100.00"
    assert prem_msg == "Precio final: $85.00"
    assert legacy_msg == "Estado del sistema: legacy-active"
