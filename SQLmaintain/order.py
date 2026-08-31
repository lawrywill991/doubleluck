import sqlite3
import traceback
from typing import Any
# from datetime import date

from .SQLutils import check_phone,check_internal_id_format
from config import get_db_path



class CustomerTableCRUD:
    @staticmethod
    def create_customer_table():
        database=get_db_path()
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
        database=get_db_path()
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
    def read_customer_table(customer_id=None,customer_name=None):
        if customer_id is not None or customer_name is not None:
            column_dict={"customer_id":customer_id,"customer_name":customer_name,}
            data_dict={k:v for k,v in column_dict.items() if v is not None}
            data_keys=list(data_dict.keys())
            # print(data_keys)
            condition_columns=[]
            for key in data_keys:
                key += "=?"
                condition_columns.append(key)
            condition_statement=" AND ".join(condition_columns)
            values=list(data_dict.values())

            sql = f"""SELECT * FROM customers WHERE {condition_statement}"""

            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(sql, tuple(values))
                customers = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                customers_data = [dict(zip(columns, row)) for row in customers]
                return customers_data
        else:
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = "SELECT * FROM customers"
                cursor.execute(query)
                customers = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                customers_data = [dict(zip(columns, row)) for row in customers]
                return customers_data

    @staticmethod
    def customer_fuzzy_search(customer_name)->list[dict]:
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor=con.cursor()
            query="SELECT * FROM customers WHERE customer_name LIKE ?"
            data =(f"%{customer_name}%",)
            cursor.execute(query,data)
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
            check_result,customer_phone,_= check_phone(customer_phone)           
            if not check_result:
                return False, "輸入電話號碼格式不正確"
            if payment_method not in ["Cash", "Transfer"]:
                return False, "付款只有現金與匯款方式"
            if payment_method == "Transfer" and transfer_account is None:
                return False, "轉帳客戶請輸入預計匯款帳戶"
            
            column_dict={"customer_name":customer_name,
                       "customer_phone":customer_phone,
                       "customer_address":customer_address,
                       "payment_method":payment_method,
                       "transfer_account":transfer_account,
                       "note":note,
                       "create_by":create_by}
            required_column=["customer_name","customer_phone","customer_address","payment_method","create_by"]
            data_dict={k:v for k,v in column_dict.items() if k in required_column or v is not None}
            # print(data_dict)
            columns = ", ".join(data_dict.keys())
            placeholders = ", ".join("?" * len(data_dict))

            sql = f"""INSERT INTO customers ({columns}) VALUES ({placeholders})"""
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(sql, tuple(data_dict.values()))
                con.commit()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = (
                    f"SELECT customer_id FROM customers WHERE customer_name=?"
                )
                data = (customer_name,)
                cursor.execute(query, data)
                customer_id = cursor.fetchone()
            # customer_id = "測試ID"
            return (
                True,
                f"客戶{customer_name}資料建立成功，客戶編號為{customer_id}",
            )
        except sqlite3.IntegrityError as e:
            if 'UNIQUE' in str(e):
                return False, f"已有此客戶名稱{customer_name}"
            else:
                traceback.print_exc()
                return False, f"發生錯誤:{e}"  
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"
    @staticmethod
    def delete_customer(id):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "DELETE FROM customers WHERE id=?"
            data = (id,)
            cursor.execute(query, data)
            con.commit()
        return f"已從customers表格中刪除{id}紀錄"
    @staticmethod
    def read_customer_for_flask(customer_name):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor=con.cursor()
            query="SELECT * FROM customers WHRER custmoer_name=?"
            data=(customer_name,)
            cursor.execute(query,data)
            customer_info=cursor.fetchall()
        if customer_info is None:
            return False,f"資料庫中查無客戶名稱{customer_name}"
        elif len(customer_info)>1:
            columns = [col[0] for col in cursor.description]
            customer_data = [dict(zip(columns, row)) for row in customer_info]
            customer_data[0].pop('id')
            customer_data[0].pop('create_by')
            return False,customer_info
        else:
            columns = [col[0] for col in cursor.description]
            customer_data = [dict(zip(columns, row)) for row in customer_info]
            customer_data[0].pop('id')
            customer_data[0].pop('create_by')
            # customer_data[0].pop('created_at')
            return True,customer_info

    @staticmethod
    def update_customer(customer_id,column,new_data):
        columns=['customer_name','customer_phone','customer_address','customer_level','payment_method','transfer_account','notes']
        try:
            customer_data=CustomerTableCRUD.read_customer_table(customer_id=customer_id)
            if not customer_data:
                return False,f"找不到客戶編號為{customer_id}的資料"
            
            if column in columns:
                database=get_db_path()
                with sqlite3.connect(database) as con:
                    cursor = con.cursor()
                    query = (
                        f"UPDATE customers SET {column}=? WHERE customer_id=?"
                    )
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
    def create_order_table():
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = """CREATE TABLE orders (
                    id INTEGER PRIMARY KEY,
                    order_id TEXT UNIQUE,
                    product_code TEXT NOT NULL REFERENCES products(product_code),
                    product_name TEXT NOT NULL,
                    spec TEXT NOT NULL,
                    qty INTEGER NOT NULL CHECK(qty >=1),
                    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
                    subtotal INTEGER NOT NULL,
                    shipment_fee INTEGER NOT NULL,
                    ship_date_requested DATETIME,

                    receiver_name TEXT NOT NULL,
                    receiver_phone TEXT NOT NULL CHECK (
                    receiver_phone GLOB '09[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]' 
                    OR receiver_phone GLOB '0[2-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
                    OR receiver_phone GLOB '0[2-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
                    receiver_address TEXT NOT NULL ,
                                        
                    payment_method TEXT CHECK (payment_method IN ('Cash','Transfer')),
                    transfer_account TEXT,
                    order_notes TEXT,
                    status TEXT CHECK (status IN ("not_shipped","not_paid","order_canceled","complete","bad debt")) DEFAULT 'not_shipped',
                    shipment_date DATETIME,
                    payment_reciving_date DATETIME,
                    create_by TEXT NOT NULL REFERENCES employee(employee_no),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );"""
            cursor.execute(query)
            con.commit()

    @staticmethod
    def create_order_trigger(table="orders")->str:
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f"""CREATE TRIGGER trg_order_id
            AFTER INSERT ON {table}
            FOR EACH ROW
            BEGIN
                UPDATE orders
                SET order_id =
                printf('On') ||
                substr(strftime('%Y', NEW.created_at), 3, 2) || '-' ||
                printf('%04d', NEW.id)
                WHERE id = NEW.id;
            END;"""
            cursor.execute(query)
            con.commit()
        return f"{table}表格的Trigger: trg_order_id 建立成功"


    @staticmethod
    def read_order_table(order_id=None,receiver_name=None,status=None)->list[dict[Any,Any]]:
        status_list=["not_shipped","not_paid","order_canceled","complete","bad debt"] #應該要把檢查的段落放在db_admin與flask那裏

        if order_id is not None or receiver_name is not None or status is not None:
            if status not in [status_list,None]: #應該要把檢查的段落放在db_admin與flask那裏
                return [{"read result":"wrong status"}]#應該要把檢查的段落放在db_admin與flask那裏
            column_dict={"order_id":order_id,"receiver_name":receiver_name,"status":status}
            data_dict={k:v for k,v in column_dict.items() if v is not None}
            data_keys=list(data_dict.keys())
            # print(data_keys)
            condition_columns=[]
            for key in data_keys:
                key += "=?"
                condition_columns.append(key)
            condition_statement=" AND ".join(condition_columns)
            values=list(data_dict.values())

            sql = f"""SELECT * FROM orders WHERE {condition_statement}"""

            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(sql, tuple(values))
                customers = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                customers_data = [dict(zip(columns, row)) for row in customers]
                return customers_data

        else:
            sql= """SELECT * FROM orders"""
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(sql,)
                customers = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                customers_data = [dict(zip(columns, row)) for row in customers]
                return customers_data

    @staticmethod
    def read_order_for_flask(create_by,order_id=None,reciver_name=None,status="not_shipped"):#沒權限分級前，這個設計給flask只讀create是自己的
        pass

    @staticmethod
    def order_fuzzy_search(receiver_name)->list[dict]:
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor=con.cursor()
            query="SELECT * FROM orders WHERE receiver_name LIKE ?"
            data =(f"%{receiver_name}%",)
            cursor.execute(query,data)
            customers = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            customers_data = [dict(zip(columns, row)) for row in customers]
            return customers_data

    @staticmethod
    def insert_order_table(product_code,product_name,spec,qty,customer_id,subtotal,shipment_fee,receiver_name,receiver_phone,receiver_address,create_by,payment_method="Cash",transfer_account=None,order_notes=None)->tuple[bool,str]:
        try:
            check_result,reciver_phone,_= check_phone(receiver_phone)           
            if not check_result:
                return False, "輸入電話號碼格式不正確"
            if payment_method not in ["Cash", "Transfer"]:
                return False, "付款只有現金與匯款方式"
            if payment_method == "Transfer" and transfer_account is None:
                return False, "轉帳客戶請輸入預計匯款帳戶"
            if  (not isinstance(qty,int)) or (not isinstance(subtotal,int)) or (not isinstance(shipment_fee,int)):
                return False,"輸入的數量、貨款、運費並非數字"
                    
            column_dict={"product_code":product_code,
                         "product_name":product_name,
                         "spec":spec,
                         "qty":qty,
                         "customer_id":customer_id,
                         "subtotal":subtotal,
                         "shipment_fee":shipment_fee,
                         "receiver_name":receiver_name,
                         "receiver_phone":receiver_phone,
                         "receiver_address":receiver_address,
                         "payment_method":payment_method,
                         "transfer_account":transfer_account,
                         "order_notes":order_notes,
                         "create_by":create_by}
            required_column=["product_code","product_name","spec","qty","customer_id","subtotal","shipment_fee","receiver_name","receiver_phone","receiver_address","create_by"]
            data_dict={k:v for k,v in column_dict.items() if k in required_column or v is not None}
                    # print(data_dict)
            columns = ", ".join(data_dict.keys())
            placeholders = ", ".join("?" * len(data_dict))
        
            sql = f"""INSERT INTO orders ({columns}) VALUES ({placeholders})"""
            database=get_db_path()
            with sqlite3.connect(database) as con:
                con.execute("PRAGMA foreign_keys = ON;")
                cursor = con.cursor()
                cursor.execute(sql, tuple(data_dict.values()))
                con.commit()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = (
                        f"SELECT order_id FROM orders WHERE receiver_name=? AND customer_id=?"
                        )
                data = (receiver_name,customer_id)
                cursor.execute(query, data)
                order_id = cursor.fetchone()[0]
            return (
                True,
                f"客戶編號{customer_id}的訂單建立成功，收件人資料:{receiver_name}；訂單編號為:{order_id}",
            )
        except sqlite3.IntegrityError as e:
            if 'UNIQUE' in str(e):
                # return False, f"已有此客戶名稱{customer_name}"
                return False,"應該不會出現UNIQUE錯誤才對"
            else:
                traceback.print_exc()
                return False, f"發生錯誤:{e}"  
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"
        # 

    @staticmethod
    def update_order(order_id,column,old_data,new_data):
        columns=["product_code","product_name","spec","qty","subtotal","shipment_fee","ship_date_requested","receiver_name","receiver_phone","receiver_address","payment_method","transfer_account","order_notes"]
        pass

    @staticmethod
    def order_shipping(order_id,shipment_date)->str: #出貨確認
        try:
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor=con.cursor()
                query="UPDATE orders SET status=? , shipment_date=? WHERE order_id=?"
                data=("not_paid",shipment_date,order_id)
                cursor.execute(query,data)
                con.commit()
            return f"{order_id}訂單狀態已更新至<等待收款中>"
        except Exception as e:
            traceback.print_exc()
            return f"發生未預期錯誤{e}"

    @staticmethod
    def order_complete(order_id,payment_reciving_date,payment_method="Cash",transfer_account=None)->str: #收款確認
        # payment_methods=[{"mayment_method":"Cash","transfer_account":None},{"mayment_method":"Transfer","transfer_account":transfer_account}]
        if payment_method not in ["Cash","Transfer"]:
            return "收款方式只有現金與轉帳"
        try:
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor=con.cursor()
                query="UPDATE orders SET status=? , payment_reciving_date=? ,payment_method=? , transfer_account=? WHERE order_id=?"
                data=("complete",payment_reciving_date,payment_method,transfer_account,order_id)
                cursor.execute(query,data)
                con.commit()
            return f"{order_id}訂單狀態已更新至<收款確認，結案>"
        except Exception as e:
            traceback.print_exc()
            return f"發生未預期的錯誤{e}"

    @staticmethod
    def order_cancel(order_id)->str:
        try:
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor=con.cursor()
                query="UPDATE orders SET status=? WHERE order_id=?"
                data=("order_canceled",order_id)
                cursor.execute(query,data)
                con.commit()
            return f"{order_id}訂單狀態已更新至<訂單取消>"
        except Exception as e:
            traceback.print_exc()
            return f"發生未預期的錯誤{e}"


    @staticmethod
    def delete_order(id)->str:
        bool,internal_id,id_type=check_internal_id_format(id)
        print(id_type)
        if bool and id_type == "order_id":
            query = "DELETE FROM orders WHERE order_id=?"
            data=(internal_id,)    
        elif not bool and internal_id is None:
            query = "DELETE FROM orders WHERE id=?"
            data=(id,)
        else:
            return "輸入id不合法，未進行刪除"
        try:
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(query, data)
                con.commit()
            return f"已從orders表格中刪除{id}的紀錄"
        except Exception as e:
            traceback.print_exc()
            return f"發生未預期的錯誤{e}"