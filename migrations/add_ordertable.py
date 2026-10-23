import sqlite3
import traceback

from config import get_db_path


def create_order_table():
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = """CREATE TABLE orders (
                    id INTEGER PRIMARY KEY,
                    order_id TEXT UNIQUE,
                    reserved TEXT NOT NULL CHECK(reserved IN('保留','排單')),
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
                    --一般手機
                    receiver_phone GLOB '09[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]' 
                    --一般9碼市話
                    OR receiver_phone GLOB '0[2-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
                    -- 一般10碼市話
                    OR receiver_phone GLOB '0[2-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
                    -- 一般9碼市話+分機
                    OR receiver_phone GLOB '0[2-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]#[0-9][0-9]*'
                    -- 一般10碼市話+分機
                    OR receiver_phone GLOB '0[2-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]#[0-9][0-9]*'),
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