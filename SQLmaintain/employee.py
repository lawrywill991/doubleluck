import sqlite3
import traceback
from datetime import datetime,timedelta

import werkzeug.security as secur
import bcrypt

from .SQLutils import DataTransfer
from config import get_db_path



class EmployeeTableCRUD:
    @staticmethod
    def create_enployee_table(database=None):
        if database is None:
            database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = """CREATE TABLE employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_no TEXT NOT NULL UNIQUE,
            employee_name TEXT NOT NULL,
            department TEXT REFERENCES role(department),
            status INTEGER DEFAULT 1,
            role TEXT REFERENCES role(role_name),
            phone TEXT,
            personal_email TEXT,
            create_by TEXT ,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );"""
            cursor.execute(query)
            con.commit()

    
    @staticmethod ##員工編號取消自動建立，這函式先留著
    def create_number_trigger(table="employee"):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f"""CREATE TRIGGER trg_employee_no
            AFTER INSERT ON {table}
            FOR EACH ROW
            BEGIN
                UPDATE employee
                SET employee_no = 'E' || printf('%03d', NEW.id)
                WHERE id = NEW.id;
            END;"""
            cursor.execute(query)
            con.commit()
        return f"{table}表格的Trigger: trg_employee_no 建立成功"

    @staticmethod  # 員工離職順手刪帳號
    def create_status_trigger(table="employee"):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f"""CREATE TRIGGER employee_quick
            AFTER UPDATE OF status ON {table}
            FOR EACH ROW
            WHEN OLD.status = 1 AND NEW.status = 0
            BEGIN
                DELETE FROM user WHERE employee_no=OLD.employee_no;
            END;"""
            cursor.execute(query)
            con.commit()
        return f"{table}表格的Trigger: employee_quick 建立成功"

    @staticmethod
    def drop_number_trigger(trigger_name="trg_employee_no"):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f"""DROP TRIGGER IF EXISTS {trigger_name}"""
            cursor.execute(query)
            con.commit()
        return f"Trigger: {trigger_name} 移除成功"

    @staticmethod
    def insert_employee(
        employee_no,
        employee_name,
        role,
        department,
        phone=None,
        personal_email=None,
        create_by="admin",
    ):
        try:
            database=get_db_path()
            with sqlite3.connect(database) as con:
                con.execute("PRAGMA foreign_keys = ON;")
                cursor = con.cursor()
                query = "INSERT INTO employee (employee_no,employee_name,department,role,phone,personal_email,create_by) VALUES (?,?,?,?,?,?,?)"
                data = (
                    employee_no,
                    employee_name,
                    department,
                    role,
                    phone,
                    personal_email,
                    create_by,
                )
                cursor.execute(query, data)
                con.commit()

            return (
                True,
                f"{create_by}已將{employee_name}建立成功，員工編號:{employee_no}",
            )
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def read_employee_table(employee_name=None, status=1):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            if employee_name != None and status == 1:
                query = "SELECT * FROM employee WHERE employee_name = ? AND status=?"
                data = (employee_name, status)
                cursor.execute(query, data)
            elif employee_name != None and status != 1:
                query = "SELECT * FROM employee WHERE employee_name = ? AND status=?"
                data = (employee_name, status)
                cursor.execute(query, data)
            else:
                query = "SELECT * FROM employee"
                cursor.execute(query)
            workers = cursor.fetchall()
            if workers is None:
                return False, []
            else:
                columns = [col[0] for col in cursor.description]
                employee_data = [dict(zip(columns, row)) for row in workers]
                return True, employee_data

    @staticmethod
    def read_employee_for_flask():
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "SELECT * FROM employee WHERE status=?"
            data = (1,)
            cursor.execute(query, data)
            workers = cursor.fetchall()
            if workers is None:
                raise ValueError("目前資料表沒有員工在職!")
            else:
                columns = [col[0] for col in cursor.description]
                workers_data = [dict(zip(columns, row)) for row in workers]
                worker_dicts = DataTransfer(workers_data).to_worker_dicts()
                return worker_dicts

    @staticmethod
    def update_employee_table(employee_no, column=None, new_data=None):
        columns = [
            "employee_no",
            "employee_name",
            "department",
            "status",
            "role",
            "phone",
            "personal_email",
        ]
        try:
            if (column == "employee_name" and new_data is None) or (
                column == "status" and new_data == "0"
            ):
                database=get_db_path()
                with sqlite3.connect(database) as con:
                    cursor = con.cursor()
                    query = f"UPDATE employee SET status=? WHERE employee_no=?"
                    data = (0, employee_no)
                    cursor.execute(query, data)
                    con.commit()

                return True, f"已將{employee_no} 狀態改為0(離職)"
            elif column in columns:
                database=get_db_path()
                with sqlite3.connect(database) as con:
                    cursor = con.cursor()
                    query = (
                        f"UPDATE employee SET {column}=? WHERE employee_no=?"
                    )
                    data = (new_data, employee_no)
                    cursor.execute(query, data)
                    con.commit()
                return True, f"已將{employee_no}的欄位{column}修改為{new_data}"
            else:
                return False, f"找不到{column}  可修改其欄位"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def delete_employee(id):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "DELETE FROM employee WHERE id=?"
            data = (id,)
            cursor.execute(query, data)
            con.commit()
        return f"已從employee表格中刪除{id}紀錄"
    
class UserTableCRUD:
    @staticmethod
    def create_user_table(database=None):
        if database is None:
            database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = """CREATE TABLE IF NOT EXISTS user(
                id INTEGER PRIMARY KEY,
                user_name TEXT NOT NULL UNIQUE,
                employee_no TEXT NOT NULL REFERENCES employee(employee_no),
                account TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                last_login TIMESTAMP,
                last_fail_login TIMESTAMP,
                fail_login_times INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
            cursor.execute(query)
            con.commit()
            return True

    @staticmethod
    def insert_user(user_name, employee_no, account, password, email):
        try:
            password = secur.generate_password_hash(password)
            database=get_db_path()
            with sqlite3.connect(database) as con:
                con.execute("PRAGMA foreign_keys = ON;")
                cursor = con.cursor()
                query = "INSERT INTO user (user_name,employee_no,account, password, email) VALUES (?,?, ?, ?,?)"
                cursor.execute(
                    query, (user_name, employee_no, account, password, email)
                )
                con.commit()
            return f"使用者:{user_name}帳戶{account}已創建成功"
        except Exception as e:
            return f"發生錯誤:{e}"

    @staticmethod
    def read_user_table(user_name=None,account=None):
        if user_name is not None or account is not None:
            column_dict={"user_name":user_name,"account":account}
            data_dict={k:v for k,v in column_dict.items() if v is not None}
            data_keys=list(data_dict.keys())
            # print(data_keys)
            condition_columns=[]
            for key in data_keys:
                key += "=?"
                condition_columns.append(key)
            condition_statement=" AND ".join(condition_columns)
            values=list(data_dict.values())

            sql = f"""SELECT * FROM user WHERE {condition_statement}"""
            # print(sql)
            # print(values)
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                cursor.execute(sql, tuple(values))
                user = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                user_data = [dict(zip(columns, row)) for row in user]
                return user_data
        else:
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor = con.cursor()
                query = "SELECT * FROM user"
                cursor.execute(query)
                users = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                user_data = [dict(zip(columns, row)) for row in users]
                return user_data

    @staticmethod
    def delete_user(id, user_name=None):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            if user_name != None:
                query = "DELETE FROM user WHERE id=? AND user_name=?"
                data = (id, user_name)
            else:
                query = "DELETE FROM user WHERE id=?"
                data = (id,)
            cursor.execute(query, data)
            con.commit()
        return f"已從user表格中刪除{id}的資料"
    @staticmethod
    def update_user(employee_no, column, new_data):
        try:
            if column=="password":
               new_data=secur.generate_password_hash(new_data)
            database=get_db_path() 
            with sqlite3.connect(database) as con:
                cursor=con.cursor()
                query=f"UPDATE user SET {column}=? WHERE employee_no=?"
                data=(new_data,employee_no)
                cursor.execute(query,data)
                if cursor.rowcount == 0:
                    return False
                con.commit()
                return True
        except:
            traceback.print_exc()
            return False
        
    @staticmethod
    def update_login_record(login_boll,account,try_times=0):
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if login_boll:
            query="UPDATE user SET last_login=?,fail_login_times=? WHERE account=?"
            data=(now,0,account)
        elif 1<try_times<6:
            query="UPDATE user SET fail_login_times=fail_login_times + 1 WHERE account=?"
            data=(account,)
        else:
            query="UPDATE user SET last_fail_login=?,fail_login_times=fail_login_times + 1 WHERE account=?"
            data=(now,account)
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor=con.cursor()
            cursor.execute(query,data)
            con.commit()

    @staticmethod
    def user_locked(user_data:dict):
        last_login= user_data["last_login"]
        fail_login_times= int(user_data['fail_login_times'])
        last_fail_login= user_data["last_fail_login"]
        if last_login is None and fail_login_times==0:
            return False
        elif last_fail_login is None:
            return False
        else:
            last_fail_login=datetime.strptime(last_fail_login,"%Y-%m-%d %H:%M:%S")
            now=datetime.now()
            deltatime=now-last_fail_login
            if deltatime>timedelta(minutes=30):
                return False 
            else:
                return (deltatime < timedelta(minutes=30)and fail_login_times >= 5)
            
    @staticmethod
    def login_check(account,password):
        user_list=UserTableCRUD.read_user_table(account=account)
        if user_list==[] or len(user_list)>1:
            return False,{"user_data":None,"falure_message":"no users_account"}
        user=user_list[0]
        try_times=int(user['fail_login_times'])
        is_locked=UserTableCRUD.user_locked(user)
        if not is_locked:
            password_hash=user['password']
            if secur.check_password_hash(password_hash,password):
                UserTableCRUD.update_login_record(True,account,try_times=try_times)
                min_user_info=DataTransfer(user_list).remove_information(information_keys=("id","created_at","password","last_fail_login","fail_login_times"))
                print(min_user_info)
                return True,{"user_data":min_user_info[0],"falure_message":None}
            else:
                try_times +=1
                UserTableCRUD.update_login_record(False,account,try_times=try_times)
                return False,{"user_data":None,"falure_message":"login faliure"}
        else:
            return False,{"user_data":None,"falure_message":"Too often login"}

    @staticmethod
    def validation_data_build(relationship,author_name):
        relationship=bcrypt.hashpw(relationship.encode("utf-8"),bcrypt.gensalt())
        author_name=bcrypt.hashpw(author_name.encode("utf-8"),bcrypt.gensalt())
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor=con.cursor()
            
            query2="INSERT INTO validation (key,value) VALUES(?,?)"
            data=(relationship,author_name)
            cursor.execute(query2,data)

            con.commit()

        return "成功建立validation資料"
    
    @staticmethod
    def validation_table_build(database= None):
        if database is None:
            database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor=con.cursor()
            query="CREATE TABLE IF NOT EXISTS validation (key BLOB NOT NULL,value BLOB NOT NULL)"
            cursor.execute(query)
            con.commit()
            return True

    @staticmethod
    def validation_infomations():
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor=con.cursor()
            query="SELECT * FROM validation"
            cursor.execute(query)
            validation_info=cursor.fetchall()
            if validation_info:
                return validation_info
            else:
                return []


    @staticmethod
    def validation_sequence(account,verify_email,relationship,name):
        user_info=UserTableCRUD.read_user_table(account=account)
        if user_info==None or len(user_info)>1:
            return False
        email=user_info[0]["email"]
        id=user_info[0]["id"]
        user_name=user_info[0]["user_name"]
        emplyee_no=user_info[0]["employee_no"]
        is_locked=UserTableCRUD.user_locked(user_info[0])
        if is_locked:
            return False
        elif verify_email==email:
            database=get_db_path()
            with sqlite3.connect(database) as con:
                cursor=con.cursor()
                query="SELECT * FROM validation"
                cursor.execute(query)
                vlidation_info=cursor.fetchall()
        # print(vlidation_info)
            relation_hash=vlidation_info[0][0]
            name_hash=vlidation_info[0][1]
            check=bcrypt.checkpw(relationship.encode("utf-8"),relation_hash) and bcrypt.checkpw(name.encode("utf-8"),name_hash)
            if check:
                now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                UserTableCRUD.update_user(emplyee_no,"last_login",now)
                UserTableCRUD.update_user(emplyee_no,"last_fail_login",now)
                UserTableCRUD.update_user(emplyee_no,"fail_login_times",6)
                
                return True
            else:
                UserTableCRUD.delete_user(id,user_name)
                return False
        else:
            return False 

class RoleTableCRUD:
    @staticmethod
    def create_role_table():
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = """CREATE TABLE role (
            id INTEGER PRIMARY KEY,
            role_name TEXT NOT NULL,
            department TEXT NOT NULL,
            HR_sys INTEGER CHECK(HR_sys IN(0,10,20,30))  DEFAULT 0,
            finance_sys INTEGER CHECK(finance_sys IN(0,10,20,30)) DEFAULT 0,
            order_sys INTEGER CHECK(order_sys IN(0,10,20,30)) DEFAULT 0,
            create_by TEXT DEFAULT 'admin',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );"""
            cursor.execute(query)
            con.commit()

    @staticmethod
    def insert_role(role_name,department,HR_sys,finance_sys,order_sys):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "INSERT INTO role (role_name,department,HR_sys,finance_sys,order_sys) Values(?,?,?,?,?)"
            data = (role_name,department,HR_sys,finance_sys,order_sys)
            cursor.execute(query, data)
            con.commit()

    @staticmethod
    def read_role():
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "SELECT * FROM role "
            cursor.execute(query)
            roles = cursor.fetchall()
        return roles

    @staticmethod
    def delete_role(id):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "DELETE FROM role WHERE id=?"
            data = (id,)
            cursor.execute(query, data)
            con.commit()
        return f"已從role表格中刪除{id}紀錄"

    @staticmethod
    def read_personal_permission(employee_no):
        database=get_db_path()
        with sqlite3.connect(database) as con:
           cursor = con.cursor()
           query ="""SELECT
                    e.employee_name,
                    r.HR_sys,
                    r.finance_sys,
                    r.order_sys
                FROM employee AS e
                INNER JOIN role AS r
                    ON e.role = r.role_name
                    AND e.department = r.department
                WHERE e.employee_no = ?;"""
           data=(employee_no,)
           cursor.execute(query,data)
           roles = cursor.fetchall()
           columns = [col[0] for col in cursor.description]
           user_promission = [dict(zip(columns, row)) for row in roles]
        return user_promission
"""
        ALTER TABLE Orders
ADD CONSTRAINT FK_Orders_Customer
FOREIGN KEY (CustomerID)
REFERENCES Customers(CustomerID);"""