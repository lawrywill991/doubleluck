import sqlite3

from .SQLutils import DataTransfer
from config import get_db_path


class ProductsTableCRUD:
    @staticmethod
    def create_product_table(database=None):
        if database is None:
            database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = """CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            product_code TEXT NOT NULL UNIQUE,
            product_name TEXT NOT NULL,
            spec TEXT NOT NULL,
            default_price INTEGER NOT NULL CHECK (default_price >=0),
            create_by TEXT DEFAULT 'admin',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );"""
            cursor.execute(query)
            con.commit()

    @staticmethod
    def insert_product(
        product_name, spec, price, product_code, create_by=None
    ):
        try:
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                if create_by is not None:
                    query = "INSERT INTO products (product_code,product_name,spec,default_price,create_by) VALUES (?,?,?,?,?)"
                    data = (product_code, product_name, spec, price, create_by)
                else:
                    query = "INSERT INTO products (product_code,product_name,spec,default_price) VALUES (?,?,?,?)"
                    data = (product_code, product_name, spec, price)
                cursor.execute(query, data)
                con.commit()
            return f"{product_name}:規格{spec}已創建成功"
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                return f"{product_code}已重複"
            else:
                return f"發生錯誤:{e}"
        except Exception as e:
            return f"發生錯誤:{e}"

    @staticmethod
    def read_products_table(product_name=None, spec=None):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            ## 其實更好是用動態寫法 conditions=[] data=[] + append() 然後 query += " WHERE " + " OR ".join(where) 但稍微難讀。
            if product_name != None and spec != None:
                query = (
                    "SELECT * FROM products WHERE product_name = ? and spec =?"
                )
                data = (product_name, spec)
                cursor.execute(query, data)
            elif product_name != None:
                query = "SELECT * FROM products WHERE product_name = ?"
                data = (product_name,)
                cursor.execute(query, data)
            elif spec != None:
                query = "SELECT * FROM products WHERE spec=?"
                data = (spec,)
                cursor.execute(query, data)
            else:
                query = "SELECT * FROM products"
                cursor.execute(query)
            products = cursor.fetchall()
            if products is None:
                return False, []
            else:
                columns = [col[0] for col in cursor.description]
                products_data = [dict(zip(columns, row)) for row in products]
                return True, products_data

    @staticmethod
    def read_products_for_flask(product_class="pomelo"):
        product_classes=["pomelo","freight"]
        if product_class not in product_classes:
            raise ValueError("目前產品只有文旦、運費")
        else:
            database=get_db_path()
            with sqlite3.connect(database) as con:

                cursor=con.cursor()
                query = "SELECT * FROM products WHERE product_code LIKE ?"
                data=(product_class+"%",)
                cursor.execute(query,data)
                products=cursor.fetchall()
                if products is None:
                    raise ValueError(f"目前資料表沒有{product_class}類產品!")
                else:
                    columns = [col[0] for col in cursor.description]
                    products_data = [dict(zip(columns, row)) for row in products]
                    product_dicts = DataTransfer(products_data).to_product_dicts()
            return product_dicts

    @staticmethod
    def delete_product(id):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "DELETE FROM products WHERE id=?"
            data = (id,)
            cursor.execute(query, data)
            con.commit()
        return f"已從products表格中刪除{id}紀錄"