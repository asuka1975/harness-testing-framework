from shopcart.cart import Cart


def test_no_code_pays_subtotal() -> None:
    cart = Cart()
    cart.add("item", 440)
    assert cart.total() == 440
