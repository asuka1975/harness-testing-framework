import pytest
from shopcart.cart import Cart
from shopcart.discount import parse_code


def _cart(subtotal: int) -> Cart:
    cart = Cart()
    cart.add("item", subtotal)
    return cart


def test_percent_code_takes_percentage_off() -> None:
    assert _cart(1000).total("PCT10") == 900


def test_amount_code_takes_amount_off() -> None:
    assert _cart(1000).total("OFF500") == 500


def test_amount_code_never_goes_below_zero() -> None:
    assert _cart(300).total("OFF500") == 0


def test_no_code_pays_subtotal() -> None:
    assert _cart(440).total() == 440


@pytest.mark.parametrize("code", ["PCT0", "PCT51", "XYZ", "OFF"])
def test_invalid_codes_are_rejected(code: str) -> None:
    with pytest.raises(ValueError):
        parse_code(code)


def test_percent_discount_rounds_the_discount_down() -> None:
    # 333 円の 10% は 33.3 円。割引額を 33 円に切り捨てるので、支払額は 300 円
    assert _cart(333).total("PCT10") == 300
