import flet as ft
import random
import string
import time
import os
import qrcode
import base64
import csv
from datetime import datetime
from io import BytesIO

from services.household_service import (
    register_household,
    get_redemption_balance,
    load_households,
    households,
    save_households
)
from services.merchant_service import (
    register_merchant, 
    load_merchants, 
    merchants
)

def generate_multi_redeem_token(selected_data):
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    token = f"TXN-{random_str}"
    return token, selected_data

def save_redemption_records(transaction_id, household_id, merchant_id, voucher_details):
    """按照PNG文件格式要求保存核销记录"""
    os.makedirs("storage/redemptions", exist_ok=True)
    
    # 生成文件名（按小时）
    now = datetime.now()
    filename = f"storage/redemptions/Redeem{now.strftime('%Y%m%d%H')}.csv"
    
    # 检查文件是否存在，决定是否写入表头
    file_exists = os.path.exists(filename)
    
    # 为每个券生成独立记录
    record_number = 1
    total_records = len(voucher_details)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        if not file_exists:
            # 写入表头
            writer.writerow([
                "Transaction_ID",
                "Household_ID",
                "Merchant_ID",
                "Transaction_Date_Time",
                "Voucher_Code",
                "Denomination_Used",
                "Amount_Redeemed",
                "Payment_Status",
                "Remarks"
            ])
        
        for i, detail in enumerate(voucher_details):
            # 生成券码 - 使用家庭ID后8位
            household_num = ''.join(filter(str.isdigit, household_id))
            if len(household_num) >= 8:
                voucher_code = f"V{household_num[-8:].zfill(8)}"
            else:
                voucher_code = f"V{household_num.zfill(8)}"
            
            # 添加序列号后缀以区分同一交易的不同券
            voucher_code = f"{voucher_code}{i+1:03d}"
            
            # 确定备注
            if i == total_records - 1:
                remarks = "Final denomination used"
            else:
                remarks = str(record_number)
            
            # 写入记录
            writer.writerow([
                transaction_id,
                household_id,
                merchant_id,
                now.strftime("%Y%m%d%H%M%S"),
                voucher_code,
                f"${detail['denomination']}.00",
                f"${detail['total_value']}.00",
                "Completed",
                remarks
            ])
            
            record_number += 1
    
    return filename

def main(page: ft.Page):
    page.title = "CDC Mobile Portal"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO
    
    load_households()
    load_merchants()
    os.makedirs("tmp", exist_ok=True)
    os.makedirs("storage/redemptions", exist_ok=True)
    
    session = {
        "user_id": None,
        "role": None,
        "selected_vouchers": {}
    }

    def show_snack(text, color="blue"):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def logout():
        session["user_id"] = None
        session["role"] = None
        session["selected_vouchers"] = {}
        page.controls.clear()
        page.add(login_view())
        page.update()

    def login_view():
        user_id_input = ft.TextField(label="Enter ID (Household or Merchant)", width=350)
        
        def do_login(e):
            uid = user_id_input.value.strip()
            if not uid:
                show_snack("Please enter an ID", "red")
                return

            if uid in households:
                session.update({"user_id": uid, "role": "household"})
                household = households[uid]
                available_tranches = [t for t in household.TRANCHE_CONFIG.keys() 
                                    if t not in household.vouchers]
                
                if available_tranches:
                    claim_tranche_view(available_tranches)
                else:
                    household_dashboard()
            elif uid in merchants:
                session.update({"user_id": uid, "role": "merchant"})
                merchant_dashboard()
            else:
                show_snack("ID not found. Please register first.", "red")

        return ft.Column([
            ft.Container(height=50),
            ft.Text("CDC Voucher System", size=32, weight="bold", color="blue"),
            ft.Text("Login to continue", size=16, color="grey"),
            ft.Container(height=20),
            user_id_input,
            ft.ElevatedButton("Login", on_click=do_login, width=350, height=50),
            ft.TextButton("New Household? Register Here", on_click=lambda _: register_view())
        ], horizontal_alignment="center", spacing=10)

    def register_view():
        page.controls.clear()
        
        members_input = ft.TextField(label="Family Members (comma separated)", width=350)
        postal_input = ft.TextField(label="Postal Code", width=350)
        
        result_container = ft.Column(horizontal_alignment="center", spacing=10)

        def submit_registration(e):
            try:
                if not members_input.value or not postal_input.value:
                    show_snack("Please fill in all fields", "red")
                    return

                res, status = register_household({
                    "members": [m.strip() for m in members_input.value.split(",") if m.strip()],
                    "postal_code": postal_input.value
                })
                
                if status != 200:
                    raise Exception("Service Error")

                new_id = res.get("household_id")
                
                result_container.controls = [
                    ft.Container(
                        padding=20,
                        margin=ft.margin.only(top=20),
                        border_radius=10,
                        bgcolor="#ecfdf5",
                        border=ft.border.all(2, "#059669"),
                        content=ft.Column([
                            ft.Icon("check_circle", color="green", size=50),
                            ft.Text("Registration Successful!", size=20, weight="bold", color="green"),
                            ft.Divider(),
                            ft.Text("YOUR LOGIN ID:", size=14, weight="bold"),
                            ft.Text(new_id, size=40, weight="bold", color="black", selectable=True),
                            ft.Text("Please COPY this ID now!", color="red", italic=True),
                        ], horizontal_alignment="center")
                    ),
                    ft.ElevatedButton("Back to Login", on_click=lambda _: logout(), bgcolor="blue", color="white")
                ]
                page.update()

            except Exception as err:
                show_snack(f"Error: {str(err)}", "red")

        page.add(
            ft.AppBar(
                title=ft.Text("Register Household"),
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout())
            ),
            ft.Column([
                ft.Text("Enter details below", size=16),
                members_input,
                postal_input,
                ft.ElevatedButton("Register Now", on_click=submit_registration, width=350, height=50),
                result_container
            ], horizontal_alignment="center", spacing=20)
        )
        page.update()

    def claim_tranche_view(available_tranches):
        page.controls.clear()
        
        def claim_all_tranches(e):
            household = households[session["user_id"]]
            success_count = 0
            
            for tranche in available_tranches:
                success, message = household.claim_tranche(tranche)
                if success:
                    success_count += 1
            
            save_households()
            
            if success_count > 0:
                show_snack(f"Successfully claimed {success_count} batch(es)!", "green")
                time.sleep(1)
                household_dashboard()
            else:
                show_snack("Failed to claim vouchers", "red")

        def claim_single_tranche(tranche_name, e=None):
            household = households[session["user_id"]]
            success, message = household.claim_tranche(tranche_name)
            
            if success:
                save_households()
                
                show_snack(f"Successfully claimed {tranche_name}!", "green")
                time.sleep(1)
                
                remaining_tranches = [t for t in household.TRANCHE_CONFIG.keys() 
                                    if t not in household.vouchers]
                if remaining_tranches:
                    claim_tranche_view(remaining_tranches)
                else:
                    household_dashboard()
            else:
                show_snack(message, "red")

        tranche_cards = []
        for tranche_name in available_tranches:
            config = households[session["user_id"]].TRANCHE_CONFIG[tranche_name]
            total_value = sum(int(denom) * count for denom, count in config.items())
            
            card = ft.Container(
                padding=15,
                margin=ft.margin.only(bottom=10),
                bgcolor="#f0f9ff",
                border_radius=10,
                border=ft.border.all(1, "#e0e7ff"),
                content=ft.Column([
                    ft.Row([
                        ft.Text(tranche_name, size=18, weight="bold", color="blue"),
                        ft.Text(f"Total: ${total_value}", size=16, weight="bold")
                    ], alignment="spaceBetween"),
                    ft.Divider(height=1),
                    ft.Text("Vouchers included:", size=14, color="grey"),
                    ft.Row([
                        ft.Container(
                            padding=ft.padding.all(8),
                            bgcolor="white",
                            border_radius=5,
                            content=ft.Column([
                                ft.Text(f"${denom}", size=16, weight="bold", color="green"),
                                ft.Text(f"x{count}", size=14)
                            ], horizontal_alignment="center")
                        ) for denom, count in config.items()
                    ], wrap=True),
                    ft.ElevatedButton(
                        "Claim This Batch",
                        on_click=lambda e, tn=tranche_name: claim_single_tranche(tn, e),
                        width=200
                    )
                ], spacing=8)
            )
            tranche_cards.append(card)

        page.add(
            ft.AppBar(
                title=ft.Text("Claim Your Vouchers"),
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout())
            ),
            ft.Column([
                ft.Container(
                    padding=20,
                    bgcolor="#ecfdf5",
                    border_radius=10,
                    margin=ft.margin.all(15),
                    content=ft.Column([
                        ft.Icon("card_giftcard", size=40, color="green"),
                        ft.Text("Vouchers Available!", size=20, weight="bold", color="green"),
                        ft.Text(f"You have {len(available_tranches)} batch(es) to claim", size=14),
                    ], horizontal_alignment="center")
                ),
                *tranche_cards,
                ft.Container(height=10),
                ft.ElevatedButton(
                    "Claim All Batches",
                    on_click=claim_all_tranches,
                    width=350,
                    height=50,
                    bgcolor="blue",
                    color="white"
                ),
                ft.TextButton(
                    "Skip to Dashboard",
                    on_click=lambda _: household_dashboard()
                )
            ], scroll=ft.ScrollMode.AUTO, spacing=10)
        )
        page.update()

    def household_dashboard():
        page.controls.clear()
        bal, _ = get_redemption_balance(session["user_id"])
        
        household = households[session["user_id"]]
        available_tranches = [t for t in household.TRANCHE_CONFIG.keys() 
                            if t not in household.vouchers]
        
        vouchers_column = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO)
        summary_text = ft.Text("Total Selected: $0", size=18, weight="bold", color="blue")
        
        if available_tranches:
            reminder_bar = ft.Container(
                padding=10,
                bgcolor="#fffbeb",
                border_radius=5,
                margin=ft.margin.only(bottom=10),
                content=ft.Row([
                    ft.Icon("info", color="orange", size=20),
                    ft.Text(f"You have {len(available_tranches)} unclaimed batch(es)", size=14, expand=True),
                    ft.TextButton("Claim Now", on_click=lambda _: claim_tranche_view(available_tranches))
                ], alignment="center")
            )
            vouchers_column.controls.append(reminder_bar)
        
        def refresh_summary():
            total = sum(int(d) * c for d, c in session["selected_vouchers"].items())
            summary_text.value = f"Total Selected: ${total}"
            page.update()

        def update_count(denom, delta, max_limit, count_text):
            current = session["selected_vouchers"].get(denom, 0)
            new_val = current + delta
            
            if 0 <= new_val <= max_limit:
                session["selected_vouchers"][denom] = new_val
                count_text.value = str(new_val)
                refresh_summary()

        if "vouchers" in bal and bal["vouchers"]:
            for tranche, denoms in bal["vouchers"].items():
                vouchers_column.controls.append(ft.Container(
                    bgcolor="#f0f9ff", padding=10, border_radius=5,
                    content=ft.Text(f"Batch: {tranche}", weight="bold")
                ))
                
                for denom, max_count in denoms.items():
                    current_sel = session["selected_vouchers"].get(denom, 0)
                    count_display = ft.Text(str(current_sel), size=20, width=40, text_align="center")
                    
                    row = ft.Container(
                        padding=10, border=ft.border.all(1, "#e5e7eb"), border_radius=10,
                        content=ft.Row([
                            ft.Text(f"${denom}", size=24, weight="bold", width=60),
                            ft.Column([
                                ft.Text(f"Available: {max_count}", size=12, color="grey"),
                            ], expand=True),
                            ft.IconButton(icon="remove", on_click=lambda e, d=denom, m=max_count, t=count_display: update_count(d, -1, m, t)),
                            count_display,
                            ft.IconButton(icon="add", on_click=lambda e, d=denom, m=max_count, t=count_display: update_count(d, 1, m, t)),
                        ], alignment="spaceBetween")
                    )
                    vouchers_column.controls.append(row)
        else:
            vouchers_column.controls.append(
                ft.Container(
                    padding=30,
                    content=ft.Column([
                        ft.Icon("inbox", size=50, color="grey"),
                        ft.Text("No vouchers available", size=18, color="grey"),
                        ft.Text("Claim vouchers first to use them", size=14, color="grey"),
                        ft.ElevatedButton(
                            "Check Available Batches",
                            on_click=lambda _: claim_tranche_view(available_tranches) if available_tranches else show_snack("No batches available", "red"),
                            width=250
                        )
                    ], horizontal_alignment="center")
                )
            )

        def generate_qr(e):
            total = sum(int(d) * c for d, c in session["selected_vouchers"].items())
            if total == 0:
                show_snack("Please select at least one voucher", "red")
                return
            
            # 验证用户是否有足够的券
            for denom, count in session["selected_vouchers"].items():
                if count > 0:
                    found = False
                    for tranche, denoms in bal["vouchers"].items():
                        if denom in denoms and denoms[denom] >= count:
                            found = True
                            break
                    if not found:
                        show_snack(f"Insufficient ${denom} vouchers", "red")
                        return
            
            token, data = generate_multi_redeem_token(session["selected_vouchers"])
            
            # 存储token到household数据中
            households[session["user_id"]]["active_token"] = token
            households[session["user_id"]]["token_data"] = data
            save_households()
            
            # 生成二维码
            qr = qrcode.make(token)
            buffered = BytesIO()
            qr.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # 创建 QR 显示页面
            def qr_display_view():
                page.controls.clear()
                
                page.add(
                    ft.Column([
                        # 顶部栏
                        ft.Container(
                            height=60,
                            bgcolor="blue",
                            padding=ft.padding.only(left=15, right=15),
                            content=ft.Row([
                                ft.IconButton(
                                    icon="arrow_back",
                                    icon_color="white",
                                    on_click=lambda e: household_dashboard()
                                ),
                                ft.Text("Your QR Code", 
                                    size=22, 
                                    weight="bold", 
                                    color="white",
                                    expand=True),
                                ft.Container(width=48)  # 占位符
                            ], vertical_alignment="center")
                        ),
                        
                        # 主要内容
                        ft.Container(
                            expand=True,
                            alignment=ft.alignment.center,
                            content=ft.Column([
                                # 二维码区域
                                ft.Container(
                                    width=320,
                                    height=320,
                                    bgcolor="white",
                                    border=ft.border.all(3, "#4f46e5"),
                                    border_radius=15,
                                    padding=15,
                                    alignment=ft.alignment.center,
                                    content=ft.Image(
                                        src_base64=img_str,
                                        width=290,
                                        height=290,
                                        fit=ft.ImageFit.CONTAIN
                                    )
                                ),
                                
                                # 信息区域
                                ft.Container(
                                    padding=20,
                                    content=ft.Column([
                                        ft.Text(f"Total Value", size=14, color="grey"),
                                        ft.Text(f"${total}", size=36, weight="bold", color="green"),
                                        ft.Divider(height=20),
                                        ft.Text("Token", size=14, color="grey"),
                                        ft.Container(
                                            bgcolor="#f3f4f6",
                                            padding=10,
                                            border_radius=8,
                                            content=ft.Text(token, size=18, selectable=True)
                                        ),
                                        ft.Text("Show this QR code to the merchant", 
                                            size=14, italic=True, color="blue"),
                                    ], spacing=10, horizontal_alignment="center")
                                ),
                                
                                # 按钮
                                ft.Container(
                                    padding=20,
                                    content=ft.ElevatedButton(
                                        "Back to Vouchers",
                                        icon="arrow_back",
                                        on_click=lambda e: household_dashboard(),
                                        width=250,
                                        height=50,
                                        bgcolor="blue",
                                        color="white"
                                    )
                                )
                            ], horizontal_alignment="center")
                        )
                    ], spacing=0)
                )
                page.update()
            
            # 切换到 QR 显示页面
            qr_display_view()

        page.add(
            ft.AppBar(
                title=ft.Text("My Vouchers"),
                actions=[
                    ft.IconButton(icon="card_giftcard", tooltip="Claim Vouchers", 
                                on_click=lambda _: claim_tranche_view(available_tranches) if available_tranches else show_snack("All batches claimed", "blue")),
                    ft.IconButton(icon="logout", on_click=lambda _: logout())
                ]
            ),
            ft.Container(vouchers_column, expand=True), # 让列表可滚动
            ft.Container(
                padding=20, bgcolor="white", 
                border=ft.border.only(top=ft.BorderSide(1, "#eee")),
                content=ft.Column([
                    summary_text,
                    ft.Button("Generate QR Code", on_click=generate_qr, width=350, height=50)
                ], horizontal_alignment="center")
            )
        )
        page.update()

    def merchant_dashboard():
        page.controls.clear()
        
        token_input = ft.TextField(label="Scan QR or Enter Token", width=350, text_align="center")
        
        def process_txn(e):
            token_val = token_input.value.strip()
            if not token_val:
                show_snack("Please input a token", "red")
                return
            
            # 查找对应的家庭
            target_hid = None
            token_data = None
            
            for hid, h in households.items():
                if h.get("active_token") == token_val:
                    target_hid = hid
                    token_data = h.get("token_data")
                    break
            
            if not target_hid:
                show_snack("Invalid or Expired Token", "red")
                return
            
            # 计算总金额并准备券详情
            total_amt = 0
            voucher_details = []
            
            for denom, count in token_data.items():
                if count > 0:
                    denom_value = int(denom)
                    total_for_denom = denom_value * count
                    total_amt += total_for_denom
                    
                    voucher_details.append({
                        "denomination": denom,
                        "count": count,
                        "total_value": total_for_denom
                    })
            
            # 从家庭券中扣除
            household = households[target_hid]
            for denom, count in token_data.items():
                remaining = count
                for tranche, vouchers in household.vouchers.items():
                    if denom in vouchers and vouchers[denom] > 0:
                        deduct = min(vouchers[denom], remaining)
                        vouchers[denom] -= deduct
                        remaining -= deduct
                        if remaining == 0:
                            break
            
            # 清除已使用的token
            households[target_hid]["active_token"] = None
            
            # 保存家庭数据
            save_households()
            
            # 生成交易ID（格式：TX + 年月日时分秒）
            transaction_id = f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 保存核销记录
            saved_file = save_redemption_records(
                transaction_id,
                target_hid,
                session["user_id"],  # 商家ID
                voucher_details
            )
            
            # 显示成功对话框
            page.dialog = ft.AlertDialog(
                title=ft.Text("Transaction Success"),
                content=ft.Column([
                    ft.Icon("check_circle", color="green", size=60),
                    ft.Text(f"Collected: ${total_amt}", size=30, weight="bold"),
                    ft.Text(f"From Household: {target_hid}"),
                    ft.Divider(height=10),
                    ft.Text(f"Transaction ID: {transaction_id}", size=14, weight="bold"),
                    ft.Text(f"Records saved to:", size=12, color="grey"),
                    ft.Text(os.path.basename(saved_file), size=12, color="blue", selectable=True)
                ], height=280, tight=True, horizontal_alignment="center"),
                actions=[ft.TextButton("Close", on_click=lambda e: page.close_dialog())]
            )
            page.dialog.open = True
            
            # 清空输入框
            token_input.value = ""
            page.update()

        page.add(
            ft.AppBar(
                title=ft.Text("Merchant POS"),
                leading=ft.Icon("store"),
                actions=[ft.IconButton(icon="logout", on_click=lambda _: logout())]
            ),
            ft.Column([
                ft.Container(height=50),
                ft.Icon("qr_code_scanner", size=100, color="blue"),
                ft.Text("Ask customer to show QR Code", size=16),
                ft.Text("or enter token manually", size=14, color="grey"),
                ft.Container(height=20),
                token_input,
                ft.ElevatedButton("Process Payment", on_click=process_txn, width=350, height=60),
                ft.Container(height=20),
                ft.Text("Recent redemptions saved to:", size=12, color="grey"),
                ft.Text("storage/redemptions/", size=12, color="blue", selectable=True)
            ], horizontal_alignment="center")
        )
        page.update()

    page.add(login_view())

ft.app(target=main, assets_dir=".")