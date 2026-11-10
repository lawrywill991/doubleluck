import sqlite3
import traceback

from config import get_db_path

database=get_db_path()

def alter_weight_column(): 
    """寫order的時候一直要用斤數轉換，乾脆Alter建在product表格裡面，之後好拿出來給df.map()用
    """
    with sqlite3.connect(database) as con:
        cursor=con.cursor()
        sql1 = "ALTER TABLE products ADD COLUMN 'unit_weight' REAL;"
        cursor.execute(sql1)
        con.commit()
    return "表格products已加上欄位unit_weight"