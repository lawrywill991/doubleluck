import sqlite3
import traceback

from .SQLutils import check_phone
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