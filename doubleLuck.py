import flask
from flask import render_template

from SQLmaintain import WorkingTimeTableCRUD, DataTransfer, EmployeeTableCRUD,ProductsTableCRUD,CustomerTableCRUD,UserTableCRUD
from SQLmaintain import default_date_range
from config import get_db_path,get_secret_key,get_session_time

doubleluck = flask.Flask(__name__)


doubleluck.secret_key = get_secret_key()
database=get_db_path()
doubleluck.config["PERMANENT_SESSION_LIFETIME"]=get_session_time()

@doubleluck.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        login_user = flask.request.get_json()
        account = login_user.get("account")
        password = login_user.get("password")
        access_bool,message=UserTableCRUD.login_check(account,password)
        if  access_bool:
            user_data=message["user_data"]
            flask.session["login"] = True
            flask.session.permanent = True
            flask.session["username"] = user_data["user_name"]
            flask.session["employee_id"]= user_data["employee_no"]
            flask.session["account"] = user_data["account"]
            flask.session["permisson"]=True #之後要來這裡改權限傳遞
            return flask.jsonify({"status":access_bool,"message": "welcome,"})
        else:
            return flask.jsonify({"status":access_bool,"message":f"{message["falure_message"]}"})

    else:
        return flask.render_template("login.html")


@doubleluck.route("/logout", methods=["Get"])
def logout():
    flask.session.clear()
    print("登出測試")
    return flask.redirect(flask.url_for("login"))

@doubleluck.route("/login/forgotpassword", methods=["POST"])
def forgotpassword():
    if flask.request.method == "POST":
        user_submit_info=flask.request.get_json()
        account=user_submit_info.get("account")
        email=user_submit_info.get("email")
        relationship=user_submit_info.get("relationship")
        name=user_submit_info.get("name")
        user_identity=UserTableCRUD.validation_sequence(account,email,relationship,name)
        if user_identity:
            user_data=UserTableCRUD.read_user_table(account=account)[0]
            flask.session["login"] = True
            flask.session["username"] = user_data["user_name"]
            flask.session["employee_id"]= user_data["employee_no"]
            flask.session["username"] = user_data["user_name"]
            flask.session["account"] = user_data["account"]
            flask.session["temporary_login"] = True
            return flask.jsonify({"status":True})
        else:
            return flask.jsonify({"status":False})
    else:
        return flask.render_template("login.html")

@doubleluck.route("/login/resetpassword",methods=["POST"])
def reset_password():
    if flask.session.get("login") !=True:
        return flask.redirect(flask.url_for("login"))
    reset_password_info=flask.request.get_json()
    new_password=reset_password_info.get("new_password")
    confirm_password=reset_password_info.get("confirm_password")
    password=reset_password_info.get("origin_password")
    # print(f"前端來的資訊:{reset_password_info}")
    if flask.session.get("temporary_login") ==True:
        login_check=True
    else:
        account=flask.session.get("account")
        login_check,_= UserTableCRUD.login_check(account,password)
        
    if login_check:       
        employee_no=flask.session.get("employee_id")
        print(employee_no)
        if confirm_password==new_password:
            result=UserTableCRUD.update_user(employee_no,"password",confirm_password)
            print(f"密碼重設結果:{result}")
            return flask.jsonify({"status":True})
        else:
            return flask.jsonify({"status":False})
    else:
        return flask.jsonify({"status":False})

@doubleluck.route("/")
def home():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        return flask.render_template(
            "homepage.html", username=flask.session.get("username")
        )


@doubleluck.route("/addWorkHour", methods=["GET"])
def to_duration_page():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        workers = EmployeeTableCRUD.read_employee_for_flask()
        return flask.render_template(
            "workDuration.html",
            username=flask.session.get("username"),
            workers=workers,
        )


@doubleluck.route("/insertDuration", methods=["POST"])
def add_Duration():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))

    working_data = flask.request.get_json()
    
    _, worker_dicts = EmployeeTableCRUD.read_employee_table()
    worker_dicts = DataTransfer(worker_dicts).to_worker_dicts(nick_name=False)
    
    recorder = flask.session["employee_id"]
    
    # 提取共用參數
    work_date = working_data["date"]
    start_time = working_data["start_time"]
    end_time = working_data["end_time"]
    duration = working_data["duration"]
    work_description = working_data["workContent"]
    
    data = []
    
    # 將寫入與計算合併在同一個迴圈，減少重複走訪
    for worker_no in working_data["workers"]:
        worker = worker_dicts[worker_no]
        worker_name = worker
        worker_nick_name = worker[-1]
        
        # 1. 寫入資料庫
        success, _ = WorkingTimeTableCRUD.insert_work_time(
            worker_name,
            work_date,
            start_time,
            end_time,
            duration,
            work_description,
            recorder,
        )
        
        if not success:
            worker_duration = None
        else:
            start_date,end_date=default_date_range()
            worker_record = WorkingTimeTableCRUD.read_work_time_table(
                worker,start_date,end_date
            )
            if worker_record:
                worker_duration = DataTransfer(worker_record).get_duration_sum()
            else:
                worker_duration = 0
                
        data.append({worker_nick_name: worker_duration})

    return flask.jsonify({"status": True, "data": data})

@doubleluck.route("/readpersonalDuration", methods=["GET"])
def get_personal_duration():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        user = flask.session["username"]
        data = []
        worker_record = WorkingTimeTableCRUD.read_work_time_table(user)
        print(worker_record)
        if worker_record is not None:
            worker_duration = DataTransfer(worker_record).get_duration_sum()
            worker_data = {user: worker_duration}
            data.append(worker_data)
            return flask.jsonify({"status": True, "data": data})
        else:
            worker_data = {user: 0}
            data.append(worker_data)
            return flask.jsonify({"status": True, "data": data})

@doubleluck.route("/order/create",methods=["GET"])
def to_create_order_page():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        products = ProductsTableCRUD.read_products_for_flask()
        freights= ProductsTableCRUD.read_products_for_flask(product_class='freight')
        return flask.render_template(
            "createOrder.html",
            item=products,freights=freights
        )

@doubleluck.route("/orders/search-customer",methods=["POST"])
def search_customer():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        recorder = flask.session["employee_id"]
        customer_data = flask.request.get_json()
        customer_name = customer_data['buyerName']
        # customer_phone= customer_data['buyerPhone']
        # customer_adress = customer_data['byerAdress']
        receiver_name=customer_data['receivername']
        checkresult,SQL_data=CustomerTableCRUD.read_customer_for_flask(customer_name)
        
        print(checkresult)
        print(SQL_data)
        if not checkresult and not isinstance(SQL_data,list):
            return flask.jsonify({"status":False,'data':None})
        elif not checkresult and isinstance(SQL_data,list):
            return flask.jsonify({"status":False,'data':SQL_data})
        else:
            return flask.jsonify({"status":True,'data':SQL_data})



if __name__ == "__main__":
    doubleluck.run(debug=True, host="localhost", port=5000)
    # doubleluck.run(debug=True, host="0.0.0.0", port=5000)
