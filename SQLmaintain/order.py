import sqlite3
import traceback
import math
from typing import Any
from datetime import datetime, date
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np

from .SQLutils import check_phone, check_internal_id_format
from config import get_db_path

LAST_PRODUCTION = 4130
RESERVE_RATIO = {
    "SHR01": 0.01613,
    "SHR03": 0.06452,
    "SHR05": 0.23226,
    "SHR06": 0.64517,
    "SHR07": 0.01613,
    "SHR08": 0.02581,
}
# 2027正式採收日(2027,8,21)
# 2027開始接單日(2027,8,15)
HARVEST_DAY = date(2027, 8, 21)
START_ORDER_TAKING = date(2026, 8, 15)
END_ORDER_TAKING = date(2027, 12, 31)
HARVEST_DAY_PD = pd.Timestamp(2027, 8, 21)
START_ORDER_TAKING_PD = pd.Timestamp(2026, 8, 15)


class CustomerTableCRUD:
    @staticmethod
    def create_customer_table():
        database = get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = """CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            customer_id TEXT UNIQUE,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL CHECK (
            customer_phone GLOB '09[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]' 
            OR customer_phone GLOB '0[2-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
            OR customer_phone GLOB '0[2-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
            customer_address TEXT NOT NULL ,
            customer_level INTEGER DEFAULT 1,
            payment_method TEXT CHECK (payment_method IN ('Cash','Transfer')),
            transfer_account TEXT,
            notes TEXT,
            create_by TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (customer_name, customer_phone)
            );"""
            cursor.execute(query)
            con.commit()

    @staticmethod
    def create_customer_trigger(table="customers"):
        database = get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f"""CREATE TRIGGER trg_customer_id
            AFTER INSERT ON {table}
            FOR EACH ROW
            BEGIN
                UPDATE customers
                SET customer_id =
                printf('Cn') ||
                substr(strftime('%Y', NEW.created_at), 3, 2) || '-' ||
                printf('%03d', NEW.id)
                WHERE id = NEW.id;
            END;"""
            cursor.execute(query)
            con.commit()
        return f"{table}表格的Trigger: trg_customer_id 建立成功"

    @staticmethod
    def read_customer_table(customer_id=None, customer_name=None):
        if customer_id is not None or customer_name is not None:
            column_dict = {
                "customer_id": customer_id,
                "customer_name": customer_name,
            }
            data_dict = {k: v for k, v in column_dict.items() if v is not None}
            data_keys = list(data_dict.keys())
            # print(data_keys)
            condition_columns = []
            for key in data_keys:
                key += "=?"
                condition_columns.append(key)
            condition_statement = " AND ".join(condition_columns)
            values = list(data_dict.values())

            sql = f"""SELECT * FROM customers WHERE {condition_statement}"""

            database = get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(sql, tuple(values))
                customers = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                customers_data = [dict(zip(columns, row)) for row in customers]
                return customers_data
        else:
            database = get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = "SELECT * FROM customers"
                cursor.execute(query)
                customers = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                customers_data = [dict(zip(columns, row)) for row in customers]
                return customers_data

    @staticmethod
    def customer_fuzzy_search(customer_name) -> list[dict]:
        database = get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "SELECT * FROM customers WHERE customer_name LIKE ?"
            data = (f"%{customer_name}%",)
            cursor.execute(query, data)
            customers = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            customers_data = [dict(zip(columns, row)) for row in customers]
            return customers_data

    @staticmethod
    def insert_customer(
        customer_name,
        customer_phone,
        customer_address,
        create_by,
        note=None,
        payment_method="Cash",
        transfer_account=None,
    ):
        try:
            check_result, customer_phone, _ = check_phone(customer_phone)
            if not check_result:
                return False, "輸入電話號碼格式不正確"
            if payment_method not in ["Cash", "Transfer"]:
                return False, "付款只有現金與匯款方式"
            if payment_method == "Transfer" and transfer_account is None:
                return False, "轉帳客戶請輸入預計匯款帳戶"

            column_dict = {
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_address": customer_address,
                "payment_method": payment_method,
                "transfer_account": transfer_account,
                "note": note,
                "create_by": create_by,
            }
            required_column = [
                "customer_name",
                "customer_phone",
                "customer_address",
                "payment_method",
                "create_by",
            ]
            data_dict = {
                k: v
                for k, v in column_dict.items()
                if k in required_column or v is not None
            }
            # print(data_dict)
            columns = ", ".join(data_dict.keys())
            placeholders = ", ".join("?" * len(data_dict))

            sql = f"""INSERT INTO customers ({columns}) VALUES ({placeholders})"""
            database = get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(sql, tuple(data_dict.values()))
                con.commit()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = f"SELECT customer_id FROM customers WHERE customer_name=?"
                data = (customer_name,)
                cursor.execute(query, data)
                customer_id = cursor.fetchone()
            # customer_id = "測試ID"
            return (
                True,
                f"客戶{customer_name}資料建立成功，客戶編號為{customer_id}",
            )
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                return False, f"已有此客戶名稱{customer_name}"
            else:
                traceback.print_exc()
                return False, f"發生錯誤:{e}"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def delete_customer(id):
        database = get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "DELETE FROM customers WHERE id=?"
            data = (id,)
            cursor.execute(query, data)
            con.commit()
        return f"已從customers表格中刪除{id}紀錄"

    @staticmethod
    def read_customer_for_flask(customer_name):
        database = get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "SELECT * FROM customers WHRER custmoer_name=?"
            data = (customer_name,)
            cursor.execute(query, data)
            customer_info = cursor.fetchall()
        if customer_info is None:
            return False, f"資料庫中查無客戶名稱{customer_name}"
        elif len(customer_info) > 1:
            columns = [col[0] for col in cursor.description]
            customer_data = [dict(zip(columns, row)) for row in customer_info]
            customer_data[0].pop("id")
            customer_data[0].pop("create_by")
            return False, customer_info
        else:
            columns = [col[0] for col in cursor.description]
            customer_data = [dict(zip(columns, row)) for row in customer_info]
            customer_data[0].pop("id")
            customer_data[0].pop("create_by")
            # customer_data[0].pop('created_at')
            return True, customer_info

    @staticmethod
    def update_customer(customer_id, column, new_data):
        columns = [
            "customer_name",
            "customer_phone",
            "customer_address",
            "customer_level",
            "payment_method",
            "transfer_account",
            "notes",
        ]
        try:
            customer_data = CustomerTableCRUD.read_customer_table(
                customer_id=customer_id
            )
            if not customer_data:
                return False, f"找不到客戶編號為{customer_id}的資料"

            if column in columns:
                database = get_db_path()
                with sqlite3.connect(database) as con:
                    cursor = con.cursor()
                    query = f"UPDATE customers SET {column}=? WHERE customer_id=?"
                    data = (new_data, customer_id)
                    cursor.execute(query, data)
                    con.commit()
                return True, f"已將{customer_id}的欄位{column}修改為{new_data}"
            else:
                return False, f"找不到{column}可修改其欄位"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"


class OrderTableCRUD:

    @staticmethod
    def read_order_table(
        order_id=None, receiver_name=None, status=None
    ) -> list[dict[Any, Any]]:
        status_list = [
            "not_shipped",
            "not_paid",
            "order_canceled",
            "complete",
            "bad debt",
        ]  # 應該要把檢查的段落放在db_admin與flask那裏

        if order_id is not None or receiver_name is not None or status is not None:
            if status not in [
                status_list,
                None,
            ]:  # 應該要把檢查的段落放在db_admin與flask那裏
                return [
                    {"read result": "wrong status"}
                ]  # 應該要把檢查的段落放在db_admin與flask那裏
            column_dict = {
                "order_id": order_id,
                "receiver_name": receiver_name,
                "status": status,
            }
            data_dict = {k: v for k, v in column_dict.items() if v is not None}
            data_keys = list(data_dict.keys())
            # print(data_keys)
            condition_columns = []
            for key in data_keys:
                key += "=?"
                condition_columns.append(key)
            condition_statement = " AND ".join(condition_columns)
            values = list(data_dict.values())

            sql = f"""SELECT * FROM orders WHERE {condition_statement}"""

            database = get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(sql, tuple(values))
                customers = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                customers_data = [dict(zip(columns, row)) for row in customers]
                return customers_data

        else:
            sql = """SELECT * FROM orders"""
            database = get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(
                    sql,
                )
                customers = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                customers_data = [dict(zip(columns, row)) for row in customers]
                return customers_data

    @staticmethod
    def read_order_for_flask(
        create_by, order_id=None, reciver_name=None, status="not_shipped"
    ):  # 沒權限分級前，這個設計給flask只讀create是自己的
        pass

    @staticmethod
    def read_order_for_xlsx(year: int) -> pd.DataFrame:

        database = get_db_path()
        with sqlite3.connect(database) as con:
            sql = "SELECT * FROM orders WHERE created_at BETWEEN ? AND ?"
            sql_condition = (f"{year}-01-01", f"{year}-12-31")
            df = pd.read_sql_query(con=con, sql=sql, params=sql_condition)
            return df

    @staticmethod
    def get_sales_df(employee_no: str) -> pd.DataFrame:
        database = get_db_path()
        with sqlite3.connect(database) as con:
            # cursor=con.cursor()
            sql = f"SELECT order_id,reserved,product_name,spec,qty,created_at FROM orders WHERE create_by=? AND created_at BETWEEN ? AND ?"
            sql_condition = (
                employee_no,
                str(START_ORDER_TAKING),
                str(END_ORDER_TAKING),
            )
            df = pd.read_sql_query(con=con, sql=sql, params=sql_condition)
            condition = [
                df["spec"] == "10斤裝",
                df["spec"] == "15斤裝",
                df["spec"] == "20斤裝",
            ]
            choice_list = [10, 15, 20]
            weight = np.select(condition, choice_list, default=0)
            df["weight"] = weight

        return df

    @staticmethod
    def get_sales_reservation(df: pd.DataFrame) -> float:
        df["created_at"] = pd.to_datetime(df["created_at"])
        condition = (df["created_at"] < HARVEST_DAY_PD) & (
            df["created_at"] > START_ORDER_TAKING_PD
        )
        condition2 = df["reserved"] == "保留"
        df = df.loc[condition2 & condition]
        reservation_weight = round((df["weight"] * df["qty"]).sum(), 2)
        # print(f"保留值={reservation_weight}")
        return reservation_weight

    @staticmethod
    def order_fuzzy_search(receiver_name) -> list[dict]:
        database = get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "SELECT * FROM orders WHERE receiver_name LIKE ?"
            data = (f"%{receiver_name}%",)
            cursor.execute(query, data)
            customers = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            customers_data = [dict(zip(columns, row)) for row in customers]
            return customers_data

    @staticmethod
    def insert_order_table(
        reserved,
        product_code,
        product_name,
        spec,
        qty,
        customer_id,
        subtotal,
        shipment_fee,
        receiver_name,
        receiver_phone,
        receiver_address,
        create_by,
        payment_method="Cash",
        transfer_account=None,
        order_notes=None,
    ) -> tuple[bool, str]:
        try:
            check_result, reciver_phone, _ = check_phone(receiver_phone)
            if not check_result:
                return False, "輸入電話號碼格式不正確"
            if payment_method not in ["Cash", "Transfer"]:
                return False, "付款只有現金與匯款方式"
            # if payment_method == "Transfer" and transfer_account is None:
            #     return False, "轉帳客戶請輸入預計匯款帳戶"
            if (
                (not isinstance(qty, int))
                or (not isinstance(subtotal, int))
                or (not isinstance(shipment_fee, int))
            ):
                return False, "輸入的數量、貨款、運費並非數字"

            column_dict = {
                "reserved": reserved,
                "product_code": product_code,
                "product_name": product_name,
                "spec": spec,
                "qty": qty,
                "customer_id": customer_id,
                "subtotal": subtotal,
                "shipment_fee": shipment_fee,
                "receiver_name": receiver_name,
                "receiver_phone": receiver_phone,
                "receiver_address": receiver_address,
                "payment_method": payment_method,
                "transfer_account": transfer_account,
                "order_notes": order_notes,
                "create_by": create_by,
            }
            # print(column_dict)
            required_column = [
                "reserved",
                "product_code",
                "product_name",
                "spec",
                "qty",
                "customer_id",
                "subtotal",
                "shipment_fee",
                "receiver_name",
                "receiver_phone",
                "receiver_address",
                "create_by",
            ]
            data_dict = {
                k: v
                for k, v in column_dict.items()
                if k in required_column or v is not None
            }
            # print(data_dict)
            columns = ", ".join(data_dict.keys())
            placeholders = ", ".join("?" * len(data_dict))

            sql = f"""INSERT INTO orders ({columns}) VALUES ({placeholders})"""
            # print(sql)
            database = get_db_path()
            with sqlite3.connect(database) as con:
                con.execute("PRAGMA foreign_keys = ON;")
                cursor = con.cursor()
                # print(sql)
                # print(tuple(data_dict.values()))
                cursor.execute(sql, tuple(data_dict.values()))
                con.commit()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = f"SELECT order_id FROM orders WHERE receiver_name=? AND customer_id=?"
                data = (receiver_name, customer_id)
                cursor.execute(query, data)
                order_id = cursor.fetchone()[0]
            return (
                True,
                f"{order_id}",
            )
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                # return False, f"已有此客戶名稱{customer_name}"
                return False, "應該不會出現UNIQUE錯誤才對"
            else:
                traceback.print_exc()
                return False, f"發生錯誤:{e}"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"
        #

    @staticmethod
    def update_order(order_id, column, old_data, new_data):
        columns = [
            "product_code",
            "product_name",
            "spec",
            "qty",
            "subtotal",
            "shipment_fee",
            "ship_date_requested",
            "receiver_name",
            "receiver_phone",
            "receiver_address",
            "payment_method",
            "transfer_account",
            "order_notes",
        ]
        pass

    @staticmethod
    def order_shipping(order_id, shipment_date) -> str:  # 出貨確認
        try:
            database = get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = "UPDATE orders SET status=? , shipment_date=? WHERE order_id=?"
                data = ("not_paid", shipment_date, order_id)
                cursor.execute(query, data)
                con.commit()
            return f"{order_id}訂單狀態已更新至<等待收款中>"
        except Exception as e:
            traceback.print_exc()
            return f"發生未預期錯誤{e}"

    @staticmethod
    def order_complete(
        order_id, payment_reciving_date, payment_method="Cash", transfer_account=None
    ) -> str:  # 收款確認
        # payment_methods=[{"mayment_method":"Cash","transfer_account":None},{"mayment_method":"Transfer","transfer_account":transfer_account}]
        if payment_method not in ["Cash", "Transfer"]:
            return "收款方式只有現金與轉帳"
        try:
            database = get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = "UPDATE orders SET status=? , payment_reciving_date=? ,payment_method=? , transfer_account=? WHERE order_id=?"
                data = (
                    "complete",
                    payment_reciving_date,
                    payment_method,
                    transfer_account,
                    order_id,
                )
                cursor.execute(query, data)
                con.commit()
            return f"{order_id}訂單狀態已更新至<收款確認，結案>"
        except Exception as e:
            traceback.print_exc()
            return f"發生未預期的錯誤{e}"

    @staticmethod
    def order_cancel(order_id) -> str:
        try:
            database = get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = "UPDATE orders SET status=? WHERE order_id=?"
                data = ("order_canceled", order_id)
                cursor.execute(query, data)
                con.commit()
            return f"{order_id}訂單狀態已更新至<訂單取消>"
        except Exception as e:
            traceback.print_exc()
            return f"發生未預期的錯誤{e}"

    @staticmethod
    def delete_order(id) -> str:
        bool, internal_id, id_type = check_internal_id_format(id)
        print(id_type)
        if bool and id_type == "order_id":
            query = "DELETE FROM orders WHERE order_id=?"
            data = (internal_id,)
        elif not bool and internal_id is None:
            query = "DELETE FROM orders WHERE id=?"
            data = (id,)
        else:
            return "輸入id不合法，未進行刪除"
        try:
            database = get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(query, data)
                con.commit()
            return f"已從orders表格中刪除{id}的紀錄"
        except Exception as e:
            traceback.print_exc()
            return f"發生未預期的錯誤{e}"

    @staticmethod
    def check_new_order_status(
        product_code: str, old_oder: float, new_oder: int, reservation_amount: float
    ) -> str:
        """ "input the product code and weight(new_oder is qty) ,return "保留"or"排單"or"退回" """
        need_reserve_product = {
            "pomelo-G-10": 10,
            "pomelo-G-15": 15,
            "pomelo-G-20": 20,
            "pomelo-G-1": 1,
        }

        if product_code in need_reserve_product.keys():
            new_weight = new_oder * need_reserve_product[product_code]
            # print(f"本次新增重量:{new_oder}")
            if old_oder + new_weight <= reservation_amount:
                # print("O+N<=R")
                reservation_result = "保留"
            else:
                # print("O+N>R")
                if old_oder >= reservation_amount:
                    reservation_result = "排單"
                else:
                    reservation_result = "退回"

        else:
            # print("非保留項目，請直接排單")
            reservation_result = "排單"
        return reservation_result


def calculate_reserved_amount(employee_no: str) -> int:
    total_reserved_production = math.ceil(LAST_PRODUCTION * 0.75 / 10) * 10
    # print(total_reserved_production)
    personal_reversed_production = (
        RESERVE_RATIO[employee_no] * total_reserved_production
    )
    personal_reversed_production = math.floor(personal_reversed_production / 10) * 10
    return personal_reversed_production


def order_taking_date_check(today: date) -> bool:
    # today=datetime.date.today()
    if today < START_ORDER_TAKING:
        return False
    else:
        return True


def order_reserving_date_check(today: date) -> bool:
    # today=datetime.date.today()
    if today < HARVEST_DAY and today > START_ORDER_TAKING:
        return True
    else:
        return False


def check_oder_data(order_data) -> tuple[bool, str]:
    if not isinstance(order_data, dict):
        return False, "dataset not a dict"
    required_items = [
        "receiver_name",
        "receiver_phone",
        "receiver_address",
        "customer_name",
        "customer_phone",
        "customer_address",
        "product_code",
        "qty",
        "subtotal",
        "shipment_fee",
        "predict_payment_method",
    ]
    problem_info = []
    # print("開始檢查欄位為空")
    for require_item in required_items:
        # print(order_data[require_item])
        if order_data[require_item] is None or order_data[require_item] == "":
            problem_info.append(require_item)
            # print(f"這個欄位真的為空:{order_data[require_item]}")
    phone_items = ["receiver_phone", "customer_phone"]
    # print("開始檢查電話號碼")
    for phone in phone_items:
        # print(order_data[phone])
        check_bool, _, _ = check_phone(order_data[phone])
        if not check_bool:
            problem_info.append(phone)
            # print(f"這個電話號碼真的不對:{order_data[phone]}")
    number_items = ["qty", "subtotal", "shipment_fee"]
    # print("開始檢查欄位是否為數字")
    for number in number_items:
        # print(order_data[number])
        if not isinstance(order_data[number], int):
            problem_info.append(number)
            # print(f"這個資料真的不是數字:{order_data[number]}")
    str_items = [
        "receiver_name",
        "receiver_phone",
        "receiver_address",
        "customer_name",
        "customer_phone",
        "customer_address",
        "product_code",
        "predict_payment_method",
    ]
    # print("開始檢查欄位是否為字串")
    for str_item in str_items:
        # print(order_data[str_item])
        if not isinstance(order_data[str_item], str):
            problem_info.append(str_item)
            # print(f"這個資料真的不是字串:{order_data[str_item]}")
    if len(problem_info) == 0:
        return True, "no problems"
    else:
        return False, f"problem_items{problem_info}"
