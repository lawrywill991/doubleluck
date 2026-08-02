import sys
# print(sys.path)
from SQLmaintain import EmployeeTableCRUD,UserTableCRUD,WorkingTimeTableCRUD,ProductsTableCRUD,CustomerTableCRUD
from SQLmaintain import database_manager,check_phone,DataTransfer

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
                "validation"
            ]
            if set(tables) != set(necessary_tables):
                table_choice = input(
                    "目前還少table，請選擇建立：A.使用者資料表 B.工作時間資料表 c.員工資料表 D.職位列表 E.產品規格售價表 F:顧客資料表 G:驗證資料\n"
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
                    EmployeeTableCRUD.create_role_table()
                    print("職位表已創建成功!")
                    break
                elif table_choice =="G":
                    relation=input("請輸入關係: \n")
                    name= input("請輸入人名:\n")
                    UserTableCRUD.validation_table_build()
                    result=UserTableCRUD.validation_data_build(relation,name)
                    print(result)
                elif table_choice == "F":
                    CustomerTableCRUD.create_customer_table()
                    print("顧客資料表已創建成功!")
                else:
                    print("暫無預設表格可輸入，請聯繫程式作者")
                    break
            table_deal = input(
                "請輸入表格操作A.查表格欄位與設定 B.刪除整個表格 C.加入Trigger 0.退出\n"
            ).upper()
            if table_deal == "0":
                print("退出db_manager")
                continue
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

            else:
                print("查無表格名稱或，請重新操作")
                break

            # if table_deal=="B":

            break
        table_choice = input(
            "請選擇要操作的資料表：A.使用者資料表 B.工作時間資料表 C.員工資料表 D:產品規格表 E:客戶資料表\n"
        )
        if function_choice == "1" and table_choice.upper() == "A":
            data = UserTableCRUD.read_user_table()
            for user in data:
                print(user)
            break  # 一次插入一筆就好(先別嫌煩)
        elif function_choice == "1" and table_choice.upper() == "B":
            worker = input("請輸入查詢對象 Enter=明細全查 \n")
            full_record = input("請輸入是否不過濾日期 Y/N \n").upper()
            _, employee_data = EmployeeTableCRUD.read_employee_table()
            employee_name_list = (
                DataTransfer(employee_data)
                .to_worker_dicts(nick_name=False)
                .values()
            )
            # print(employee_name_list)
            if worker == "" and full_record != "Y":
                worker = None
                work_records = WorkingTimeTableCRUD.read_work_time_table()
            elif worker == "" and full_record == "Y":
                worker = None
                work_records = WorkingTimeTableCRUD.read_work_time_table(
                    full_record=True
                )
            elif worker in employee_name_list and full_record == "Y":
                work_records = WorkingTimeTableCRUD.read_work_time_table(
                    worker, full_record=True
                )
            elif worker in employee_name_list and full_record != "Y":
                work_records = WorkingTimeTableCRUD.read_work_time_table(
                    worker
                )
            else:
                raise KeyError(f"{worker}not in workers")
            for work_record in work_records:
                print(work_record)
            # ----以下是對DataTransfer 類別的方法測試用----
            # test=DataTransfer(work_records)
            # keys=test.get_keys()
            # print(keys)
            # duration=test.get_values(key='duration')
            # print(duration)

            # all_series=test.get_all_value_series()
            # print(all_series)

            # total_duration = test.get_duration_sum()
            # print(total_duration)
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
            customer_data = CustomerTableCRUD.read_customer_table()
            if not customer_data:
                print(customer_data)
            else:
                for customer in customer_data:
                    print(customer)
            
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
            insert_result, message = EmployeeTableCRUD.insert_employee(
                employee_no, employee_name, employee_role
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
        elif function_choice == "T" and table_choice.upper() == "A":
            # customer_id='Cn26-001'
            # customer_name='林家慧'
            # result=CustomerTableCRUD.read_customer_table(customer_id=customer_id)
            # # print(result)
            # print(result)
            ##----
            # now=datetime.now()
            # print(now)
            #-----------
            account = input("請輸入帳戶:\n")
            password= input("請輸入密碼:\n")
            login_bool,data=UserTableCRUD.login_check(account,password)
            print(login_bool)
            print(data)
            break

        elif function_choice == "T" and table_choice.upper() == "P":
            # result=UserTableCRUD.validation_infomations()
            # print(result)
            workers = EmployeeTableCRUD.read_employee_for_flask()
            print(workers)
            # worker_dicts = DataTransfer(workers_data).to_worker_dicts()
            break

        else:
            print("無效的選擇，請重新輸入。")
            break


if __name__ == "__main__":
    main()
    # boll=has_db_file()
    # print(boll)
