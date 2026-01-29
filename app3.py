import flet as ft
import random
import string
import time
import os
import qrcode

# 确保这几个 Service 文件存在且代码正确 (使用之前修复过的版本)
from services.household_service import (
    register_household,
    get_redemption_balance,
    load_households,
    households
)
from services.merchant_service import (
    register_merchant, 
    load_merchants, 
    merchants
)

# =========================
# 辅助函数
# =========================

def generate_multi_redeem_token(selected_data):
    """生成包含多种面额信息的 Token"""
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    token = f"TXN-{random_str}"
    return token, selected_data

# =========================
# 主程序
# =========================
def main(page: ft.Page):
    page.title = "CDC Mobile Portal"
    page.theme_mode = ft.ThemeMode.LIGHT
    # 模拟手机尺寸，方便调试
    page.window_width = 400
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO
    
    # 初始化数据
    load_households()
    load_merchants()
    os.makedirs("tmp", exist_ok=True)
    
    # 全局 Session 状态
    session = {
        "user_id": None,
        "role": None,
        "selected_vouchers": {} # 格式: { denomination: count }
    }

    def show_snack(text, color="blue"):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def logout():
        session.clear()
        session["selected_vouchers"] = {}
        page.controls.clear()
        page.add(login_view())
        page.update()

    # =========================
    # 1. 登录视图
    # =========================
    def login_view():
        user_id_input = ft.TextField(label="Enter ID (Household or Merchant)", width=350)
        
        def do_login(e):
            uid = user_id_input.value.strip()
            if not uid:
                show_snack("Please enter an ID", "red")
                return

            if uid in households:
                session.update({"user_id": uid, "role": "household"})
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

    # =========================
    # 2. 注册视图 (已修复显示问题)
    # =========================
    def register_view():
        page.controls.clear()
        
        members_input = ft.TextField(label="Family Members (comma separated)", width=350)
        postal_input = ft.TextField(label="Postal Code", width=350)
        
        # 结果容器
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
                
                # 注册成功显示逻辑
                result_container.controls = [
                    ft.Container(
                        padding=20,
                        margin=ft.margin.only(top=20),
                        border_radius=10,
                        bgcolor="#ecfdf5",
                        border=ft.border.all(2, "#059669"),
                        content=ft.Column([
                            # 修复：直接使用字符串图标名
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
                # 修复：使用字符串 "arrow_back"
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

    # =========================
    # 3. 住户仪表盘 (选券逻辑)
    # =========================
    def household_dashboard():
        page.controls.clear()
        bal, _ = get_redemption_balance(session["user_id"])
        
        vouchers_column = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO)
        summary_text = ft.Text("Total Selected: $0", size=18, weight="bold", color="blue")
        
        # 刷新总金额
        def refresh_summary():
            total = sum(int(d) * c for d, c in session["selected_vouchers"].items())
            summary_text.value = f"Total Selected: ${total}"
            page.update()

        # 加减逻辑
        def update_count(denom, delta, max_limit, count_text):
            current = session["selected_vouchers"].get(denom, 0)
            new_val = current + delta
            
            if 0 <= new_val <= max_limit:
                session["selected_vouchers"][denom] = new_val
                count_text.value = str(new_val) # 更新界面数字
                refresh_summary()

        # 构建列表
        if "vouchers" in bal:
            for tranche, denoms in bal["vouchers"].items():
                vouchers_column.controls.append(ft.Container(
                    bgcolor="#f0f9ff", padding=10, border_radius=5,
                    content=ft.Text(f"Batch: {tranche}", weight="bold")
                ))
                
                for denom, max_count in denoms.items():
                    # 当前选择的数量
                    current_sel = session["selected_vouchers"].get(denom, 0)
                    count_display = ft.Text(str(current_sel), size=20, width=40, text_align="center")
                    
                    # 每一行的 UI
                    row = ft.Container(
                        padding=10, border=ft.border.all(1, "#e5e7eb"), border_radius=10,
                        content=ft.Row([
                            ft.Text(f"${denom}", size=24, weight="bold", width=60),
                            ft.Column([
                                ft.Text(f"Available: {max_count}", size=12, color="grey"),
                            ], expand=True),
                            # 修复：使用字符串 "remove" 和 "add"
                            ft.IconButton(icon="remove", on_click=lambda e, d=denom, m=max_count, t=count_display: update_count(d, -1, m, t)),
                            count_display,
                            ft.IconButton(icon="add", on_click=lambda e, d=denom, m=max_count, t=count_display: update_count(d, 1, m, t)),
                        ], alignment="spaceBetween")
                    )
                    vouchers_column.controls.append(row)

        def generate_qr(e):
            total = sum(int(d) * c for d, c in session["selected_vouchers"].items())
            print(total)
            if total == 0:
                show_snack("Please select at least one voucher", "red")
                return
            
            # 生成 Token
            token, data = generate_multi_redeem_token(session["selected_vouchers"])
            print(token)
            
            # 保存 Token 到住户数据 (内存中模拟)
            households[session["user_id"]].update({
                "active_token": token,
                "token_data": data
            })
            
            # 生成二维码图片
            qr_path = f"tmp/{token}.png"
            img = qrcode.make(token)
            img.save(qr_path)
            
            # 弹窗显示 QR
            page.dialog = ft.AlertDialog(
                title=ft.Text("Scan to Redeem"),
                content=ft.Column([
                    ft.Image(src=qr_path, width=200, height=200),
                    ft.Text(f"Value: ${total}", size=20, weight="bold"),
                    ft.Container(
                        bgcolor="#eee", padding=10, border_radius=5,
                        content=ft.Text(token, size=24, weight="bold", selectable=True)
                    ),
                    ft.Text("Show this to Merchant", italic=True)
                ], height=350, tight=True, horizontal_alignment="center")
            )
            page.dialog.open = True
            page.update()

        page.add(
            ft.AppBar(
                title=ft.Text("My Vouchers"),
                # 修复：使用字符串 "logout"
                actions=[ft.IconButton(icon="logout", on_click=lambda _: logout())]
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

    # =========================
    # 4. 商户仪表盘 (核销逻辑)
    # =========================
    def merchant_dashboard():
        page.controls.clear()
        
        token_input = ft.TextField(label="Scan QR or Enter Token", width=350, text_align="center")
        
        def process_txn(e):
            token_val = token_input.value.strip()
            if not token_val:
                show_snack("Please input a token", "red")
                return
            
            # 查找匹配的住户
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
            
            # 执行核销 (模拟)
            total_amt = sum(int(d) * c for d, c in token_data.items())
            
            # 清除 Token 防止二次使用
            households[target_hid]["active_token"] = None
            
            # 成功反馈
            page.dialog = ft.AlertDialog(
                title=ft.Text("Transaction Success"),
                content=ft.Column([
                    # 修复：直接使用字符串图标
                    ft.Icon("check_circle", color="green", size=60),
                    ft.Text(f"Collected: ${total_amt}", size=30, weight="bold"),
                    ft.Text(f"From Household: {target_hid}")
                ], height=200, tight=True, horizontal_alignment="center"),
                actions=[ft.TextButton("Close", on_click=lambda e: page.close_dialog())]
            )
            page.dialog.open = True
            token_input.value = "" # 清空输入框
            page.update()

        page.add(
            ft.AppBar(
                title=ft.Text("Merchant POS"),
                leading=ft.Icon("store"), # 修复：字符串图标
                actions=[ft.IconButton(icon="logout", on_click=lambda _: logout())]
            ),
            ft.Column([
                ft.Container(height=50),
                # 修复：字符串图标
                ft.Icon("qr_code_scanner", size=100, color="blue"),
                ft.Text("Ask customer to show QR Code", size=16),
                ft.Container(height=20),
                token_input,
                ft.ElevatedButton("Process Payment", on_click=process_txn, width=350, height=60)
            ], horizontal_alignment="center")
        )

    # 启动程序
    page.add(login_view())

ft.app(target=main, assets_dir="tmp")