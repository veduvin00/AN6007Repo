"""
CDC Household App - API Version
EXACT UI from original app3.py, just using API calls
"""
import flet as ft
import time
import threading
from datetime import datetime

from api_client import api_client

def main(page: ft.Page):
    page.title = "CDC Household App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 0
    
    if not api_client.check_connection():
        page.add(ft.Text("❌ Cannot connect to API. Run: python app.py", color="red"))
        page.update()
        return
    
    session = {"user_id": None, "selected_vouchers": {}}

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

    # LOGIN VIEW
    def login_view():
        user_id_input = ft.TextField(label="Household ID", width=350, prefix_icon="home")
        
        def do_login(e):
            uid = user_id_input.value.strip()
            if not uid:
                show_snack("Please enter an ID", "red")
                return

            response, status = api_client.get_balance(uid)
            
            if status == 200:
                session["user_id"] = uid
                vouchers = response.get("vouchers", {})
                has_vouchers = any(any(count > 0 for count in tranche.values()) for tranche in vouchers.values())
                
                if has_vouchers:
                    household_dashboard()
                else:
                    claim_vouchers_view()
            else:
                show_snack("ID not found. Please register first.", "red")

        logo_header = ft.Container(
            width=350, padding=30, border_radius=15,
            gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=["#3b82f6", "#2563eb"]),
            content=ft.Column([
                ft.Container(width=80, height=80, border_radius=40, bgcolor="white", content=ft.Text("🎫", size=45), alignment=ft.alignment.center),
                ft.Container(height=10),
                ft.Text("CDC VOUCHER", size=28, weight="bold", color="white", text_align="center"),
                ft.Text("Digital Redemption System", size=14, color="white", opacity=0.9, text_align="center"),
            ], horizontal_alignment="center")
        )

        return ft.Column([
            ft.Container(height=40), logo_header, ft.Container(height=30),
            ft.Text("Welcome Back", size=24, weight="bold", color="#1f2937"),
            ft.Text("Login to continue", size=14, color="grey"), ft.Container(height=20), user_id_input,
            ft.ElevatedButton("Login", on_click=do_login, width=350, height=50, bgcolor="#3b82f6", color="white"),
            ft.TextButton("New Household? Register Here", on_click=lambda _: register_view())
        ], horizontal_alignment="center", spacing=10)

    # REGISTER VIEW
    def register_view():
        page.controls.clear()
        members_input = ft.TextField(label="Family Members (comma separated)", width=350)
        postal_input = ft.TextField(label="Postal Code", width=350)
        result_container = ft.Column(horizontal_alignment="center", spacing=10)

        def submit_registration(e):
            if not members_input.value or not postal_input.value:
                show_snack("Please fill in all fields", "red")
                return

            members = [m.strip() for m in members_input.value.split(",") if m.strip()]
            response, status = api_client.register_household(members, postal_input.value)
            
            if status == 200:
                new_id = response.get("household_id")
                session["user_id"] = new_id
                result_container.controls = [
                    ft.Container(padding=20, margin=ft.margin.only(top=20), border_radius=10,
                               bgcolor="#ecfdf5", border=ft.border.all(2, "#059669"), width=350,
                               content=ft.Column([
                                   ft.Icon("check_circle", color="green", size=50),
                                   ft.Text("Registration Successful!", size=20, weight="bold", color="green"),
                                   ft.Divider(),
                                   ft.Text("YOUR LOGIN ID:", size=14, weight="bold"),
                                   ft.Container(bgcolor="#f3f4f6", padding=15, border_radius=8,
                                              content=ft.Text(new_id, size=28, weight="bold", color="black", selectable=True)),
                                   ft.Text("Please SAVE this ID now!", color="red", italic=True, size=12),
                                   ft.Container(height=20),
                                   ft.ElevatedButton("Claim Your Vouchers", on_click=lambda _: claim_vouchers_view(),
                                                   bgcolor="blue", color="white", width=280, height=50)
                               ], horizontal_alignment="center"))
                ]
            else:
                show_snack(f"Error: {response.get('error', 'Failed')}", "red")
            page.update()

        page.add(
            ft.AppBar(title=ft.Row([ft.Text("🎫", size=24), ft.Text("Register Household", size=18, weight="bold")], spacing=10),
                     center_title=True, bgcolor="#3b82f6", color="white",
                     leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout(), icon_color="white")),
            ft.Column([ft.Text("Enter details below", size=16), members_input, postal_input,
                      ft.ElevatedButton("Register Now", on_click=submit_registration, width=350, height=50),
                      result_container], horizontal_alignment="center", spacing=20)
        )
        page.update()

    # CLAIM VOUCHERS VIEW - EXACT ORIGINAL DESIGN
    def claim_vouchers_view():
        page.controls.clear()
        
        schemes = {
            "Jan2026": {"2": 30, "5": 20, "10": 14},
            "Feb2026": {"2": 35, "5": 25, "10": 18},
        }
        
        def claim_scheme(scheme_name, vouchers):
            # API call instead of direct file access
            print(f"\n🔍 Claiming: {scheme_name}")
            print(f"User ID: {session['user_id']}")
            
            response, status = api_client.claim_vouchers(session["user_id"], scheme_name)
            
            print(f"Response: Status={status}, Data={response}")
            
            if status == 200:
                show_snack(f"Successfully claimed {scheme_name}!", "green")
                claim_vouchers_view()  # Refresh
            else:
                error = response.get("error", "Failed")
                if "already" in error.lower():
                    show_snack(f"{scheme_name} already claimed!", "orange")
                else:
                    show_snack(f"Error: {error}", "red")
        
        # Get current claimed vouchers
        response, status = api_client.get_balance(session["user_id"])
        existing_vouchers = response.get("vouchers", {}) if status == 200 else {}
        
        scheme_cards = ft.Column(spacing=15, horizontal_alignment="center")
        
        for scheme_name, vouchers in schemes.items():
            already_claimed = scheme_name in existing_vouchers
            total_value = sum(int(d) * c for d, c in vouchers.items())
            
            voucher_boxes = ft.Row(
                spacing=8, wrap=True, alignment="center",
                controls=[
                    ft.Container(
                        padding=10, border_radius=8, bgcolor="#eff6ff",
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
                padding=20, border_radius=10, width=350,
                bgcolor="#ffffff" if not already_claimed else "#f3f4f6",
                border=ft.border.all(2, "#3b82f6" if not already_claimed else "#9ca3af"),
                content=ft.Column([
                    ft.Row([
                        ft.Icon("card_giftcard" if not already_claimed else "check_circle",
                               color="blue" if not already_claimed else "green", size=40),
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
                        color="white", width=310, height=45,
                        disabled=already_claimed
                    )
                ], spacing=12, horizontal_alignment="center")
            )
            scheme_cards.controls.append(card)
        
        has_vouchers = len(existing_vouchers) > 0
        
        page.add(
            ft.AppBar(
                title=ft.Row([ft.Text("🎫", size=24), ft.Text("Claim Vouchers", size=18, weight="bold")], spacing=10),
                center_title=True, bgcolor="#3b82f6", color="white",
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout(), icon_color="white"),
                actions=[ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")]
            ),
            ft.Column([
                ft.Container(
                    padding=20, bgcolor="#eff6ff", border_radius=10, margin=10, width=350,
                    content=ft.Column([
                        ft.Icon("info", color="blue", size=30),
                        ft.Text("Claim Your CDC Vouchers", size=18, weight="bold", text_align="center"),
                        ft.Text("Select schemes below to add vouchers to your account", 
                               size=12, color="grey", text_align="center")
                    ], horizontal_alignment="center", spacing=5)
                ),
                ft.Container(content=scheme_cards, padding=ft.padding.symmetric(vertical=10), expand=True),
                ft.Container(
                    padding=20, bgcolor="white", border=ft.border.only(top=ft.BorderSide(1, "#eee")),
                    content=ft.Column([
                        ft.ElevatedButton("Go to My Vouchers", on_click=lambda _: household_dashboard(),
                                        bgcolor="#10b981", color="white", width=350, height=50,
                                        disabled=not has_vouchers),
                        ft.Text(
                            "Claim at least one scheme to continue" if not has_vouchers 
                            else f"You have {len(existing_vouchers)} scheme(s) claimed",
                            size=12, color="grey" if not has_vouchers else "green", text_align="center"
                        )
                    ], horizontal_alignment="center", spacing=10)
                )
            ], expand=True, scroll=ft.ScrollMode.AUTO)
        )
        page.update()

    # TRANSACTION HISTORY
    def transaction_history_view():
        page.controls.clear()
        
        response, status = api_client.get_transactions(session["user_id"], 50)
        transactions = response.get("transactions", []) if status == 200 else []
        
        page.add(
            ft.AppBar(
                title=ft.Row([ft.Text("📜", size=24), ft.Text("Transaction History", size=18, weight="bold")], spacing=10),
                center_title=True, bgcolor="#3b82f6", color="white",
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: household_dashboard(), icon_color="white")
            )
        )
        
        if not transactions:
            page.add(ft.Container(padding=40, content=ft.Column([
                ft.Icon("receipt_long", size=80, color="grey"),
                ft.Text("No transactions yet", size=18, color="grey"),
                ft.Text("Your redemption history will appear here", size=12, color="grey")
            ], horizontal_alignment="center", spacing=10)))
        else:
            txn_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
            for txn in transactions:
                voucher_text = ", ".join([f"${d}×{c}" for d, c in sorted(txn["vouchers"].items(), key=lambda x: int(x[0]))])
                txn_list.controls.append(
                    ft.Container(width=350, padding=15, border_radius=10, bgcolor="white",
                               border=ft.border.all(1, "#e5e7eb"),
                               content=ft.Column([
                                   ft.Row([
                                       ft.Icon("store", color="#10b981", size=24),
                                       ft.Column([
                                           ft.Text(txn["merchant_name"], size=16, weight="bold"),
                                           ft.Text(txn["datetime"], size=10, color="grey")
                                       ], expand=True, spacing=2),
                                       ft.Text(f"${txn['amount']}", size=20, weight="bold", color="#059669")
                                   ], alignment="spaceBetween"),
                                   ft.Container(height=5),
                                   ft.Container(padding=8, bgcolor="#f0fdf4", border_radius=6,
                                              content=ft.Text(f"Vouchers: {voucher_text}", size=12, color="#065f46"))
                               ], spacing=5))
                )
            page.add(ft.Container(padding=20, content=txn_list))
        page.update()

    # HOUSEHOLD DASHBOARD with notification auto-reload
    def household_dashboard():
        page.controls.clear()
        
        response, status = api_client.get_balance(session["user_id"])
        if status != 200:
            show_snack("Error loading balance", "red")
            return
        
        vouchers = response.get("vouchers", {})
        session["selected_vouchers"] = {}
        
        # Check for notifications ONCE when dashboard loads
        def check_notifications_once():
            notif_response, notif_status = api_client.get_notifications(session["user_id"])
            if notif_status == 200 and notif_response.get("notifications"):
                show_snack("💰 Payment received!", "green")
                time.sleep(1)
                # Don't reload - just show notification
        
        # Check once at load
        check_notifications_once()
        
        vouchers_column = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center")
        summary_text = ft.Text("Total Selected: $0", size=18, weight="bold", color="blue")
        code_display_container = ft.Container()
        
        def refresh_summary():
            total = sum(int(d) * c for d, c in session["selected_vouchers"].items())
            summary_text.value = f"Total Selected: ${total}"
            page.update()

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

        for tranche_name, denoms in vouchers.items():
            if not any(denoms.values()):
                continue
            vouchers_column.controls.append(
                ft.Container(padding=10, bgcolor="#f0f9ff", border_radius=8,
                           content=ft.Text(f"From {tranche_name}", size=14, weight="bold", color="#1e40af"))
            )
            for denom, max_count in denoms.items():
                if max_count == 0:
                    continue
                denom_str = str(denom)
                current_sel = session["selected_vouchers"].get(denom_str, 0)
                count_display = ft.Text(str(current_sel), size=20, width=40, text_align="center")
                
                vouchers_column.controls.append(
                    ft.Container(padding=10, border=ft.border.all(1, "#e5e7eb"), border_radius=10,
                               bgcolor="white", width=350,
                               content=ft.Row([
                                   ft.Text(f"${denom}", size=24, weight="bold", width=60),
                                   ft.Column([ft.Text(f"Available: {max_count}", size=12, color="grey")], expand=True),
                                   ft.IconButton(icon="remove", on_click=lambda e, d=denom_str, m=max_count, t=count_display: update_count(d, -1, m, t)),
                                   count_display,
                                   ft.IconButton(icon="add", on_click=lambda e, d=denom_str, m=max_count, t=count_display: update_count(d, 1, m, t)),
                               ], alignment="spaceBetween"))
                )

        def generate_qr(e):
            selected = session["selected_vouchers"]
            if not selected or all(v == 0 for v in selected.values()):
                show_snack("Please select at least one voucher", "red")
                return
            
            response, status = api_client.generate_token(session["user_id"], selected)
            
            if status == 200:
                token = response["token"]
                total = response["total"]
                voucher_text = ", ".join([f"${d}×{c}" for d, c in sorted(selected.items(), key=lambda x: int(x[0]))])
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                def copy_code(e):
                    page.set_clipboard(token)
                    show_snack("✓ Code copied!", "green")
                
                def close_code(e):
                    code_display_container.content = None
                    code_display_container.visible = False
                    session["selected_vouchers"] = {}
                    refresh_summary()
                    page.update()
                
                code_display_container.content = ft.Container(
                    width=350, padding=20, bgcolor="white", border_radius=12,
                    border=ft.border.all(3, "#1976d2"),
                    shadow=ft.BoxShadow(spread_radius=2, blur_radius=10, color="#90caf9"),
                    content=ft.Column([
                        ft.Row([
                            ft.Text("🎫 Redemption Code", size=20, weight="bold", expand=True),
                            ft.IconButton(icon="close", on_click=close_code, icon_size=20)
                        ], alignment="spaceBetween"),
                        ft.Divider(),
                        ft.Text("Show this code to merchant:", size=12, color="grey", text_align="center"),
                        ft.Container(height=10),
                        ft.Container(
                            bgcolor="#e3f2fd", padding=20, border_radius=8,
                            content=ft.Text(token, size=32, weight="bold", color="#1565c0",
                                          selectable=True, text_align="center")
                        ),
                        ft.Container(height=15),
                        ft.ElevatedButton("📋 Copy Code", on_click=copy_code, width=310,
                                        height=40, bgcolor="#1976d2", color="white"),
                        ft.Divider(),
                        ft.Container(
                            bgcolor="#f5f5f5", padding=15, border_radius=8,
                            content=ft.Column([
                                ft.Text(f"Total: ${total}", size=20, weight="bold", color="#2e7d32"),
                                ft.Container(height=5),
                                ft.Text(f"Vouchers: {voucher_text}", size=12, color="grey"),
                            ], horizontal_alignment="center")
                        ),
                        ft.Container(height=5),
                        ft.Text(f"Generated: {current_time}", size=10, color="grey", text_align="center"),
                        ft.Text("💡 Merchant will enter this code on their device",
                               size=11, color="grey", italic=True, text_align="center")
                    ], horizontal_alignment="center", spacing=10)
                )
                code_display_container.visible = True
                page.update()
            else:
                show_snack(f"❌ {response.get('error', 'Failed')}", "red")

        page.add(
            ft.AppBar(
                title=ft.Row([ft.Text("🎫", size=24), ft.Text("My Vouchers", size=18, weight="bold")], spacing=10),
                center_title=True, bgcolor="#3b82f6", color="white",
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: claim_vouchers_view(), icon_color="white"),
                actions=[
                    ft.IconButton(icon="receipt_long", on_click=lambda _: transaction_history_view(),
                                tooltip="Transaction History", icon_color="white"),
                    ft.IconButton(icon="refresh", on_click=lambda _: household_dashboard(),
                                tooltip="Refresh Balance", icon_color="white"),
                    ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")
                ]
            ),
            ft.Container(content=vouchers_column, expand=True, padding=10, alignment=ft.alignment.top_center),
            ft.Container(
                padding=20, bgcolor="white", border=ft.border.only(top=ft.BorderSide(1, "#eee")),
                content=ft.Column([
                    summary_text,
                    ft.ElevatedButton("Generate QR Code", on_click=generate_qr, width=350, height=50,
                                    bgcolor="blue", color="white"),
                    ft.Container(height=10),
                    code_display_container
                ], horizontal_alignment="center")
            )
        )
        page.update()

    page.add(login_view())

ft.app(target=main, port=8550)