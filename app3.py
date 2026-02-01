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
    households,
    save_households
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
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 0
    
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
                # Check if household has any vouchers
                household = households[uid]
                has_vouchers = any(
                    any(count > 0 for count in tranche.values()) 
                    for tranche in household.get("vouchers", {}).values()
                )
                
                if has_vouchers:
                    household_dashboard()
                else:
                    claim_vouchers_view()
            elif uid in merchants:
                session.update({"user_id": uid, "role": "merchant"})
                merchant_dashboard()
            else:
                show_snack("ID not found. Please register first.", "red")

        # Professional logo header
        logo_header = ft.Container(
            width=350,
            padding=30,
            border_radius=15,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#3b82f6", "#2563eb"]
            ),
            content=ft.Column([
                # Logo icon
                ft.Container(
                    width=80,
                    height=80,
                    border_radius=40,
                    bgcolor="white",
                    content=ft.Text("🎫", size=45),
                    alignment=ft.alignment.center
                ),
                ft.Container(height=10),
                # App name
                ft.Text(
                    "CDC VOUCHER",
                    size=28,
                    weight="bold",
                    color="white",
                    text_align="center"
                ),
                ft.Text(
                    "Digital Redemption System",
                    size=14,
                    color="white",
                    opacity=0.9,
                    text_align="center"
                ),
            ], horizontal_alignment="center")
        )

        return ft.Column([
            ft.Container(height=40),
            logo_header,
            ft.Container(height=30),
            ft.Text("Welcome Back", size=24, weight="bold", color="#1f2937"),
            ft.Text("Login to continue", size=14, color="grey"),
            ft.Container(height=20),
            user_id_input,
            ft.ElevatedButton("Login", on_click=do_login, width=350, height=50, bgcolor="#3b82f6", color="white"),
            ft.TextButton("New Household? Register Here", on_click=lambda _: register_view())
        ], horizontal_alignment="center", spacing=10)

    # =========================
    # 2. 注册视图
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
                session.update({"user_id": new_id, "role": "household"})
                
                # 注册成功显示逻辑
                result_container.controls = [
                    ft.Container(
                        padding=20,
                        margin=ft.margin.only(top=20),
                        border_radius=10,
                        bgcolor="#ecfdf5",
                        border=ft.border.all(2, "#059669"),
                        width=350,
                        content=ft.Column([
                            ft.Icon("check_circle", color="green", size=50),
                            ft.Text("Registration Successful!", size=20, weight="bold", color="green"),
                            ft.Divider(),
                            ft.Text("YOUR LOGIN ID:", size=14, weight="bold"),
                            ft.Container(
                                bgcolor="#f3f4f6",
                                padding=15,
                                border_radius=8,
                                content=ft.Text(new_id, size=28, weight="bold", color="black", selectable=True)
                            ),
                            ft.Text("Please SAVE this ID now!", color="red", italic=True, size=12),
                            ft.Container(height=20),
                            ft.Text("Next Steps:", size=16, weight="bold"),
                            ft.ElevatedButton(
                                "Claim Your Vouchers", 
                                on_click=lambda _: claim_vouchers_view(),
                                bgcolor="blue",
                                color="white",
                                width=280,
                                height=50
                            )
                        ], horizontal_alignment="center")
                    )
                ]
                page.update()

            except Exception as err:
                show_snack(f"Error: {str(err)}", "red")

        page.add(
            ft.AppBar(
                title=ft.Row([
                    ft.Text("🎫", size=24),
                    ft.Text("Register Household", size=18, weight="bold")
                ], spacing=10),
                center_title=True,
                bgcolor="#3b82f6",
                color="white",
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout(), icon_color="white")
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
    # 3. 领取券视图 (Claim Vouchers) - IMPROVED UI
    # =========================
    def claim_vouchers_view():
        page.controls.clear()
        
        # Available voucher schemes
        schemes = {
            "Jan2026": {"2": 30, "5": 20, "10": 14},
            "Feb2026": {"2": 25, "5": 25, "10": 10},
        }
        
        def claim_scheme(scheme_name, vouchers):
            household = households[session["user_id"]]
            
            # Check if already claimed
            if scheme_name in household.get("vouchers", {}):
                show_snack(f"{scheme_name} already claimed!", "orange")
                return
            
            # Add vouchers to household
            if "vouchers" not in household:
                household["vouchers"] = {}
            
            household["vouchers"][scheme_name] = vouchers.copy()
            save_households()
            
            show_snack(f"Successfully claimed {scheme_name}!", "green")
            
            # Refresh the view
            claim_vouchers_view()
        
        # Build scheme cards
        household = households[session["user_id"]]
        existing_vouchers = household.get("vouchers", {})
        
        scheme_cards = ft.Column(spacing=15, horizontal_alignment="center")
        
        for scheme_name, vouchers in schemes.items():
            already_claimed = scheme_name in existing_vouchers
            
            # Calculate total value
            total_value = sum(int(d) * c for d, c in vouchers.items())
            
            # Create voucher denomination boxes
            voucher_boxes = ft.Row(
                spacing=8,
                wrap=True,
                alignment="center",
                controls=[
                    ft.Container(
                        padding=10,
                        border_radius=8,
                        bgcolor="#eff6ff",
                        border=ft.border.all(1, "#3b82f6"),
                        content=ft.Column([
                            ft.Text(f"${denom}", size=18, weight="bold", color="#1e40af"),
                            ft.Text(f"× {count}", size=12, color="grey")
                        ], horizontal_alignment="center", spacing=2, tight=True)
                    )
                    for denom, count in sorted(vouchers.items(), key=lambda x: int(x[0]))
                ]
            )
            
            card = ft.Container(
                padding=20,
                border_radius=10,
                bgcolor="#ffffff" if not already_claimed else "#f3f4f6",
                border=ft.border.all(2, "#3b82f6" if not already_claimed else "#9ca3af"),
                width=350,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(
                            "card_giftcard" if not already_claimed else "check_circle",
                            color="blue" if not already_claimed else "green",
                            size=40
                        ),
                        ft.Column([
                            ft.Text(scheme_name, size=20, weight="bold"),
                            ft.Text(f"Total Value: ${total_value}", size=14, color="grey")
                        ], spacing=2, expand=True)
                    ], alignment="start"),
                    ft.Divider(height=1, color="#e5e7eb"),
                    ft.Text("Includes:", size=12, weight="bold", color="#374151"),
                    voucher_boxes,
                    ft.Container(height=5),
                    ft.ElevatedButton(
                        "✓ Claimed" if already_claimed else "Claim Now",
                        on_click=lambda e, s=scheme_name, v=vouchers: claim_scheme(s, v),
                        bgcolor="grey" if already_claimed else "#3b82f6",
                        color="white",
                        width=310,
                        height=45,
                        disabled=already_claimed
                    )
                ], spacing=12, horizontal_alignment="center")
            )
            scheme_cards.controls.append(card)
        
        # Check if any vouchers claimed
        has_vouchers = len(existing_vouchers) > 0
        
        page.add(
            ft.AppBar(
                title=ft.Row([
                    ft.Text("🎫", size=24),
                    ft.Text("Claim Vouchers", size=18, weight="bold")
                ], spacing=10),
                center_title=True,
                bgcolor="#3b82f6",
                color="white",
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout(), icon_color="white"),
                actions=[ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")]
            ),
            ft.Column([
                ft.Container(
                    padding=20,
                    bgcolor="#eff6ff",
                    border_radius=10,
                    margin=10,
                    width=350,
                    content=ft.Column([
                        ft.Icon("info", color="blue", size=30),
                        ft.Text("Claim Your CDC Vouchers", size=18, weight="bold", text_align="center"),
                        ft.Text("Select schemes below to add vouchers to your account", 
                               size=12, color="grey", text_align="center")
                    ], horizontal_alignment="center", spacing=5)
                ),
                ft.Container(
                    content=scheme_cards,
                    padding=ft.padding.symmetric(vertical=10),
                    expand=True
                ),
                # Bottom action buttons
                ft.Container(
                    padding=20,
                    bgcolor="white",
                    border=ft.border.only(top=ft.BorderSide(1, "#eee")),
                    content=ft.Column([
                        ft.ElevatedButton(
                            "Go to My Vouchers",
                            on_click=lambda _: household_dashboard(),
                            bgcolor="#10b981",
                            color="white",
                            width=350,
                            height=50,
                            disabled=not has_vouchers
                        ),
                        ft.Text(
                            "Claim at least one scheme to continue" if not has_vouchers else f"You have {len(existing_vouchers)} scheme(s) claimed",
                            size=12,
                            color="grey" if not has_vouchers else "green",
                            text_align="center"
                        )
                    ], horizontal_alignment="center", spacing=10)
                )
            ], spacing=0, expand=True, horizontal_alignment="center")
        )
        page.update()

    # =========================
    # 4. 住户仪表盘 (选券逻辑)
    # =========================
    def household_dashboard():
        page.controls.clear()
        
        # Reload fresh data from file
        load_households()
        
        # Reset selected vouchers when entering dashboard
        session["selected_vouchers"] = {}
        
        bal, status = get_redemption_balance(session["user_id"])
        
        if status != 200:
            show_snack("Error loading balance", "red")
            return
        
        vouchers_column = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center")
        summary_text = ft.Text("Total Selected: $0", size=18, weight="bold", color="blue")
        
        # 刷新总金额
        def refresh_summary():
            total = sum(int(d) * c for d, c in session["selected_vouchers"].items())
            summary_text.value = f"Total Selected: ${total}"
            page.update()

        # 加减逻辑
        def update_count(denom, delta, max_limit, count_text):
            denom_str = str(denom)
            current = session["selected_vouchers"].get(denom_str, 0)
            new_val = current + delta
            
            if 0 <= new_val <= max_limit:
                if new_val == 0:
                    session["selected_vouchers"].pop(denom_str, None)
                else:
                    session["selected_vouchers"][denom_str] = new_val
                count_text.value = str(new_val)
                refresh_summary()
                page.update()

        # 构建列表
        voucher_data = bal.get("vouchers", {})
        
        if not voucher_data:
            vouchers_column.controls.append(
                ft.Container(
                    padding=40,
                    width=350,
                    content=ft.Column([
                        ft.Icon("inbox", size=80, color="grey"),
                        ft.Text("No vouchers available", size=18, color="grey"),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "Claim Vouchers",
                            on_click=lambda _: claim_vouchers_view(),
                            bgcolor="blue",
                            color="white",
                            width=200
                        )
                    ], horizontal_alignment="center")
                )
            )
        else:
            for tranche, denoms in voucher_data.items():
                vouchers_column.controls.append(ft.Container(
                    bgcolor="#f0f9ff", 
                    padding=10, 
                    border_radius=5,
                    width=350,
                    content=ft.Text(f"Batch: {tranche}", weight="bold", size=16, text_align="center")
                ))
                
                for denom, max_count in denoms.items():
                    denom_str = str(denom)
                    
                    if max_count == 0:
                        continue
                    
                    current_sel = session["selected_vouchers"].get(denom_str, 0)
                    count_display = ft.Text(str(current_sel), size=20, width=40, text_align="center")
                    
                    row = ft.Container(
                        padding=10, 
                        border=ft.border.all(1, "#e5e7eb"), 
                        border_radius=10,
                        bgcolor="white",
                        width=350,
                        content=ft.Row([
                            ft.Text(f"${denom}", size=24, weight="bold", width=60),
                            ft.Column([
                                ft.Text(f"Available: {max_count}", size=12, color="grey"),
                            ], expand=True),
                            ft.IconButton(
                                icon="remove", 
                                on_click=lambda e, d=denom_str, m=max_count, t=count_display: update_count(d, -1, m, t)
                            ),
                            count_display,
                            ft.IconButton(
                                icon="add", 
                                on_click=lambda e, d=denom_str, m=max_count, t=count_display: update_count(d, 1, m, t)
                            ),
                        ], alignment="spaceBetween")
                    )
                    vouchers_column.controls.append(row)

        # Container to hold the generated code display
        code_display_container = ft.Container()

        def generate_qr(e):
            selected = session["selected_vouchers"]
            
            if not selected or all(v == 0 for v in selected.values()):
                show_snack("Please select at least one voucher", "red")
                return
            
            total = sum(int(d) * c for d, c in selected.items())
            
            token, data = generate_multi_redeem_token(selected.copy())
            
            households[session["user_id"]]["active_token"] = token
            households[session["user_id"]]["token_data"] = data
            
            # 🔥 CRITICAL: Save to file so merchant app can see it!
            save_households()
            
            print(f"\n{'='*50}")
            print(f"GENERATED TOKEN: {token}")
            print(f"Total Amount: ${total}")
            print(f"✅ Token saved to households.json")
            print(f"{'='*50}\n")
            
            # Save QR to file
            qr_filename = f"{token}.png"
            qr_path = os.path.abspath(f"tmp/{qr_filename}")
            try:
                qr_img = qrcode.make(token)
                qr_img.save(qr_path)
                print(f"✅ QR code saved to: {qr_path}")
            except Exception as e:
                print(f"⚠️ QR code save failed: {e}")
            
            # Voucher breakdown text
            voucher_text = ", ".join([f"${d}×{c}" for d, c in sorted(selected.items(), key=lambda x: int(x[0]))])
            
            def copy_code(e):
                page.set_clipboard(token)
                show_snack("✓ Code copied!", "green")
            
            def close_code_display(e):
                code_display_container.content = None
                code_display_container.visible = False
                page.update()
            
            # Display code directly on the page (not in dialog)
            code_display_container.content = ft.Container(
                width=350,
                padding=20,
                bgcolor="white",
                border_radius=10,
                border=ft.border.all(2, "#3b82f6"),
                content=ft.Column([
                    # Header
                    ft.Row([
                        ft.Text("🎫 Redemption Code", size=18, weight="bold", expand=True),
                        ft.IconButton(icon="close", on_click=close_code_display, icon_size=20)
                    ]),
                    
                    ft.Divider(),
                    
                    # THE CODE - Big and visible
                    ft.Container(
                        bgcolor="#e3f2fd",
                        padding=20,
                        border_radius=8,
                        content=ft.Column([
                            ft.Text("Show this code to merchant:", size=12, color="grey"),
                            ft.Container(height=5),
                            ft.Text(token, size=36, weight="bold", selectable=True, color="#1976d2"),
                        ], horizontal_alignment="center")
                    ),
                    
                    ft.Container(height=10),
                    
                    # Copy button
                    ft.ElevatedButton(
                        "📋 Copy Code",
                        on_click=copy_code,
                        width=200,
                        height=40,
                        bgcolor="#1976d2",
                        color="white"
                    ),
                    
                    ft.Divider(),
                    
                    # Details
                    ft.Container(
                        bgcolor="#f5f5f5",
                        padding=15,
                        border_radius=8,
                        content=ft.Column([
                            ft.Text(f"Total: ${total}", size=20, weight="bold", color="#2e7d32"),
                            ft.Container(height=5),
                            ft.Text(f"Vouchers: {voucher_text}", size=12, color="grey"),
                        ], horizontal_alignment="center")
                    ),
                    
                    ft.Container(height=5),
                    
                    # Instructions
                    ft.Text(
                        "💡 Merchant will enter this code on their device",
                        size=11,
                        color="grey",
                        italic=True,
                        text_align="center"
                    )
                ], horizontal_alignment="center", spacing=10)
            )
            
            code_display_container.visible = True
            page.update()
            
            print(f"✅ Code displayed on page: {token}")

        page.add(
            ft.AppBar(
                title=ft.Row([
                    ft.Text("🎫", size=24),
                    ft.Text("My Vouchers", size=18, weight="bold")
                ], spacing=10),
                center_title=True,
                bgcolor="#3b82f6",
                color="white",
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: claim_vouchers_view(), icon_color="white"),
                actions=[
                    ft.IconButton(
                        icon="refresh", 
                        on_click=lambda _: household_dashboard(),
                        tooltip="Refresh Balance",
                        icon_color="white"
                    ),
                    ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")
                ]
            ),
            ft.Container(
                content=vouchers_column, 
                expand=True,
                padding=10,
                alignment=ft.alignment.top_center
            ),
            ft.Container(
                padding=20, 
                bgcolor="white", 
                border=ft.border.only(top=ft.BorderSide(1, "#eee")),
                content=ft.Column([
                    summary_text,
                    ft.ElevatedButton(
                        "Generate QR Code", 
                        on_click=generate_qr, 
                        width=350, 
                        height=50,
                        bgcolor="blue",
                        color="white"
                    ),
                    ft.Container(height=10),
                    code_display_container  # Add the code display container here
                ], horizontal_alignment="center")
            )
        )
        page.update()

    # =========================
    # 5. 商户仪表盘 (核销逻辑) - IMPROVED UI
    # =========================
    def merchant_dashboard():
        page.controls.clear()
        
        token_input = ft.TextField(
            label="",
            width=350,
            text_align="center",
            hint_text="Enter redemption code",
            text_size=20,
            height=70,
            border_color="#3b82f6",
            focused_border_color="#1e40af",
            prefix_text="CODE: "
        )
        
        def process_txn(e):
            token_val = token_input.value.strip()
            if not token_val:
                show_snack("Please enter a token", "red")
                return
            
            target_hid = None
            token_data = None
            
            for hid, h in households.items():
                if h.get("active_token") == token_val:
                    target_hid = hid
                    token_data = h.get("token_data")
                    break
            
            if not target_hid or not token_data:
                show_snack("Invalid or Expired Token", "red")
                return
            
            total_amt = sum(int(d) * c for d, c in token_data.items())
            
            household = households[target_hid]
            for denom, count in token_data.items():
                for tranche in household.get("vouchers", {}).values():
                    if denom in tranche:
                        tranche[denom] = max(0, tranche[denom] - count)
                        break
            
            households[target_hid]["active_token"] = None
            households[target_hid]["token_data"] = None
            save_households()
            
            # Create voucher boxes
            voucher_boxes = []
            for denom, count in sorted(token_data.items(), key=lambda x: int(x[0])):
                voucher_boxes.append(
                    ft.Container(
                        padding=10,
                        border_radius=8,
                        bgcolor="#dbeafe",
                        border=ft.border.all(1, "#3b82f6"),
                        content=ft.Column([
                            ft.Text(f"${denom}", size=20, weight="bold", color="#1e40af"),
                            ft.Text(f"× {count}", size=12, color="grey")
                        ], horizontal_alignment="center", spacing=2, tight=True)
                    )
                )
            
            def close_success(e):
                page.dialog.open = False
                token_input.value = ""
                page.update()
            
            page.dialog = ft.AlertDialog(
                title=ft.Text("✅ Payment Successful", text_align="center", size=22, weight="bold", color="#059669"),
                content=ft.Container(
                    width=320,
                    content=ft.Column([
                        ft.Icon("check_circle", color="green", size=80),
                        
                        ft.Container(height=10),
                        
                        # Amount
                        ft.Container(
                            padding=20,
                            bgcolor="#ecfdf5",
                            border_radius=10,
                            border=ft.border.all(2, "#10b981"),
                            content=ft.Column([
                                ft.Text("Total Amount", size=14, color="#065f46"),
                                ft.Text(f"${total_amt}", size=48, weight="bold", color="#059669")
                            ], horizontal_alignment="center", spacing=5)
                        ),
                        
                        ft.Container(height=10),
                        
                        # Vouchers breakdown
                        ft.Container(
                            padding=15,
                            bgcolor="#f9fafb",
                            border_radius=8,
                            content=ft.Column([
                                ft.Text("Vouchers Redeemed:", size=12, weight="bold", color="#374151"),
                                ft.Row(
                                    controls=voucher_boxes,
                                    spacing=8,
                                    wrap=True,
                                    alignment="center"
                                )
                            ], spacing=10, horizontal_alignment="center")
                        ),
                        
                        ft.Container(height=5),
                        
                        # Transaction details
                        ft.Container(
                            padding=10,
                            bgcolor="#fef3c7",
                            border_radius=6,
                            content=ft.Column([
                                ft.Text("Transaction Completed", size=10, color="#92400e", weight="bold"),
                                ft.Text(f"Household: {target_hid[:12]}...", size=10, color="#92400e")
                            ], spacing=3, horizontal_alignment="center")
                        )
                    ], spacing=8, horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)
                ),
                actions=[
                    ft.Container(
                        content=ft.ElevatedButton(
                            "Done",
                            on_click=close_success,
                            bgcolor="#10b981",
                            color="white",
                            width=280,
                            height=50
                        ),
                        alignment=ft.alignment.center
                    )
                ],
                actions_alignment="center"
            )
            page.dialog.open = True
            page.update()

        page.add(
            ft.AppBar(
                title=ft.Text("Merchant POS"),
                center_title=True,
                leading=ft.Icon("store"),
                actions=[ft.IconButton(icon="logout", on_click=lambda _: logout())]
            ),
            ft.Column([
                ft.Container(height=20),
                
                # Info card
                ft.Container(
                    padding=20,
                    bgcolor="#eff6ff",
                    border_radius=10,
                    margin=10,
                    width=350,
                    content=ft.Column([
                        ft.Icon("qr_code_scanner", size=60, color="#3b82f6"),
                        ft.Text("Customer Redemption", size=18, weight="bold", color="#1e40af"),
                        ft.Text("Enter code shown by customer", size=12, color="grey")
                    ], horizontal_alignment="center", spacing=8)
                ),
                
                ft.Container(height=10),
                
                # Token input with label
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10),
                    content=ft.Column([
                        ft.Text("Redemption Code:", size=14, weight="bold", color="#374151"),
                        token_input
                    ], spacing=5)
                ),
                
                # Process button
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10),
                    content=ft.ElevatedButton(
                        "💳 Process Payment", 
                        on_click=process_txn, 
                        width=350, 
                        height=60,
                        bgcolor="#10b981",
                        color="white"
                    )
                ),
                
                ft.Container(height=10),
                
                # Help text
                ft.Container(
                    padding=10,
                    width=350,
                    content=ft.Text(
                        "Customer will show a code like: TXN-ABC123",
                        size=11,
                        color="grey",
                        italic=True,
                        text_align="center"
                    )
                )
            ], spacing=10, horizontal_alignment="center")
        )
        page.update()

    # 启动程序
    page.add(login_view())

# Run in desktop mode on port 8550
print("\n" + "="*50)
print("🏠 HOUSEHOLD APP RUNNING")
print("="*50)
print("Access at: http://localhost:8550")
print("Press Ctrl+C to stop")
print("="*50 + "\n")

ft.app(target=main, assets_dir="tmp", port=8550)