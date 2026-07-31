import re
import sqlite3
import string
import random

from config import get_db_path



class DataTransfer:  # 要回傳資料給前端時把read結果解析的方法集
    def __init__(self, data: list):
        self.data = data

    def get_keys(self):
        if self.data == []:
            raise ValueError("傳入的資料為空串列")
        keys = []
        for dict_list in self.data:
            for key in dict_list:
                if key not in keys:
                    keys.append(key)
        return keys

    def get_values(self, key="duration"):
        keys = self.get_keys()
        values = []
        if key in keys:
            for dicts in self.data:
                value = dicts[key]
                values.append(value)
            return values
        else:
            raise KeyError(f"{key} not found in {keys}")

    def get_all_value_series(self):
        keys = self.get_keys()
        key_value_series = []
        for key in keys:
            value_series = []
            for dicts in self.data:
                value = dicts[key]
                value_series.append(value)
            key_value_series.append(value_series)
        return key_value_series

    def get_duration_sum(self):
        duration = self.get_values("duration")
        try:
            int_duration = [int(round(x * 100)) for x in duration]
            return sum(int_duration) / 100
        except:
            invalid_item = next(
                x for x in duration if not isinstance(x, (int, float))
            )
            raise TypeError(f"{invalid_item} not a number")

    def to_worker_dicts(self, nick_name=True):
        employee_no = self.get_values(key="employee_no")
        employee_name = self.get_values(key="employee_name")
        if nick_name:
            worker_name = list(employee[-1] for employee in employee_name)
        else:
            worker_name = employee_name
        worker_dicts = dict(zip(employee_no, worker_name))
        return worker_dicts

    def to_product_dicts(self):
        for dict in self.data:
            dict.pop("id")
            dict.pop("create_by")
            dict.pop("created_at")
        return self.data

    def remove_information(self,information_keys=("id","crate_by","created_at")):
        for dicts in self.data:
            for key in information_keys:
                dicts.pop(key)
        return self.data
    
class database_manager:
    
    
    @staticmethod
    def check_tables(database=None):
        if database is None:
            database= get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = 'SELECT * FROM sqlite_master WHERE type="table" AND name != "sqlite_sequence"'
            cursor.execute(query)
            tables = cursor.fetchall()
            if tables:
                return [table[1] for table in tables]
            else:
                return []

    @staticmethod
    def delete_table(table_name):
        database= get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f"DROP TABLE IF EXISTS {table_name}   "
            cursor.execute(query)
            con.commit()
        return f"Table {table_name} has been deleted."

    @staticmethod
    def check_table_columns(table_name):
        database= get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f'SELECT * FROM pragma_table_info("{table_name}")'
            cursor.execute(query)
            columns = cursor.fetchall()
            if columns:
                return [column for column in columns]
            else:
                return f"Table {table_name} does not exist."

    @staticmethod
    def check_trigger():
        database= get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = """SELECT name, tbl_name FROM sqlite_schema WHERE type = 'trigger'"""
            cursor.execute(query)
            triggers=cursor.fetchall()

            if triggers:
                return [trigger[0] for trigger in triggers]
            else:
                return []
        # return triggers
    
    @staticmethod
    def drop_trigger(trigger_name):
        database= get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f"""DROP TRIGGER IF EXISTS {trigger_name}"""
            cursor.execute(query)
            con.commit()
        return f"Trigger: {trigger_name} 移除成功"




def check_phone(phone_no):
    if not isinstance(phone_no, str):
        return False,phone_no, f"傳入數值非文字格式"
    phone_no = re.sub(r"\D", "", phone_no)
    if re.fullmatch(r"09\d{8}", phone_no):
        return True, phone_no,"mobile phone"
    elif re.fullmatch(r"0\d{9}", phone_no):
        return True, phone_no, "local phone"
    elif re.fullmatch(r"0\d{8}", phone_no):
        return True, phone_no, "local phone(other)"
    else:
        return False,None, "not a phone number"

def generated_randompassword():
    aproved_alphabet=string.ascii_letters + string.digits
    generated_randompassword="".join(random.choices(aproved_alphabet,k=6))

    return generated_randompassword