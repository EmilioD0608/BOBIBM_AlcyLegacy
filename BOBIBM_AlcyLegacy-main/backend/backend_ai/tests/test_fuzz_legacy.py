"""Adversarial and fuzz testing for scripts/legacy_module.py and its consumers.

Milestone M4 Challenger 2 verification suite.
Tests edge-case prices, customer_type variations, crash resilience,
float return guarantees, rounding precision, and downstream consumer stability.
"""

import math
import random
import sys
from decimal import Decimal
import pytest

from legacy_module import calculate_price, get_legacy_status, LEGACY_DISCOUNT
import pricing_utils
import notification_service


# ==============================================================================
# 1. Edge-Case Prices Suite
# ==============================================================================

@pytest.mark.parametrize(
    "price,customer_type,expected",
    [
        (0.0, "regular", 0.0),
        (0.0, "premium", 0.0),
        (-0.0, "regular", -0.0),
        (-0.0, "premium", -0.0),
        (-100.0, "regular", -100.0),
        (-100.0, "premium", -85.0),
        (-0.01, "regular", -0.01),
        (-0.01, "premium", -0.01),
        (-49.99, "regular", -49.99),
        (-49.99, "premium", -42.49),
        (1e12, "regular", 1000000000000.0),
        (1e12, "premium", 850000000000.0),
        (-1e12, "regular", -1000000000000.0),
        (-1e12, "premium", -850000000000.0),
        (1e-10, "regular", 0.0),
        (1e-10, "premium", 0.0),
        (0.005, "regular", 0.01),
        (0.00499, "regular", 0.0),
        (10.005, "regular", 10.01),
        (10.004, "regular", 10.0),
        (10.123456, "regular", 10.12),
        (10.123456, "premium", 8.6),
        (99.999, "regular", 100.0),
        (99.999, "premium", 85.0),
    ],
)
def test_edge_case_prices(price, customer_type, expected):
    """Verify calculate_price with zero, negative, extreme, and fractional cent prices."""
    result = calculate_price(price, customer_type)
    assert result == pytest.approx(expected, abs=1e-4)
    # Check that rounding to 2 decimals holds
    assert result == round(result, 2)


# ==============================================================================
# 2. Customer Type Variations Suite
# ==============================================================================

@pytest.mark.parametrize(
    "customer_type,should_apply_discount",
    [
        ("regular", False),
        ("premium", True),
        ("PREMIUM", False),  # Case sensitive legacy check
        ("Premium", False),
        ("pReMiUm", False),
        ("REGULAR", False),
        ("Regular", False),
        ("vip", False),
        ("gold", False),
        ("enterprise", False),
        ("", False),
        (" ", False),
        ("  premium  ", False),
        ("\tpremium\n", False),
        (None, False),
        (123, False),
        (0, False),
        (False, False),
        (True, False),
        (3.14, False),
    ],
)
def test_customer_type_variations(customer_type, should_apply_discount):
    """Verify that calculate_price never crashes on customer_type variations

    Only exact string 'premium' triggers the discount in legacy logic; all others
    cleanly fall back to standard undiscounted price without raising exceptions.
    """
    base = 100.0
    result = calculate_price(base, customer_type)
    if should_apply_discount:
        assert result == 85.0
    else:
        assert result == 100.0


# ==============================================================================
# 3. Crash Resilience and Precision Property-Based Fuzzing
# ==============================================================================

def test_fuzz_calculate_price_random_samples():
    """Fuzz calculate_price across 2,000 randomized float values and customer types.

    Properties verified:
    1. calculate_price never raises an exception for valid float inputs.
    2. Result is rounded to at most 2 decimal places.
    3. Mathematical property: premium result == round(base_price * 0.85, 2).
    4. Mathematical property: regular/other result == round(base_price, 2).
    """
    random.seed(42)  # Deterministic repeatability

    customer_types_pool = [
        "regular",
        "premium",
        "PREMIUM",
        "Premium",
        "unknown",
        "vip",
        "",
        " ",
        None,
        "standard",
    ]

    # Test broad ranges: small, normal, negative, large, fractional
    for _ in range(2000):
        category = random.choice(["fractional", "normal", "extreme", "negative", "subcent"])
        if category == "fractional":
            base_price = round(random.uniform(-1000.0, 1000.0), random.randint(3, 8))
        elif category == "normal":
            base_price = round(random.uniform(0.01, 10000.0), 2)
        elif category == "extreme":
            base_price = random.uniform(1e6, 1e12) * random.choice([1, -1])
        elif category == "negative":
            base_price = -random.uniform(0.01, 5000.0)
        else:  # subcent
            base_price = random.uniform(0.0001, 0.0099)

        ctype = random.choice(customer_types_pool)

        # Execution must not crash
        result = calculate_price(base_price, ctype)

        # Result precision property: round(result, 2) must equal result
        assert result == round(result, 2)

        # Oracle check
        if ctype == "premium":
            expected = round(base_price * (1 - LEGACY_DISCOUNT), 2)
        else:
            expected = round(base_price, 2)

        assert result == expected


def test_calculate_price_always_float_when_given_float():
    """Verify that when base_price is float, calculate_price always returns float."""
    test_values = [0.0, -0.0, 100.0, 50.5, 42.49, -100.0, 1e12]
    for val in test_values:
        for ctype in ["regular", "premium", "other", None]:
            res = calculate_price(val, ctype)
            assert isinstance(res, float), f"Expected float for input {val}, got {type(res)}"


# ==============================================================================
# 4. Downstream Consumers Stability Suite
# ==============================================================================

@pytest.mark.parametrize(
    "base_price,customer_type",
    [
        (0.0, "regular"),
        (0.0, "premium"),
        (0.0, None),
        (-50.0, "regular"),
        (-50.0, "premium"),
        (-50.0, "UNKNOWN"),
        (1000000000000.0, "regular"),
        (1000000000000.0, "premium"),
        (10.005, "regular"),
        (10.005, "premium"),
        (10.005, None),
    ],
)
def test_pricing_utils_consumer(base_price, customer_type):
    """Verify pricing_utils.calculate_customer_price propagates calculate_price cleanly."""
    res = pricing_utils.calculate_customer_price(base_price, customer_type)
    expected = calculate_price(base_price, customer_type)
    assert res == expected
    assert res == round(res, 2)


@pytest.mark.parametrize(
    "base_price,customer_type",
    [
        (0.0, "regular"),
        (0.0, "premium"),
        (0.0, None),
        (-50.0, "regular"),
        (-50.0, "premium"),
        (-50.0, "PREMIUM"),
        (1000000000000.0, "regular"),
        (1000000000000.0, "premium"),
        (10.005, "regular"),
        (10.005, "premium"),
        (10.005, None),
    ],
)
def test_notification_service_consumer(base_price, customer_type):
    """Verify notification_service.build_price_notification formats output without crashing."""
    msg = notification_service.build_price_notification(base_price, customer_type)
    expected_price = calculate_price(base_price, customer_type)
    assert msg.startswith("Precio final: $")
    assert f"${expected_price:.2f}" in msg


def test_notification_service_legacy_status():
    """Verify build_legacy_notification returns valid legacy string."""
    msg = notification_service.build_legacy_notification()
    assert msg == "Estado del sistema: legacy-active"


def test_pricing_utils_bulk_price_edge_cases():
    """Verify calculate_bulk_price edge cases."""
    assert pricing_utils.calculate_bulk_price(10.0, 0) == 0.0
    assert pricing_utils.calculate_bulk_price(10.0, 9) == 90.0
    assert pricing_utils.calculate_bulk_price(10.0, 10) == 95.0
    assert pricing_utils.calculate_bulk_price(10.0, 100) == 950.0
    assert pricing_utils.calculate_bulk_price(0.0, 50) == 0.0
    assert pricing_utils.calculate_bulk_price(-10.0, 10) == -95.0
