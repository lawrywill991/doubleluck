import sqlite3
import traceback

from config import get_db_path

def add_login_succes_column():
    database=get_db_path()
    with sqlite3.connect(database) as con:
        query="ALTER TABLE user ADD COLUMN device TEXT;"
        cursor = con.cursor()
        cursor.execute(query)
        con.commit()
    return "表格user已加上欄位device"


def add_login_fail_table():
    database=get_db_path()
    with sqlite3.connect(database) as con:
        query="""CREATE TABLE IF NOT EXISTS login_fail(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT,
            fail_reason TEXT,
            device TEXT NOT NULL DEFAULT 'unknown',
            ip_address TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        cursor = con.cursor()
        cursor.execute(query)
        query2="CREATE INDEX IF NOT EXISTS idx_login_fail_ip ON login_fail(ip_address);"
        cursor.execute(query2)
        query3= "CREATE INDEX IF NOT EXISTS idx_login_fail_time ON login_fail(created_at);"
        cursor.execute(query3)
        con.commit()
    return "login_fail表格已新增"