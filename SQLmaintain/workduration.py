import sqlite3
from datetime import datetime, date, time
import traceback

import pandas as pd

from config import get_db_path



class WorkingTimeTableCRUD:
    @staticmethod
    def create_work_time_table(database= None):
        if database is None:
            database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = """CREATE TABLE IF NOT EXISTS work_time(
                id INTEGER PRIMARY KEY,
                worker TEXT NOT NULL,
                work_date DATE NOT NULL,
                start_time TIME CHECK(time(start_time) IS NOT NULL),
                end_time TIME CHECK(time(end_time) IS NOT NULL),
                duration REAL NOT NULL,
                work_description TEXT NOT NULL,
                recorder TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recorder) REFERENCES employee(employee_no),
                CONSTRAINT chk_time_order CHECK(end_time > start_time)
            )"""
            cursor.execute(query)
            con.commit()

    @staticmethod
    def create_time_trigger(table="work_time"):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f""" CREATE TRIGGER prevent_time_overlap
            BEFORE INSERT ON {table}
            FOR EACH ROW
            BEGIN
                SELECT RAISE(ABORT,"工作者時間已重疊")
                WHERE EXISTS(SELECT 1 FROM {table} WHERE (NEW.worker=worker) 
                AND (work_date = NEW.work_date) 
                AND (NEW.start_time <end_time) 
                AND (NEW.end_time > start_time));
            END;"""
            cursor.execute(query)
            con.commit()
        return f"{table}表格的Trigger: prevent_time_overlap 建立成功"

    @staticmethod
    def drop_time_trigger(trigger_name="prevent_time_overlap"):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = f"""DROP TRIGGER IF EXISTS {trigger_name}"""
            cursor.execute(query)
            con.commit()
        return f"Trigger: {trigger_name} 移除成功"

    @staticmethod
    def insert_work_time(
        worker,
        work_date,
        start_time,
        end_time,
        duration,
        work_description,
        recorder,
    ):
        try:
            if isinstance(work_date, date):
                work_date = work_date
            else:
                work_date = datetime.strptime(work_date, "%Y-%m-%d").date()
            work_date = work_date.strftime(
                "%Y-%m-%d"
            )  # 再轉回str才能給SQL存成TEXT
            if isinstance(start_time, time):
                start_time = start_time
            else:
                start_time = datetime.strptime(start_time, "%H:%M").time()
            start_time = start_time.strftime(
                "%H:%M"
            )  # 再轉回str才能給SQL存成TEXT
            if isinstance(end_time, time):
                end_time = end_time
            else:
                end_time = datetime.strptime(end_time, "%H:%M").time()
            end_time = end_time.strftime("%H:%M")  # 再轉回str才能給SQL存成TEXT

            database=get_db_path()
            with sqlite3.connect(database) as con:
                con.execute("PRAGMA foreign_keys = ON;")
                cursor = con.cursor()
                query = "INSERT INTO work_time (worker, work_date, start_time, end_time,duration,work_description,recorder) VALUES (?, ?, ?, ?,?,?,?)"
                data = (
                    worker,
                    work_date,
                    start_time,
                    end_time,
                    duration,
                    work_description,
                    recorder,
                )
                cursor.execute(query, data)
                con.commit()
            return (
                True,
                f"使用者:{recorder}已將{worker}的工時{duration} 小時輸入成功",
            )
        except sqlite3.IntegrityError as e:
            if "時間已重疊" in str(e):
                return False, f"{worker}的{work_date}已存在:{e}"
            else:
                return False, f"發生錯誤:{e}"
        except Exception as e:
            traceback.print_exc()
            return False, f"發生錯誤:{e}"

    @staticmethod
    def read_work_time_table(worker=None, recorder=None, start_date=None,end_date=None)->list[dict]:
        search_columns=[]
        search_values=[]
        if worker is not None:
            search_columns.append("worker=?")
            search_values.append(worker)
        if recorder is not None:
            search_columns.append("recorder=?")
            search_values.append(recorder)
        if start_date is not None and end_date is not None:
            if start_date <=date(2025,10,1):
                start_date=date(2025,10,1)
            search_columns.append("work_date BETWEEN ? AND ?")
            search_values.append(str(start_date))
            search_values.append(str(end_date))

        sql = "SELECT * FROM work_time"
        if search_columns:
            sql += " WHERE " + " AND ".join(search_columns)
        # print(sql)
        # print(search_values)

        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            if search_columns==[]:
                cursor.execute(sql)
            else:
                cursor.execute(sql,search_values)
            work_times = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in work_times]
            return data

    @staticmethod
    def delete_work_time(
        id,
    ):
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor = con.cursor()
            query = "DELETE FROM work_time WHERE id=?"
            data = (id,)
            cursor.execute(query, data)
            con.commit()
        return f"已從work_time表格中刪除{id}紀錄"

    @staticmethod
    def read_work_time_total(full_record=False):
        today = date.today()
        year = today.year
        if today.month <= 9:
            start_date = date(year - 1, 9, 30)
        else:
            start_date = date(year, 10, 1)
        database=get_db_path()
        with sqlite3.connect(database) as con:
            if not full_record:
                query = (
                    f"SELECT * FROM work_time WHERE work_date BETWEEN ? AND ?"
                )
                data = (start_date, today)
                full_df = pd.read_sql_query(query, con, params=data)
            else:
                query = f"SELECT * FROM work_time"
                full_df = pd.read_sql_query(query, con)

        grouped_df = full_df.groupby("worker")["duration"].sum()
        return grouped_df

    @staticmethod
    def read_personal_duration_list(worker,No_of_data=5)->list|None:
        database=get_db_path()
        with sqlite3.connect(database) as con:
            cursor=con.cursor()
            query=f"""SELECT wt.work_date, wt.duration, e.employee_name AS recorder FROM work_time AS wt 
            JOIN employee AS e ON wt.recorder = e.employee_no
            WHERE worker = ? ORDER BY wt.id DESC LIMIT ?;"""
            values=(worker,No_of_data)
            cursor.execute(query,values)
            personal_duration=cursor.fetchall()
        if personal_duration !=[]:
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in personal_duration]
            return data
        else:
            return []