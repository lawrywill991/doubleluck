import sqlite3
from config import get_db_path


def add_expenditure_table() -> str:
    database = get_db_path()
    with sqlite3.connect(database) as con:
        cursor = con.cursor()
        query = """CREATE TABLE IF NOT EXISTS expenditure(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            category_id TEXT NOT NULL REFERENCES expenditure_categories(categories_id),
            unit_price REAL,
            unit TEXT,
            quantity REAL,
            amount INTEGER NOT NULL,
            
            create_by TEXT NOT NULL REFERENCES employee(employee_no),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );"""
        cursor.execute(query)
        con.commit()
    return "expenditure表格已新增"


def add_expenditure_category_table() -> str:
    database = get_db_path()
    with sqlite3.connect(database) as con:
        cursor = con.cursor()
        query = """CREATE TABLE IF NOT EXISTS expenditure_categories(
                id INTEGER PRIMARY KEY,
                categories_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                parent_id TEXT REFERENCES expenditure_categories(categories_id),
                available TEXT NOT NULL DEFAULT 'N' CHECK (available IN('Y','N')),
                authority TEXT,
                create_by TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""
        cursor.execute(query)
        con.commit()
    return "expenditure_categories表格已新增"


def add_account_table() -> str:
    database = get_db_path()
    with sqlite3.connect(database) as con:
        cursor = con.cursor()
        query = """CREATE TABLE IF NOT EXISTS account(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_name TEXT NOT NULL,
        account TEXT,
        amount INTEGER NOT NULL,
        available TEXT NOT NULL DEFAULT 'Y' CHECK(available IN('Y','N')),
        last_updater TEXT NOT NULL,
        last_update_date DATETIME        
        );"""
        cursor.execute(query)
        con.commit()
    return "account表格已新增"


def add_account_trigger1(table="account"):
    database = get_db_path()
    with sqlite3.connect(database) as con:
        cursor = con.cursor()
        query = f"""CREATE TRIGGER trg_account_update_check
            BEFORE UPDATE OF amount ON {table}
            FOR EACH ROW
            WHEN NEW.amount != OLD.amount
            BEGIN
                SELECT
                    CASE
                        WHEN NEW.last_update_date IS OLD.last_update_date
                        THEN RAISE(ABORT, 'amount update requires last_updater and last_update_date')
                    END;
                END;"""
        cursor.execute(query)
        con.commit()
    return f"{table}表格的Trigger: trg_account_update_check 建立成功"


def add_account_trigger2(table="account"):
    database = get_db_path()
    with sqlite3.connect(database) as con:
        cursor = con.cursor()
        query = f"""CREATE TRIGGER IF NOT EXISTS trg_account_updater_check
            BEFORE UPDATE OF amount ON {table}
            FOR EACH ROW
            WHEN NEW.amount != OLD.amount
            BEGIN
                SELECT
                    CASE
                        WHEN NEW.last_updater != 'admin'
                        AND NOT EXISTS (
                            SELECT 1
                            FROM employee
                            WHERE employee_id = NEW.last_updater
                            )
                        THEN RAISE(ABORT, 'Invalid last_updater')
                     END;
                END;"""
        cursor.execute(query)
        con.commit()
    return f"{table}表格的Trigger: trg_account_updater_check 建立成功"


def add_transations_table():
    pass
