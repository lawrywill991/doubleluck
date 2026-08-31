import sys
# print(sys.path)
from SQLmaintain import EmployeeTableCRUD,UserTableCRUD,WorkingTimeTableCRUD,ProductsTableCRUD,CustomerTableCRUD,RoleTableCRUD,OrderTableCRUD
from SQLmaintain import database_manager,check_phone,DataTransfer,check_internal_id_format,check_datetime_formuler,date_compliarty

from datetime import date
# import pandas as pd

def main():
    
    while True:
        function_choice = input(
            "請選擇要執行的功能：1.查看資料表完整內容 2.輸入單筆資料 3.更新單一欄位 0.退出\n"
        ).upper()
        if function_choice == "0":
            print("退出程式。")
            sys.exit()
        if (
            function_choice == "ZZ"
        ):  # 查詢db檔內容或創建、刪除表格(都只能單次操作)
            tables = database_manager.check_tables()
            print(tables)
            necessary_tables = [
                "user",
                "work_time",
                "employee",
                "products",
                "role",
                "customers",
                "validation",
                "orders"
            ]
            if set(tables) != set(necessary_tables):
                table_choice = input(
                    "目前還少table，請選擇建立：A.使用者資料表 B.工作時間資料表 c.員工資料表 D.職位列表 E.產品規格售價表 F:顧客資料表 G:訂單資料表 V:驗證資料, \n"
                ).upper()
                if table_choice == "A":
                    UserTableCRUD.create_user_table()
                    print("使用者資料表已創建成功！")
                    break
                elif table_choice == "B":
                    WorkingTimeTableCRUD.create_work_time_table()
                    print("工作時間資料表已創建成功！")
                    trigger_add_result = (
                        WorkingTimeTableCRUD.create_time_trigger()
                    )
                    print(trigger_add_result)
                    break
                elif table_choice == "C":
                    EmployeeTableCRUD.create_enployee_table()
                    print("員工資料表已創建成功!")
                    break
                elif table_choice == "E":
                    ProductsTableCRUD.create_product_table()
                    print("產品規格售價表已創建成功!")
                    break
                elif table_choice == "D":
                    RoleTableCRUD.create_role_table()
                    print("職位表已創建成功!")
                    break
                elif table_choice =="V":
                    relation=input("請輸入關係: \n")
                    name= input("請輸入人名:\n")
                    UserTableCRUD.validation_table_build()
                    result=UserTableCRUD.validation_data_build(relation,name)
                    print(result)
                elif table_choice == "F":
                    CustomerTableCRUD.create_customer_table()
                    print("顧客資料表已創建成功!")
                elif table_choice == "G":
                    OrderTableCRUD.create_order_table()
                    print("訂單資料表已創建成功!")
                else:
                    print("暫無預設表格可輸入，請聯繫程式作者")
                    break
            table_deal = input(
                "請輸入表格操作A.查表格欄位與設定 B.刪除整個表格 C.加入Trigger 0.退出\n"
            ).upper()
            if table_deal == "0":
                print("退出db_manager")
                continue
            elif table_deal =="C":
                result=database_manager.check_trigger()
                print(result)

            table = input("請輸入操作表格名稱 \n")
            if (table in tables) & (table_deal == "B"):
                delete_result = database_manager.delete_table(table)
                print(delete_result)
            elif (table in tables) & (table_deal == "A"):
                columns = database_manager.check_table_columns(table)
                print(columns)
            elif (table == "work_time") & (table_deal == "C"):
                # trigger_remove = WorkingTimeTableCRUD.drop_time_trigger()
                # print(trigger_remove)
                trigger_add_result = WorkingTimeTableCRUD.create_time_trigger()
                print(trigger_add_result)
            elif (table == "employee") & (table_deal == "C"):
                # trigger_remove=EmployeeTableCRUD.drop_number_trigger()
                # print(trigger_remove)
                # trigger_add_result=EmployeeTableCRUD.create_number_trigger()
                # print(trigger_add_result)
                trigger_add_result = EmployeeTableCRUD.create_status_trigger()
                print(trigger_add_result)
            elif (table == "customers") & (table_deal=="C"):
                trigger_add_result = CustomerTableCRUD.create_customer_trigger()
                print(trigger_add_result)
                # trigger_removed_result=database_manager.drop_trigger("trg_customer_id")
                # print(trigger_removed_result)
            elif (table =="orders") & (table_deal=="C"):
                trigger_add_result = OrderTableCRUD.create_order_trigger()
                print(trigger_add_result)
                # trigger_removed_result=database_manager.drop_trigger("trg_order_id")
                # print(trigger_removed_result)
            else:
                print("查無表格名稱或，請重新操作")
                break

            # if table_deal=="B":

            break
#加速尋找: 以上為db manager區；以下是正是操作區----------------
        table_choice = input(
            "請選擇要操作的資料表：A.使用者資料表 B.工作時間資料表 C.員工資料表 D:產品規格表 E:客戶資料表 F:職位權限表 G:訂單資料表\n"
        )
        if function_choice == "1" and table_choice.upper() == "A":
            data = UserTableCRUD.read_user_table()
            print(data)
            break  # 一次插入一筆就好(先別嫌煩)
        elif function_choice == "1" and table_choice.upper() == "B":
            worker = input("請輸入查詢對象 Enter=明細全查 \n")
            _, employee_data = EmployeeTableCRUD.read_employee_table()
            employee_name_list = (
                DataTransfer(employee_data)
                .to_worker_dicts(nick_name=False)
                .values()
            )

            while worker not in employee_name_list:
                if worker=="":
                    worker=None
                    break
                worker=input("查無該工作者，請重新輸入查詢對象 Enter=明細全查 \n")
                 
            start_date = input("請輸入查詢起始日期 Enter=資料庫起用日 \n")
            if start_date =="":
                start_date="2025-10-01"
            bool_s,start_date=check_datetime_formuler(start_date)
            while not bool_s:
                start_date = input("起始日期不合法，請重新輸入 \n")
                bool_s,start_date=check_datetime_formuler(start_date)

            end_date = input("請輸入查詢結束日期 Enter=今天 \n")
            if end_date =="":
                end_date=date.today()
            bool_e,end_date=check_datetime_formuler(end_date)
            while not bool_e:
                end_date = input("起始日期不合法，請重新輸入 \n")
                bool_e,end_date=check_datetime_formuler(end_date) 
            # print(employee_name_list)
            recorder = None
            assert isinstance(start_date,date)
            assert isinstance(end_date,date)
            date_compliance=date_compliarty(start_date,end_date)
            if not date_compliance:
                print("日期前後打錯，請重來")
                sys.exit()
                
            work_records = WorkingTimeTableCRUD.read_work_time_table(
                                    worker,recorder,start_date,end_date
                                )
            for work_record in work_records:
                print(work_record)
            break
        elif function_choice == "1" and table_choice.upper() == "C":
            worker = input("請輸入查詢對象 Enter=全查 \n")
            staus = input("請輸入查詢範圍 1:在職 0:離職 Enter=全查")
            if worker == "":
                result, message = EmployeeTableCRUD.read_employee_table()
            else:
                result, message = EmployeeTableCRUD.read_employee_table(worker)
            for employee in message:
                print(employee)
            break
        elif function_choice == "1" and table_choice.upper() == "D":
            _, products_data = ProductsTableCRUD.read_products_table()
            for products in products_data:
                print(products)
            break
        elif function_choice == "1" and table_choice.upper() == "E":
            while True:
                customer_id=input("請輸入客戶id \n")
                if customer_id=="":
                    customer_id=None
                    break
                check_bool,customer_id,check_result=check_internal_id_format(customer_id)
                if check_result !="customer_id":
                    print("客戶id格式不正確!")
                    continue
                else:
                    break
            
            customer_name=input("請輸入客戶姓名\n")
            if customer_name=="":
                customer_name=None
            customer_data = CustomerTableCRUD.read_customer_table(customer_id,customer_name)
            if not customer_data:
                customer_data=CustomerTableCRUD.customer_fuzzy_search(customer_name)
                print(customer_data)
            else:
                for customer in customer_data:
                    print(customer)

        elif function_choice == "1" and table_choice.upper() == "F":
            roles=RoleTableCRUD.read_role()
            print(roles)
            break
        elif function_choice == "1" and table_choice.upper() == "G":
            results=OrderTableCRUD.read_order_table()
            for result in results:
                print(result)
            break


#加速尋找: 以上為READ區；以下為INSERT區------------------

        elif function_choice == "2" and table_choice.upper() == "A":
            user_name = input("請輸入使用者名稱:\n")
            employee_no = input("請輸入使用者員工編號: \n")
            account = input("請輸入帳號:\n")
            password = input("請輸入密碼:\n")
            email = input("請輸入email: \n")
            insert_result = UserTableCRUD.insert_user(
                user_name, employee_no, account, password, email
            )
            print(insert_result)
            break
        elif function_choice == "2" and table_choice.upper() == "B":
            worker = input("請輸入工作者名稱\n")
            work_date = input("請輸入工作日期 \n")
            start_time = input("工作開始時間 \n")
            end_time = input("工作結束時間 \n")
            duration = input("工作持續時間\n")
            work_description = input("工作項目\n")
            recorder = input("紀錄者\n")
            insert_result = WorkingTimeTableCRUD.insert_work_time(
                worker,
                work_date,
                start_time,
                end_time,
                duration,
                work_description,
                recorder,
            )
            print(insert_result)
            break
        elif function_choice == "2" and table_choice.upper() == "C":
            employee_name = input("請輸入員工姓名\n")
            employee_no = input("請輸入員工編號\n")
            employee_role = input("請輸入員工職位\n")
            department = input("請輸入員工所屬部門\n")
            insert_result, message = EmployeeTableCRUD.insert_employee(
                employee_no, employee_name,department, employee_role
            )
            print(insert_result)
            print(message)
        elif function_choice == "2" and table_choice.upper() == "D":
            product_name = input("請輸入產品名稱\n")
            spec = input("請輸入產品規格\n")
            price = int(input("請輸入建議售價\n"))
            product_code = input("請輸入產品代號\n")
            message = ProductsTableCRUD.insert_product(
                product_name, spec, price, product_code
            )
            print(message)
            break
        elif function_choice == "2" and table_choice.upper() == "E":
            customer_name=input("請輸入客戶姓名:\n")
            while True:
                customer_phone=input("請輸入客戶電話號碼: \n")
                phone_check,_,message =check_phone(customer_phone)
                if not phone_check :
                    print(message)
                else:
                    print(f"號碼驗證成功:{message}")
                    break
            customer_address = input("請輸入客戶地址: \n")
            payment_method = input ("請選擇客戶習慣付款方式 1:Cash 2:Transfer\n")
            payment_dict={"1":"Cash","2":"Transfer"}
            
            if payment_method not in payment_dict.keys():
                raise KeyError("付款只有現金與匯款方式")
            transfer_account=None
            if payment_method == "2":
                while not transfer_account:
                    transfer_account=input("轉帳客戶請輸入預計匯款帳戶:")

            payment_method=payment_dict[payment_method]
            print(payment_method)
            creator = input("紀錄者\n")
            _,message=CustomerTableCRUD.insert_customer(customer_name,customer_phone,customer_address,creator,payment_method=payment_method,transfer_account=transfer_account)
            print(message)
            break
        elif function_choice == "2" and table_choice.upper() == "F":
            role=input("請輸入職位名稱:\n")
            department=input("請輸入部門名稱:\n")
            HRsys=input("請選擇此部門職位的人事系統權限等級 (0,1,2,3)\n")
            financesys=input("請選擇此部門職位的財務系統權限等級 (0,1,2,3)\n")
            ordersys=input("請選擇此部門職位的訂單系統權限等級 (0,1,2,3)\n")
            permission_levels=["0","1","2","3"]
            if any(x not in permission_levels for x in [HRsys,financesys,ordersys] ):
                print(f"請輸入許可的權限代號，{permission_levels}")
                break
            else:
                RoleTableCRUD.insert_role(role,department,int(HRsys),int(financesys),int(ordersys))
                print("資料存入成功")

            break
        elif function_choice == "2" and table_choice.upper() == "G":
            while True:
                product_code=input("請輸入產品編號: \n")
                # print(repr(product_code))
                result=ProductsTableCRUD.read_product_info(product_code)
                if result is None:
                    print("沒有此產品編號，請重新輸入")
                else:
                    confirm=input(f"請確認產品資訊:{result} 正確(Y) /錯誤(N) \n").upper()
                    if confirm =="Y":
                        break
            product_name=result["product_name"]
            print(product_name)
            product_spec=result["spec"]
            print(product_spec)
            qty=int(input("請輸入訂單數量\n"))
            while True:
                customer_id=input("請輸入客戶編號或客戶姓名\n")
                if customer_id[0]== "C" and customer_id[1]=="n":
                    result=CustomerTableCRUD.read_customer_table(customer_id)    
                else:
                    result=CustomerTableCRUD.read_customer_table(customer_name=customer_id)
                if result is None:
                    print("沒有此客戶編號/姓名，請重新輸入")
                else:
                    confirm=input(f"請確認客戶資訊:{result} \n 正確(Y) /錯誤(N) \n").upper()
                    if confirm =="Y":
                        break

            subtotal=int(input("請輸入總計貨款(不含運費)\n"))
            shipment_fee=int(input("請輸入運費\n"))
            receiver_name=input("請輸入收件人姓名:\n")
            receiver_phone=input("請輸入收件人電話:\n")
            boolean,phone,phonetype=check_phone(receiver_phone)
            if boolean:
                print(phone,phonetype)
            receiver_address=input("請輸入收件人地址:\n")
            create_by=input("請輸入員工編號:\n")
            # payment_method=input("請選擇付款方式 1:Cash 2:Transfer \n")
            result=OrderTableCRUD.insert_order_table(product_code,product_name,product_spec,qty,customer_id,subtotal,shipment_fee,receiver_name,receiver_phone,receiver_address,create_by)
            print(result)

            break
                    
#加速尋找: 以上為INSERT區；以下為UPDATE區

        elif function_choice == "3" and table_choice.upper() == "C":
            employee_no = input("請輸入員工編號\n")
            column = input("請輸入修改欄位\n")
            new_data = input("請輸入更新數值\n")
            if column != "" and column != "" and new_data != "":
                _, updated_message = EmployeeTableCRUD.update_employee_table(
                    employee_no, column, new_data
                )
                print(updated_message)
            else:
                print("三個欄位不能為空")
                sys.exit(0)
        elif function_choice == "3" and table_choice.upper() == "E":
            customer_id = input("請輸入客戶編號\n")
            column = input("請輸入修改欄位\n")
            new_data = input("請輸入更新數值\n")
            if customer_id != "" and column != "" and new_data != "":
                if column =="payment_method" and new_data == "Transfer":
                    transfer_account=input("請輸入轉帳帳戶\n")
                    _, updated_message = CustomerTableCRUD.update_customer(
                        customer_id, column, new_data
                    )
                    print(updated_message)
                    _, updated_message = CustomerTableCRUD.update_customer(
                        customer_id,'transfer_account', transfer_account
                    )
                    print(updated_message)
                elif column =="payment_method" and new_data not in ["Cash","Transfer"]:
                    print("修改付款方式的話不能只改付款方式欄位")
                    
                else:
                    _, updated_message = CustomerTableCRUD.update_customer(
                        customer_id, column, new_data
                    )
                    print(updated_message)
            else:
                print("三個欄位不能為空")
                sys.exit(0)
        elif function_choice == "3" and table_choice.upper() == "G":
            while True:
                order_id=input("請輸入欲更新的訂單編號: \n")
                order_info=OrderTableCRUD.read_order_table(order_id)
                if len(order_info) ==1:
                    print(order_info)
                    confirm=input("確認是否要修改這筆 Y/N \n")
                    if confirm.upper()=="Y":
                        break
                else:
                    choose=input(f"資料庫查無{order_id}的資料，繼續查詢? Y/N\n").upper()
                    if choose !="Y":
                        break
            while len(order_info)==1:
                update_choice=input("請選擇更新類別 1:訂單狀態更新(已出貨) 2:訂單狀態更新(已收款) 3.訂單狀態更新(訂單取消) U.訂單資料更新  0:放棄\n")
                if update_choice=="0":
                    break
                elif update_choice.upper() =="U":
                    continue
                elif update_choice =="1":
                    shipment_date=input("請輸入出貨日期\n")
                    update_result=OrderTableCRUD.order_shipping(order_id,shipment_date)
                    print(update_result)
                    break
                elif update_choice =="2":
                    payment_method=input("請輸入收款方式: 1:Cash  2: Transfer\n")
                    if payment_method=="1":
                        payment_method="Cash"
                        transfer_account=None
                    elif payment_method=="2":
                        payment_method="Transfer"
                        transfer_account=input("請輸入匯出帳戶\n")
                    else:
                        print("無該收款方式，取消輸入")
                        break
                    payment_reciving_date=input("請輸入收款日期:\n")
                    update_result=OrderTableCRUD.order_complete(order_id,payment_reciving_date,payment_method,transfer_account)
                    print(update_result)
                    break
                elif update_choice =="3":
                    break
                else:
                    print("訂單資料更新無此選項")
                    break
#加速尋找: 以上為UPDATE區；以下為DELETE區

        elif function_choice == "D" and table_choice.upper() == "B":
            rows = WorkingTimeTableCRUD.read_work_time_table()
            while len(rows) > 0:
                delect_row_id = int(input("刪除哪一筆id\n"))
                delete_result = WorkingTimeTableCRUD.delete_work_time(
                    delect_row_id
                )
                print(delete_result)
                continue_delete = input("繼續刪除? Y/N \n").upper()
                if continue_delete == "Y":
                    continue
                else:
                    break
            else:
                print("工時表格已無紀錄")
        elif function_choice == "D" and table_choice.upper() == "A":
            rows = UserTableCRUD.read_user_table()
            for row in rows:
                print(row)
            while len(rows) > 0:
                delect_row_id = int(input("刪除哪一筆id\n"))
                delete_result = UserTableCRUD.delete_user(delect_row_id)
                print(delete_result)
                continue_delete = input("繼續刪除? Y/N \n").upper()
                if continue_delete == "Y":
                    continue
                else:
                    break
            else:
                print("使用者表格已無紀錄")
        elif function_choice == "D" and table_choice.upper() == "D":
            rows = ProductsTableCRUD.read_products_table()
            for row in rows:
                print(row)
            while len(rows) > 0:
                delect_row_id = int(input("刪除哪一筆id\n"))
                delete_result = ProductsTableCRUD.delete_product(delect_row_id)
                print(delete_result)
                continue_delete = input("繼續刪除? Y/N \n").upper()
                if continue_delete == "Y":
                    continue
                else:
                    break
            else:
                print("產品規格售價表格已無紀錄")
        elif function_choice == "D" and table_choice.upper() == "C":
            rows = EmployeeTableCRUD.read_employee_table()
            for row in rows:
                print(row)
            while len(rows) > 0:
                delect_row_id = int(input("刪除哪一筆id\n"))
                delete_result = EmployeeTableCRUD.delete_employee(
                    delect_row_id
                )
                print(delete_result)
                continue_delete = input("繼續刪除? Y/N \n").upper()
                if continue_delete == "Y":
                    continue
                else:
                    break
            else:
                print("員工資料表格已無紀錄")
        elif function_choice == "D" and table_choice.upper() == "E":
            rows = CustomerTableCRUD.read_customer_table()
            if rows is None:
                break
            for row in rows:
                print(row)
            data_len=len(rows)
            while data_len > 0:
                delect_row_id = int(input("刪除哪一筆id\n"))
                delete_result = CustomerTableCRUD.delete_customer(
                    delect_row_id
                )
                print(delete_result)
                data_len -= 1
                continue_delete = input("繼續刪除? Y/N \n").upper()
                if continue_delete == "Y":
                    continue
                else:
                    break
            else:
                print("客戶表格已無紀錄")
        elif function_choice == "TOTAL" and table_choice.upper() == "B":
            data = WorkingTimeTableCRUD.read_work_time_total()
            print(data)
            break
        elif function_choice == "D" and table_choice.upper() == "F":
            rows = RoleTableCRUD.read_role()
            while len(rows) > 0:
                delect_row_id = int(input("刪除哪一筆id\n"))
                delete_result = RoleTableCRUD.delete_role(delect_row_id)
                print(delete_result)
                continue_delete = input("繼續刪除? Y/N \n").upper()
                if continue_delete == "Y":
                    continue
                else:
                    break
            else:
                print("工時表格已無紀錄")
        elif function_choice == "D" and table_choice.upper() == "G":
            rows = OrderTableCRUD.read_order_table()
            while len(rows) > 0:
                order_id = input("刪除哪一筆的訂單編號\n")
                bool,internal_id,id_type=check_internal_id_format(id)
                print(id_type)
                if id_type =="order_id":
                    delete_result = OrderTableCRUD.delete_order(order_id)
                    print(delete_result)
                    continue_delete = input("繼續刪除? Y/N \n").upper()
                    if continue_delete == "Y":
                        continue
                    else:
                        break
                else:
                    print("輸入格式非訂單編號，請重新輸入 \n")
            else:
                print("訂單表格已無紀錄")


#加速尋找: 以上為DELETE區；以下為測試區

        elif function_choice == "T" and table_choice.upper() == "F":
            employee_no="SHR07"
            tester=RoleTableCRUD.read_personal_permission(employee_no)
            print(tester)
            break

        elif function_choice == "T" and table_choice.upper() == "P":

            break

        elif function_choice =="T" and table_choice.upper()=="G":
            # delete_result=database_manager.delete_table("orders")
            delete_result="預防誤選，仙註解掉"
            print(delete_result)
        elif function_choice=="T" and table_choice.upper()=="E":
            result=OrderTableCRUD.order_fuzzy_search("林智")
            print(result)
        else:
            print("無效的選擇，請重新輸入。")
            break


if __name__ == "__main__":
    main()
    # boll=has_db_file()
    # # print(boll)
    # Excel_PATH_ABS=r"D:\從桌面移過來較無使用的檔案\藥劑刪減會議\不符合bluesign明細\逐月資料\整理Python\好事成雙\schema.xlsx"
    # customer_table=pd.read_excel(Excel_PATH_ABS,sheet_name="客戶資料表",engine="openpyxl",dtype={"customer_phone": str})
    # tester_phone=customer_table["customer_phone"]
    # print(tester_phone)
    # import datetime 
    # input_date=check_datetime_formuler("2024.8.6")
    # print(input_date)