import pytest

# from SQLmaintain import check_phone
from datetime import date
import requests
from SQLmaintain import OrderTableCRUD


@pytest.mark.parametrize(
    "product_code,SQL_exist_amount,new_qty,salse_credit, expected",
    [
        ("pomelo-G-10", 15, 1, 30, "保留"),  # 未超出保留額度
        ("pomelo-G-10", 15, 1, 25, "保留"),  # 剛好滿保留額度
        ("pomelo-U-15", 20, 2, 60, "排單"),  # 非排單品項
        ("pomelo-G-15", 30, 1, 30, "排單"),  # 已超出保留額度
        ("pomelo-G-10", 15, 1, 20, "退回"),  # 剛好超出保留額度
        ("pomelo-G-1", 18, 2, 20, "保留"),  # 測試單顆+剛好滿保留額度
        ("pomelo-G-20", 200, 1, 200, "排單"),  # 剛好滿保留額度後再新增一筆的情況
    ],
)
def test_new_order_status(
    product_code, SQL_exist_amount, new_qty, salse_credit, expected
):
    result = OrderTableCRUD.check_new_order_status(
        product_code, SQL_exist_amount, new_qty, salse_credit
    )
    assert result == expected
