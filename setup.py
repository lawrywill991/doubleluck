import os
import sys
import secrets
import sqlite3
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from SQLmaintain import database_manager,UserTableCRUD,EmployeeTableCRUD,WorkingTimeTableCRUD,ProductsTableCRUD

BASE_DIR = Path(__file__).resolve().parent
DISK_PATH = os.getenv("PERSISTENT_DISK_PATH") 
print(DISK_PATH)
if DISK_PATH:
    DB_PATH_ABS = os.path.join(DISK_PATH, "doubleLuck.db") #雲端付費方案路徑
else:
    DB_PATH_ABS = os.path.join(BASE_DIR, "doubleLuck.db") # 本地開發路徑

if DISK_PATH:
    EXCEL_PATH_ABS = os.path.join(DISK_PATH, "schema.xlsx") 
else:
    EXCEL_PATH_ABS = os.path.join(BASE_DIR, "schema.xlsx")

ENV_FILE = ".env"
REQUIRED_ENV = ["FLASK_SECRET_KEY","DB_PATH"]
REQUIRED_TABLE=["user","employee","work_time","products","validation"]
REQUIRED_TRIGGER=["prevent_time_overlap","employee_quick"]

class checks:
    @staticmethod
    def check_env():
        """檢查 .env 是否存在"""
        if os.path.exists(ENV_FILE):
            return True
        return False
    @staticmethod
    def read_env():
        """讀取 .env，回傳 dict"""

        env = {}

        with open(ENV_FILE, "r", encoding="utf-8") as f:

            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()

        return env

    @staticmethod
    def check_db_file():
        """檢查 DB_FILE是否存在"""
        if os.path.exists(DB_PATH_ABS):
            return True
        return False

    
    @staticmethod
    def check_env_items(env):
        key_missing = []
        value_missing=[]
        for item in REQUIRED_ENV:
            if item not in env:
                key_missing.append(item)
            elif env[item] == "":
                value_missing.append(item)
        return key_missing,value_missing


    @staticmethod
    def check_tables():
        tables=database_manager.check_tables(database=DB_PATH_ABS)
        exist_tables=[]
        missing_tables=[]
        for table in REQUIRED_TABLE:
            if table in tables:
                exist_tables.append(table)
            else:
                missing_tables.append(table)
        return exist_tables,missing_tables

    @staticmethod
    def check_triggers():
        triggers=database_manager.check_trigger()

        exist_triggers=[]
        missing_triggers=[]
        for trigger in REQUIRED_TRIGGER:
            if trigger in triggers:
                exist_triggers.append(trigger)
            else:
                missing_triggers.append(trigger)
        return exist_triggers,missing_triggers
    @staticmethod
    def check_empty_tables():
        tables={"user":UserTableCRUD.read_user_table(),
        "employee":EmployeeTableCRUD.read_employee_table()[1],
        "validation":UserTableCRUD.validation_infomations(),
        "products":ProductsTableCRUD.read_products_table()[1]}

        return [table_name for table_name,data in tables.items() if not data]
        # for name, data in tables.items():
        #     print(name, type(data), data)
        # return "測試中" 
    @staticmethod
    def final_check():
        pass_steps={}
        if checks.check_env() and  not checks.check_env_items(checks.read_env())[1]:
            pass_steps.update({"env_check":True})
        else:
            pass_steps.update({"env_check":False})
        if checks.check_db_file() and not checks.check_tables()[1]:
            pass_steps.update({"db_check":True})
        else:
            pass_steps.update({"db_check":False})
        if  not checks.check_empty_tables():
            pass_steps.update({"table_check":True})
        else:
            pass_steps.update({"table_check":False})
        return pass_steps



class initializations:
    @staticmethod
    def complete_env(existing_env:dict,key_missing:list,value_missing:list):
        for item in value_missing:
                if item == "FLASK_SECRET_KEY":
                    existing_env.update({"FLASK_SECRET_KEY":secrets.token_hex(32)})
                elif item == "DB_PATH":
                    existing_env.update({"DB_PATH":DB_PATH_ABS})
        for item in key_missing:
                if item == "FLASK_SECRET_KEY":
                    existing_env.update({"FLASK_SECRET_KEY":secrets.token_hex(32)})
                elif item == "DB_PATH":
                    existing_env.update({"DB_PATH":DB_PATH_ABS})
        return existing_env

    @staticmethod
    def envdict_to_envequal(env:dict):
        env_setting=""
        for item in env:
            env_setting=env_setting + item + "=" + env[item]+"\n"
        return env_setting
    @staticmethod
    def complete_tables(missing_tables:list):
        for table in missing_tables:
            if table=="user":
                UserTableCRUD.create_user_table()
            if table=="employee":
                EmployeeTableCRUD.create_enployee_table()
            if table=="work_time":
                WorkingTimeTableCRUD.create_work_time_table()
            if table=="products":
                ProductsTableCRUD.create_product_table()
            if table=="validation":
                # key=input("請輸入身分驗證問題:")
                # value=input("請輸入身分驗證答案")
                UserTableCRUD.validation_table_build()

    @staticmethod
    def complete_triggers(missing_trigger:list):
        for trigger in missing_trigger:
            if trigger == "prevent_time_overlap":
                WorkingTimeTableCRUD.create_time_trigger()
            if trigger == "employee_quick":
                EmployeeTableCRUD.create_status_trigger()

    @staticmethod
    def create_basic_employee_data():
        employee_name = input("請輸入員工姓名:\n")
        employee_no = input("請輸入員工編號:\n")
        employee_role = input("請輸入員工職位:\n")
        insert_result, message = EmployeeTableCRUD.insert_employee(
                        employee_no, employee_name, employee_role
                    )
        # print(insert_result)
        print(message)
    @staticmethod
    def create_basic_user_data():
        user_name = input("請輸入使用者名稱:\n")
        employee_no = input("請輸入使用者員工編號: \n")
        account = input("請輸入帳號:\n")
        password = input("請輸入密碼:\n")
        email = input("請輸入email: \n")
        insert_result = UserTableCRUD.insert_user(
                        user_name, employee_no, account, password, email)
        print(insert_result)

    @staticmethod
    def create_basic_validation_data():
        validation_key=input("請輸入驗證問題:\n")
        validation_value=input("請輸入驗證答案:\n")
        message=UserTableCRUD.validation_data_build(validation_key,validation_value)
        print(message)

    @staticmethod
    def create_basic_products():
        product_name = input("請輸入產品名稱\n")
        spec = input("請輸入產品規格\n")
        price = int(input("請輸入建議售價\n"))
        product_code = input("請輸入產品代號\n")
        message = ProductsTableCRUD.insert_product(
                    product_name, spec, price, product_code)
        print(message)

def lazy_process(Excel_PATH_ABS):
    user_table=pd.read_excel(Excel_PATH_ABS,sheet_name="使用帳號表",engine="openpyxl")
    employee_table=pd.read_excel(Excel_PATH_ABS,sheet_name="員工表",engine="openpyxl")
    product_table=pd.read_excel(Excel_PATH_ABS,sheet_name="產品表",engine="openpyxl")
    with sqlite3.connect(DB_PATH_ABS) as con:
        employee_table.to_sql("employee",con=con,index=False ,if_exists="delete_rows")
        product_table.to_sql("products",con=con,index=False ,if_exists="delete_rows")
        con.commit()

    required = ["user_name","employee_no","account","password","email"]
    user_table = user_table.dropna(subset=required)

    for idx, row in user_table.iterrows():
        user_create_result=UserTableCRUD.insert_user(row["user_name"],row["employee_no"],row["account"],row["password"],row["email"])
        print(user_create_result)


def main():
    print("【Step 1】檢查 .env ...")
    time.sleep(1)
    if not checks.check_env():
        print("✗ 找不到 .env")
        print("\n開始建立 .env")
        env_dict={key:"" for key in REQUIRED_ENV}
        key_missing,value_missing=checks.check_env_items(env_dict)
        completed_env=initializations.complete_env(env_dict,key_missing,value_missing)
        completed_env=initializations.envdict_to_envequal(completed_env)
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write(completed_env)
        print("✓ .env 建立完成")
    else:
        print("✓ 找到 .env")
        print("檢查.env中是否必要有必要資訊")
        time.sleep(1)
        exist_env=checks.read_env()
        key_missing,value_missing= checks.check_env_items(exist_env)
        if key_missing or value_missing:
            completed_env=initializations.complete_env(exist_env,key_missing,value_missing)
            completed_env=initializations.envdict_to_envequal(completed_env)
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(completed_env)
            print("缺少資料已補上")
        else:
            print("檢查必要資訊均已建立")
    print("\nStep 1 完成")
    load_dotenv(".env")
    print("【Step 2】檢查 db_file 是否存在...")


    time.sleep(1)
    if checks.check_db_file():
        print(f"✓ 找到 好勢成雙的DB_FILE")
    else:
        print("✗ 找不到 db_file")
        with sqlite3.connect(DB_PATH_ABS) as con:
            con.commit()
        print(f"✓ 好勢成雙DB_FILE 建立完成")
    print("\nStep 2 完成")
    print("【Step 3】檢查 必要資料表是否存在...")
    time.sleep(1)
    exist_table,missing_table=checks.check_tables()
    if missing_table:
        print(f"資料表有缺少:{missing_table}")
        initializations.complete_tables(missing_table)
        print("缺少的資料表已建立")
    else:
        print("必要資料表均已存在")
    print("\nStep 3 完成")
    print("【Step 4】檢查 必要trigger是否存在...")
    time.sleep(1)
    exist_triggers,missing_trigger=checks.check_triggers()
    if missing_trigger:
        print(f"trigger有缺少:{missing_trigger}")
        initializations.complete_triggers(missing_trigger)
        print("缺少的trigger已建立")
    else:
        print("必要的trigger已建立")
    print("\nStep 4 完成")
    print("【Step 5】檢查是否必要資料表是否為空...")
    time.sleep(1)
    empty_tables=checks.check_empty_tables()
    print(empty_tables)

    print(all(x in empty_tables for x in ["user","employee","products"]))

    if all( x in empty_tables for x in ["user","employee","products"]) and EXCEL_PATH_ABS:
        print("主要資料表均為空")
        choice=input("找到初始化Excel,是否匯入  Y/N \n").upper()
        if choice == "Y":
            lazy_process(EXCEL_PATH_ABS)
            empty_tables.remove("user")
            empty_tables.remove("employee")
            empty_tables.remove("products")

    if empty_tables:
        while "employee" in empty_tables:
            initializations.create_basic_employee_data()
            choice=input("繼續輸入? Y/N \n").upper()
            if choice == "N":
                break
        while "user" in empty_tables:
            initializations.create_basic_user_data()
            choice=input("繼續輸入? Y/N \n").upper()
            if choice == "N":
                break
        while "validation" in empty_tables:
            initializations.create_basic_validation_data()
            break
        while "product" in empty_tables:
            initializations.create_basic_products()
            choice=input("繼續輸入? Y/N \n").upper()
            if choice == "N":
                break
    else:
        print("必要的資料表均非空資料表")
    print("\nStep 5 完成")
    print("\n 基本設定均已完成，測試檢查開始")
    time.sleep(1)
    if all(checks.final_check().values()):
        if os.path.exists(EXCEL_PATH_ABS):
            choice=input("測試通過，是否刪除初始設定xlsx檔 Y/N \n").upper()
            if choice=="Y":
                os.remove(EXCEL_PATH_ABS)
                print(f"{EXCEL_PATH_ABS}已刪除")
            else:
                print(f"{EXCEL_PATH_ABS}保留")
        print("測試通過，可開始使用本系統")
        
    else:
        print("測試失敗，請重新開始本setup程序")
        sys.exit(0)


if __name__=="__main__":

    main()