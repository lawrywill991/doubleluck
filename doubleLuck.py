import flask
import traceback
from flask import render_template
from datetime import datetime, date
from zoneinfo import ZoneInfo

from SQLmaintain import (
    WorkingTimeTableCRUD,
    DataTransfer,
    EmployeeTableCRUD,
    ProductsTableCRUD,
    CustomerTableCRUD,
    UserTableCRUD,
    OrderTableCRUD,
)
from SQLmaintain import (
    default_date_range,
    calculate_reserved_amount,
    check_oder_data,
    order_taking_date_check,
    order_reserving_date_check,
    ORDER_STATUS,
)
from config import get_db_path, get_secret_key, get_session_time

doubleluck = flask.Flask(__name__)


doubleluck.secret_key = get_secret_key()
database = get_db_path()
doubleluck.config["PERMANENT_SESSION_LIFETIME"] = get_session_time()


@doubleluck.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        login_user = flask.request.get_json()
        account = login_user.get("account")
        password = login_user.get("password")
        access_bool, message = UserTableCRUD.login_check(account, password)
        if access_bool:
            user_data = message["user_data"]
            flask.session["login"] = True
            flask.session.permanent = True
            flask.session["username"] = user_data["user_name"]
            flask.session["employee_id"] = user_data["employee_no"]
            flask.session["account"] = user_data["account"]
            flask.session["permisson"] = True  # 之後要來這裡改權限傳遞
            return flask.jsonify({"status": access_bool, "message": "welcome,"})
        else:
            return flask.jsonify(
                {"status": access_bool, "message": f"{message["falure_message"]}"}
            )

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
        user_submit_info = flask.request.get_json()
        account = user_submit_info.get("account")
        email = user_submit_info.get("email")
        relationship = user_submit_info.get("relationship")
        name = user_submit_info.get("name")
        user_identity = UserTableCRUD.validation_sequence(
            account, email, relationship, name
        )
        if user_identity:
            user_data = UserTableCRUD.read_user_table(account=account)[0]
            flask.session["login"] = True
            flask.session["username"] = user_data["user_name"]
            flask.session["employee_id"] = user_data["employee_no"]
            flask.session["username"] = user_data["user_name"]
            flask.session["account"] = user_data["account"]
            flask.session["temporary_login"] = True
            return flask.jsonify({"status": True})
        else:
            return flask.jsonify({"status": False})
    else:
        return flask.render_template("login.html")


@doubleluck.route("/login/resetpassword", methods=["POST"])
def reset_password():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    reset_password_info = flask.request.get_json()
    new_password = reset_password_info.get("new_password")
    confirm_password = reset_password_info.get("confirm_password")
    password = reset_password_info.get("origin_password")
    # print(f"前端來的資訊:{reset_password_info}")
    if flask.session.get("temporary_login") == True:
        login_check = True
    else:
        account = flask.session.get("account")
        login_check, _ = UserTableCRUD.login_check(account, password)

    if login_check:
        employee_no = flask.session.get("employee_id")
        print(employee_no)
        if confirm_password == new_password:
            result = UserTableCRUD.update_user(
                employee_no, "password", confirm_password
            )
            print(f"密碼重設結果:{result}")
            return flask.jsonify({"status": True})
        else:
            return flask.jsonify({"status": False})
    else:
        return flask.jsonify({"status": False})


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
            start_date, end_date, _ = default_date_range(usage_sys="workduration")
            worker_record = WorkingTimeTableCRUD.read_work_time_table(
                worker, None, start_date, end_date
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
        start_date, _, end_date = default_date_range(usage_sys="workduration")
        worker_record = WorkingTimeTableCRUD.read_work_time_table(
            user, None, start_date, end_date
        )
        # print(worker_record)
        if worker_record:
            worker_duration = DataTransfer(worker_record).get_duration_sum()
        else:
            worker_duration = 0
        data.append({user: worker_duration})
        return flask.jsonify({"status": True, "data": data})


@doubleluck.route("/duration/recentRecords", methods=["GET"])
def to_Duration_page():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        username = flask.session.get("username")
        # print(username)
        records = WorkingTimeTableCRUD.read_personal_duration_list(username)
        # print(records)
        return flask.render_template(
            "latestDuration.html", username=username, records=records
        )


@doubleluck.route("/order/new-order", methods=["GET"])
def to_create_order_page():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        products = ProductsTableCRUD.read_products_for_flask()
        freights = ProductsTableCRUD.read_products_for_flask(product_class="freight")
        return flask.render_template(
            "createOrder.html", item=products, freights=freights
        )


@doubleluck.route("/orders/search-customer", methods=["POST"])
def search_customer():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        request_data = flask.request.get_json(silent=True) or {}
        customer_name = str(request_data.get("buyerName", "")).strip()
        if not customer_name:
            return flask.jsonify({"status": False, "data": []})
        found, customers = CustomerTableCRUD.read_customer_for_flask(customer_name)
        return flask.jsonify({"status": found, "data": customers})


@doubleluck.route("/order/create", methods=["POST"])
def create_order():
    # today = datetime.now(ZoneInfo("Asia/Taipei"))
    today = datetime(2026, 8, 22, tzinfo=ZoneInfo("Asia/Taipei"))
    date_after_start = order_taking_date_check(today)
    in_reserving_period = order_reserving_date_check(today)
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    elif not date_after_start:
        return flask.jsonify(False, "尚未開放key單")
    else:
        order_data = flask.request.get_json()
        order_data = order_data["orderData"]
        order_data.update({"qty": int(order_data["qty"])})
        order_data.update({"subtotal": int(order_data["subtotal"])})
        order_data.update({"shipment_fee": int(order_data["shipment_fee"])})
        # print(order_data)
        recorder = flask.session["employee_id"]
        # 先檢查傳來後端的資料有無缺少，電話格式是否正確
        data_check_bool, data_missing = check_oder_data(order_data)
        if data_check_bool == False:
            return flask.jsonify(False, f"資料有缺少{data_missing}")
        # 先用產品代號取得產品資料
        product_code = order_data["product_code"]
        product_info = ProductsTableCRUD.read_product_info(product_code)
        if product_info is None:
            raise KeyError("product code is not in product table")
        else:
            product_name = product_info["product_name"]
            spec = product_info["spec"]
        new_qty = order_data["qty"]
        # 用客戶名稱查詢客戶編號，沒有則新增
        customer_name = order_data["customer_name"]
        customer_info = CustomerTableCRUD.read_customer_table(
            customer_name=customer_name
        )
        if customer_info == []:
            customer_phone = order_data["customer_phone"]
            customer_address = order_data["customer_address"]
            new_customer = CustomerTableCRUD.insert_customer(
                customer_name, customer_phone, customer_address, recorder
            )
            # print(new_customer)
            customer_info = CustomerTableCRUD.read_customer_table(
                customer_name=customer_name
            )
            customer_id = customer_info[0]["customer_id"]
        else:
            customer_id = customer_info[0]["customer_id"]
        # 計算並取得業務員的保留額與使用狀況
        if in_reserving_period:
            salse_record = OrderTableCRUD.get_sales_df(recorder)
            reservation_weight = OrderTableCRUD.get_sales_reservation(salse_record)
            reservation = calculate_reserved_amount(recorder)
            reservation_result = OrderTableCRUD.check_new_order_status(
                product_code, reservation_weight, order_data["qty"], reservation
            )
        else:
            reservation_result = "排單"
        # print(reservation_result)
        # 先寫正常接單的部分，保留或排序
        if reservation_result != "退回":
            insert_bool, new_order_id = OrderTableCRUD.insert_order_table(
                reservation_result,
                product_code,
                product_name,
                spec,
                new_qty,
                customer_id,
                order_data["subtotal"],
                order_data["shipment_fee"],
                order_data["receiver_name"],
                order_data["receiver_phone"],
                order_data["receiver_address"],
                recorder,
                payment_method=order_data["predict_payment_method"],
                order_notes=order_data["order_notes"],
                ship_date_requested=order_data.get("ship_date"),
            )
        else:
            return flask.jsonify(
                False, f"本次新增重量會超過您的保留額，請決定降低數量key單或整單取消"
            )
        # 利用訂單編號查詢回傳本單排序號是幾號&前面有多少單
        if insert_bool:
            year = today.year
            df = OrderTableCRUD.read_order_for_xlsx(year)
            reservation, sequence, reservated_weight = (
                OrderTableCRUD.get_order_sequesnce(df, new_order_id)
            )
            return flask.jsonify(
                True,
                f"訂單輸入成功，訂單號碼{new_order_id}，本單為{reservation}訂單,第{sequence}順位,前面有{reservated_weight}台斤待出貨",
            )
        else:
            return flask.jsonify(False, f"發生未預期錯誤，請聯繫程式開發者確認")


# ===== 查詢我的訂單：只能查詢、取消自己建立的單 =====
@doubleluck.route("/order/my-orders", methods=["GET"])
def to_my_orders_page():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        return flask.render_template("myOrders.html")


@doubleluck.route("/order/my-orders/search", methods=["POST"])
def search_my_orders():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        request_data = flask.request.get_json(silent=True) or {}
        keyword = str(request_data.get("keyword", "")).strip()
        status = str(request_data.get("status", "")).strip()
        if status and status not in ORDER_STATUS:
            return flask.jsonify({"status": False, "data": []})
        try:
            orders = OrderTableCRUD.read_order_for_flask(
                flask.session["employee_id"], keyword or None, status or None
            )
        except Exception:
            traceback.print_exc()
            return flask.jsonify({"status": False, "data": []}), 500
        return flask.jsonify({"status": True, "data": orders})


@doubleluck.route("/order/my-orders/cancel", methods=["POST"])
def cancel_my_order():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        request_data = flask.request.get_json(silent=True) or {}
        order_id = str(request_data.get("order_id", "")).strip()
        if not order_id:
            return flask.jsonify({"status": False, "message": "缺少訂單編號"})
        # 擁有者與狀態都在 cancel_order_for_flask 裡檢查，不靠前端藏按鈕
        result, message = OrderTableCRUD.cancel_order_for_flask(
            order_id, flask.session["employee_id"]
        )
        return flask.jsonify({"status": result, "message": message})


@doubleluck.route("/order/get-myreservation", methods=["GET"])
def get_personal_reservation():
    if flask.session.get("login") != True:
        return flask.redirect(flask.url_for("login"))
    else:
        employee_no = flask.session["employee_id"]
        # start_date, today, end_date = default_date_range("orders") #我不確定明年的時候會不會日期範圍出錯，先留著
        # 日期要和 /order/create 一致，上線時兩邊一起換回正式的 today
        # today = datetime.now(ZoneInfo("Asia/Taipei"))
        today = datetime(2026, 8, 22, tzinfo=ZoneInfo("Asia/Taipei"))
        in_reserving_period = order_reserving_date_check(today)
        sales_df = OrderTableCRUD.get_sales_df(employee_no)
        reservation_usage = OrderTableCRUD.get_sales_reservation(sales_df)
        reservation_quota = calculate_reserved_amount(employee_no)
        return flask.jsonify(
            {
                "status": True,
                "quota": reservation_quota,
                "usage": reservation_usage,
                "in_reserving_period": in_reserving_period,
            }
        )


if __name__ == "__main__":
    doubleluck.run(debug=True, host="localhost", port=5000)
    # doubleluck.run(debug=True, host="0.0.0.0", port=5000)
