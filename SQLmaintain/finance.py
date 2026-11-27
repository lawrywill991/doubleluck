import sqlite3
import traceback
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from config import get_db_path


class ExpenditureCRUD:
    @staticmethod
    def insert_expenditure(
        expense_date,
        item,
        category_id,
        amount: int,
        account_id,
        create_by,
        unit_price=None,
        unit=None,
        quantity=None,
        details=None,
        other_description=None,
    ) -> tuple[bool, str]:
        database = get_db_path()
        try:
            # 日期格式不對會丟出 ValueError；順便補零成 YYYY-MM-DD
            expense_date = datetime.strptime(expense_date, "%Y-%m-%d").strftime(
                "%Y-%m-%d"
            )
        except ValueError:
            return False, "支出日期格式須為YYYY-MM-DD"
        if amount <= 0:
            return False, "支出金額需大於0"
        try:
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                if create_by != "admin":
                    query = "SELECT 1 FROM employee WHERE employee_no=?"
                    cursor.execute(query, (create_by,))
                    if cursor.fetchone() is None:
                        return False, f"找不到員工編號{create_by}"

                query = (
                    "SELECT available FROM expenditure_categories "
                    "WHERE categories_id=?"
                )
                cursor.execute(query, (category_id,))
                category = cursor.fetchone()
                if category is None:
                    return False, f"找不到類別編號{category_id}"
                if category[0] != "Y":
                    return False, f"類別{category_id}未啟用，無法新增支出"

                query = "SELECT available FROM account WHERE id=?"
                cursor.execute(query, (account_id,))
                account = cursor.fetchone()
                if account is None:
                    return False, f"找不到帳戶{account_id}"
                if account[0] != "Y":
                    return False, f"帳戶{account_id}未啟用，無法新增支出"

                # 只新增紀錄，confirmed 用預設值 N；確認後才扣帳戶餘額
                query = """INSERT INTO expenditure
                    (expense_date, item, category_id, unit_price, unit, quantity,
                    amount, account_id, details, other_description, create_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                data = (
                    expense_date,
                    item,
                    category_id,
                    unit_price,
                    unit,
                    quantity,
                    amount,
                    account_id,
                    details,
                    other_description,
                    create_by,
                )
                cursor.execute(query, data)
                new_id = cursor.lastrowid
                con.commit()
            return True, f"支出{item}新增成功，紀錄編號為{new_id}，尚未扣款"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def confirm_expenditure(id, confirmed_by) -> tuple[bool, str]:
        database = get_db_path()
        date_time = datetime.now(ZoneInfo("Asia/Taipei")).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        try:
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                # 先鎖住資料庫，避免兩個人同時確認而扣兩次
                cursor.execute("BEGIN IMMEDIATE")
                # 確認權限暫定為任何有效員工，日後再改為特定員工
                if confirmed_by != "admin":
                    query = "SELECT 1 FROM employee WHERE employee_no=?"
                    cursor.execute(query, (confirmed_by,))
                    if cursor.fetchone() is None:
                        return False, f"找不到員工編號{confirmed_by}"

                query = (
                    "SELECT amount, account_id, confirmed "
                    "FROM expenditure WHERE id=?"
                )
                cursor.execute(query, (id,))
                expenditure = cursor.fetchone()
                if expenditure is None:
                    return False, f"找不到支出紀錄{id}"
                amount, account_id, confirmed = expenditure
                if confirmed == "Y":
                    return False, f"支出紀錄{id}已確認過，不可重複扣款"

                query = "SELECT amount, available FROM account WHERE id=?"
                cursor.execute(query, (account_id,))
                account = cursor.fetchone()
                if account is None:
                    return False, f"找不到帳戶{account_id}"
                balance, available = account
                if available != "Y":
                    return False, f"帳戶{account_id}未啟用，無法扣款"
                new_balance = balance - amount

                # 扣款和標記確認在同一個交易，任一步失敗就一起取消
                query = """UPDATE account
                    SET amount=?, last_updater=?, last_update_date=?
                    WHERE id=?"""
                cursor.execute(
                    query, (new_balance, confirmed_by, date_time, account_id)
                )
                query = """UPDATE expenditure
                    SET confirmed='Y', confirmed_by=?, confirmed_at=?
                    WHERE id=?"""
                cursor.execute(query, (confirmed_by, date_time, id))
                con.commit()
            return True, f"支出紀錄{id}已確認扣款，帳戶餘額{new_balance}"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def delete_expenditure(id) -> tuple[bool, str]:
        database = get_db_path()
        try:
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                # 只刪未確認的紀錄；條件寫在 DELETE 裡，避免刪除前剛好被確認
                query = "DELETE FROM expenditure WHERE id=? AND confirmed='N'"
                cursor.execute(query, (id,))
                if cursor.rowcount == 0:
                    query = "SELECT 1 FROM expenditure WHERE id=?"
                    cursor.execute(query, (id,))
                    if cursor.fetchone() is None:
                        return False, f"找不到支出紀錄{id}"
                    return False, f"支出紀錄{id}已確認扣款，無法刪除"
                con.commit()
            return True, f"已刪除支出紀錄{id}"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def delete_expenditure2(id) -> tuple[bool, str]:
        # 測試專用：已確認扣款的紀錄也會刪除，帳戶餘額不會退回
        database = get_db_path()
        try:
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = "DELETE FROM expenditure WHERE id=?"
                cursor.execute(query, (id,))
                if cursor.rowcount == 0:
                    return False, f"找不到支出紀錄{id}"
                con.commit()
            return True, f"已刪除支出紀錄{id}(測試用，餘額未退回)"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def delete_expenditure_category(category_id) -> tuple[bool, str]:
        database = get_db_path()
        try:
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                # 還有子類別時不可刪，避免子類別找不到上層
                query = "SELECT 1 FROM expenditure_categories WHERE parent_id=?"
                cursor.execute(query, (category_id,))
                if cursor.fetchone() is not None:
                    return False, f"類別{category_id}底下還有子類別，無法刪除"

                # 已有支出紀錄時不可刪，避免舊帳查不到類別
                query = "SELECT 1 FROM expenditure WHERE category_id=?"
                cursor.execute(query, (category_id,))
                if cursor.fetchone() is not None:
                    return False, f"類別{category_id}已有支出紀錄，無法刪除"

                query = "DELETE FROM expenditure_categories WHERE categories_id=?"
                cursor.execute(query, (category_id,))
                if cursor.rowcount == 0:
                    return False, f"找不到類別編號{category_id}"
                con.commit()
            return True, f"已刪除支出類別{category_id}"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def update_category_available(category_id, available: bool) -> tuple[bool, str]:
        database = get_db_path()
        available_flag = "Y" if available else "N"
        status = "啟用" if available else "停用"
        try:
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = (
                    "SELECT parent_id FROM expenditure_categories "
                    "WHERE categories_id=?"
                )
                cursor.execute(query, (category_id,))
                category = cursor.fetchone()
                if category is None:
                    return False, f"找不到類別編號{category_id}"
                # 根層類別(沒有上層)不可停用，只能停用下層類別
                if not available and category[0] is None:
                    return False, f"類別{category_id}是根層類別，不能停用"

                query = (
                    "UPDATE expenditure_categories SET available=? "
                    "WHERE categories_id=?"
                )
                cursor.execute(query, (available_flag, category_id))
                con.commit()
            return True, f"已將支出類別{category_id}{status}"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def insert_expenditure_category(
        categories_id,
        name,
        create_by,
        parent_id=None,
        available=False,
        authority=None,
    ) -> tuple[bool, str]:
        database = get_db_path()
        available_flag = "Y" if available else "N"
        try:
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                # SQLite 預設不檢查外鍵，所以自己確認上層類別存在
                if parent_id is not None:
                    query = "SELECT 1 FROM expenditure_categories WHERE categories_id=?"
                    cursor.execute(query, (parent_id,))
                    if cursor.fetchone() is None:
                        return False, f"找不到上層類別{parent_id}"

                # 同一上層類別下不可重名；用 IS 才能比對到 parent_id 為 NULL 的最上層
                query = (
                    "SELECT 1 FROM expenditure_categories "
                    "WHERE parent_id IS ? AND name=?"
                )
                cursor.execute(query, (parent_id, name))
                if cursor.fetchone() is not None:
                    return False, f"同一上層類別下已有名稱{name}"

                query = """INSERT INTO expenditure_categories
                    (categories_id, name, parent_id, available, authority, create_by)
                    VALUES (?, ?, ?, ?, ?, ?)"""
                data = (
                    categories_id,
                    name,
                    parent_id,
                    available_flag,
                    authority,
                    create_by,
                )
                cursor.execute(query, data)
                con.commit()
            return True, f"支出類別{name}建立成功，類別編號為{categories_id}"
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                return False, f"已有此類別編號{categories_id}"
            traceback.print_exc()
            return False, f"發生錯誤:{e}"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def read_expenditure_category() -> pd.DataFrame:
        database = get_db_path()
        with sqlite3.connect(database) as con:
            query = "SELECT * FROM expenditure_categories"
            df = pd.read_sql_query(query, con)
        return df


class AccountCRUD:
    @staticmethod
    def insert_account(
        account_name,
        updater,
        amount: int = 0,
        account=None,
        available=True,
    ) -> tuple[bool, str]:
        database = get_db_path()
        available_flag = "Y" if available else "N"
        date_time = datetime.now(ZoneInfo("Asia/Taipei")).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        try:
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                # 資料表的 trigger 只在更新金額時檢查人員，新增時自己檢查
                if updater != "admin":
                    query = "SELECT 1 FROM employee WHERE employee_no=?"
                    cursor.execute(query, (updater,))
                    if cursor.fetchone() is None:
                        return False, f"找不到員工編號{updater}"

                query = "SELECT 1 FROM account WHERE account_name=? AND account IS ?"
                cursor.execute(query, (account_name, account))
                if cursor.fetchone() is not None:
                    return False, f"已有此帳戶{account_name}"

                query = """INSERT INTO account
                    (account_name, account, amount, available,
                    last_updater, last_update_date)
                    VALUES (?, ?, ?, ?, ?, ?)"""
                data = (
                    account_name,
                    account,
                    amount,
                    available_flag,
                    updater,
                    date_time,
                )
                cursor.execute(query, data)
                con.commit()
            return True, f"帳戶{account_name}建立成功"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def read_account(account_name="cash", available=True) -> list[dict]:
        database = get_db_path()
        if available:
            account_availibility = "Y"
        else:
            account_availibility = "N"
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f"SELECT * FROM account WHERE account_name =? AND available = ?"
            data = (account_name, account_availibility)
            cursor.execute(query, data)
            account = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            account_data = [dict(zip(columns, row)) for row in account]
        return account_data

    @staticmethod
    def update_amount(id, amount: int, updater: str) -> tuple[bool, str]:
        database = get_db_path()
        date_time = datetime.now(ZoneInfo("Asia/Taipei")).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        try:
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                # 新餘額和舊餘額相同時 trigger 不會觸發，所以自己檢查人員
                if updater != "admin":
                    query = "SELECT 1 FROM employee WHERE employee_no=?"
                    cursor.execute(query, (updater,))
                    if cursor.fetchone() is None:
                        return False, f"找不到員工編號{updater}"

                query = "SELECT account_name, available FROM account WHERE id=?"
                cursor.execute(query, (id,))
                account = cursor.fetchone()
                if account is None:
                    return False, f"找不到帳戶{id}"
                account_name, available = account
                # 只有啟用中的帳戶可以更新
                if available != "Y":
                    return False, f"帳戶{account_name}未啟用，無法更新金額"

                query = """UPDATE account
                    SET amount=?, last_updater=?, last_update_date=?
                    WHERE id=?"""
                data = (amount, updater, date_time, id)
                cursor.execute(query, data)
                con.commit()
            return True, f"帳戶{account_name}餘額已更新為{amount}"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"
