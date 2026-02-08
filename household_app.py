"""
CDC Household App - API Version
Enhanced with dynamic member addition and validation
"""
import flet as ft
import time
import threading
import re
from datetime import datetime

from api_client import api_client

def validate_singapore_postal_code(postal_code):
    """Validate Singapore postal code (6 digits)"""
    if not postal_code:
        return False, "Postal code is required"
    
    # Remove spaces
    postal_code = postal_code.strip()
    
    # Check if it's exactly 6 digits
    if not re.match(r'^\d{6}$', postal_code):
        return False, "Postal code must be exactly 6 digits"
    
    # Check valid range (Singapore postal codes are 01xxxx to 82xxxx)
    code_int = int(postal_code)
    if code_int < 10000 or code_int > 829999:
        return False, "Invalid Singapore postal code range"
    
    return True, ""

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
    
    session = {"user_id": None, "selected_vouchers": {}, "members": []}

    def show_snack(text, color="blue"):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def logout():
        session.clear()
        session["selected_vouchers"] = {}
        session["members"] = []
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

    # REGISTER VIEW WITH DYNAMIC MEMBER ADDITION
    def register_view():
        page.controls.clear()
        
        # Members list container
        members_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        postal_input = ft.TextField(label="Postal Code (6 digits)*", width=350, max_length=6)
        postal_error = ft.Text("", size=12, color="red", visible=False)
        result_container = ft.Column(horizontal_alignment="center", spacing=10)
        
        def add_member_card(first_name="", last_name="", is_first=False):
            """Add a member input card"""
            first_name_input = ft.TextField(
                label="First Name*",
                value=first_name,
                width=140,
                border_color="#3b82f6"
            )
            last_name_input = ft.TextField(
                label="Last Name*",
                value=last_name,
                width=140,
                border_color="#3b82f6"
            )
            
            member_card = ft.Container(
                padding=10,
                border_radius=8,
                bgcolor="#f0f9ff",
                border=ft.border.all(1, "#3b82f6"),
                width=350,
                content=ft.Column([
                    ft.Row([
                        ft.Icon("person", color="#3b82f6", size=20),
                        ft.Text(f"Member {len(session['members']) + 1}", 
                               size=14, weight="bold", color="#1e40af", expand=True),
                        ft.IconButton(
                            icon="delete",
                            icon_color="red",
                            icon_size=20,
                            visible=not is_first,  # Can't delete first member
                            on_click=lambda e: remove_member(member_card)
                        ) if not is_first else ft.Container()
                    ], alignment="spaceBetween"),
                    ft.Row([
                        first_name_input,
                        last_name_input
                    ], spacing=10)
                ], spacing=5)
            )
            
            # Store references
            member_card.data = {
                "first_name": first_name_input,
                "last_name": last_name_input
            }
            
            members_column.controls.append(member_card)
            update_member_numbers()
            page.update()
        
        def remove_member(member_card):
            """Remove a member card"""
            members_column.controls.remove(member_card)
            update_member_numbers()
            page.update()
        
        def update_member_numbers():
            """Update member numbers after add/remove"""
            for idx, card in enumerate(members_column.controls):
                # Update the member number text
                if hasattr(card, 'content') and hasattr(card.content, 'controls'):
                    row = card.content.controls[0]  # First row with number
                    if len(row.controls) >= 2:
                        row.controls[1].value = f"Member {idx + 1}"
        
        def add_another_member(e):
            """Add another member input"""
            if len(members_column.controls) >= 10:
                show_snack("Maximum 10 members allowed", "orange")
                return
            add_member_card()
        
        def validate_postal(e):
            """Validate postal code as user types"""
            is_valid, error_msg = validate_singapore_postal_code(postal_input.value)
            if postal_input.value and not is_valid:
                postal_error.value = error_msg
                postal_error.visible = True
                postal_input.border_color = "red"
            else:
                postal_error.visible = False
                postal_input.border_color = "#3b82f6"
            page.update()
        
        postal_input.on_change = validate_postal

        def submit_registration(e):
            # Validate postal code
            is_valid, error_msg = validate_singapore_postal_code(postal_input.value)
            if not is_valid:
                show_snack(error_msg, "red")
                postal_error.value = error_msg
                postal_error.visible = True
                postal_input.border_color = "red"
                page.update()
                return
            
            # Collect all members
            members = []
            has_error = False
            
            for card in members_column.controls:
                first_name = card.data["first_name"].value.strip()
                last_name = card.data["last_name"].value.strip()
                
                if not first_name or not last_name:
                    show_snack("Please fill in all member names", "red")
                    has_error = True
                    break
                
                # Store as "FirstName LastName"
                full_name = f"{first_name} {last_name}"
                members.append(full_name)
            
            if has_error or not members:
                return
            
            # Make API call
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
                                   ft.Container(height=10),
                                   ft.Container(
                                       padding=10,
                                       bgcolor="#f0f9ff",
                                       border_radius=8,
                                       content=ft.Column([
                                           ft.Text("Registered Members:", size=12, weight="bold"),
                                           ft.Text(", ".join(members), size=11, color="#1e40af")
                                       ], spacing=5)
                                   ),
                                   ft.Container(height=20),
                                   ft.ElevatedButton("Claim Your Vouchers", on_click=lambda _: claim_vouchers_view(),
                                                   bgcolor="blue", color="white", width=280, height=50)
                               ], horizontal_alignment="center"))
                ]
            else:
                show_snack(f"Error: {response.get('error', 'Failed')}", "red")
            page.update()

        # Add first member by default
        add_member_card(is_first=True)
        
        page.add(
            ft.AppBar(title=ft.Row([ft.Text("🎫", size=24), ft.Text("Register Household", size=18, weight="bold")], spacing=10),
                     center_title=True, bgcolor="#3b82f6", color="white",
                     leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout(), icon_color="white")),
            ft.Column([
                ft.Text("Household Registration", size=20, weight="bold"),
                ft.Text("Add all household members", size=14, color="grey"),
                ft.Container(height=10),
                
                # Members section
                ft.Container(
                    padding=10,
                    bgcolor="white",
                    border_radius=10,
                    width=350,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("group", color="#3b82f6", size=24),
                            ft.Text("Household Members", size=16, weight="bold", color="#1e40af", expand=True),
                        ]),
                        ft.Container(height=5),
                        members_column,
                        ft.Container(height=10),
                        ft.OutlinedButton(
                            "➕ Add Another Member",
                            on_click=add_another_member,
                            width=330,
                            style=ft.ButtonStyle(
                                color="#3b82f6",
                                side=ft.BorderSide(2, "#3b82f6")
                            )
                        )
                    ], spacing=10)
                ),
                
                ft.Container(height=10),
                
                # Postal code section
                postal_input,
                postal_error,
                
                ft.Container(height=10),
                ft.ElevatedButton("Register Household", on_click=submit_registration, 
                                width=350, height=50, bgcolor="#3b82f6", color="white"),
                result_container
            ], horizontal_alignment="center", spacing=15, scroll=ft.ScrollMode.AUTO)
        )
        page.update()

    # CLAIM VOUCHERS VIEW - EXACT ORIGINAL DESIGN
    def claim_vouchers_view():
        page.controls.clear()
        
        schemes = {
            "May2025": {"2": 50, "5": 20, "10": 30},
            "Jan2026": {"2": 30, "5": 12, "10": 18},
        }
        
        def claim_scheme(scheme_name, vouchers):
            response, status = api_client.claim_vouchers(session["user_id"], scheme_name)
            
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
        
        def scheme_card(name, vouchers_dict):
            total_value = sum(int(denom) * count for denom, count in vouchers_dict.items())
            is_claimed = name in existing_vouchers
            
            card_content = ft.Container(
                width=350, padding=20, border_radius=12,
                bgcolor="#f0f9ff" if not is_claimed else "#ecfdf5",
                border=ft.border.all(2, "#3b82f6" if not is_claimed else "#10b981"),
                content=ft.Column([
                    ft.Row([
                        ft.Text(name, size=20, weight="bold", color="#1e3a8a" if not is_claimed else "#065f46"),
                        ft.Icon("check_circle", color="#10b981", size=24) if is_claimed else ft.Container()
                    ], alignment="spaceBetween"),
                    ft.Divider(),
                    ft.Column([
                        ft.Row([
                            ft.Text(f"${denom} vouchers", size=14, expand=True),
                            ft.Text(f"× {count}", size=16, weight="bold", color="#3b82f6" if not is_claimed else "#10b981")
                        ]) for denom, count in vouchers_dict.items()
                    ], spacing=8),
                    ft.Divider(),
                    ft.Row([
                        ft.Text("Total Value:", size=16, weight="bold"),
                        ft.Text(f"${total_value}", size=20, weight="bold", color="#10b981")
                    ], alignment="spaceBetween"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "✓ Already Claimed" if is_claimed else "Claim Vouchers",
                        on_click=lambda e: claim_scheme(name, vouchers_dict),
                        width=310, height=45,
                        bgcolor="#9ca3af" if is_claimed else "#3b82f6",
                        color="white",
                        disabled=is_claimed
                    )
                ], horizontal_alignment="center")
            )
            return card_content

        has_any_claimed = len(existing_vouchers) > 0
        
        page.add(
            ft.AppBar(
                title=ft.Row([ft.Text("🎫", size=24), ft.Text("Claim Vouchers", size=18, weight="bold")], spacing=10),
                center_title=True, bgcolor="#3b82f6", color="white",
                leading=ft.IconButton(icon="home", on_click=lambda _: logout() if not has_any_claimed else None, icon_color="white"),
                actions=[
                    ft.IconButton(icon="account_balance_wallet", on_click=lambda _: household_dashboard(),
                                tooltip="View Balance", icon_color="white") if has_any_claimed else ft.Container(),
                    ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")
                ]
            ),
            ft.Column([
                ft.Container(height=10),
                ft.Text("Available Voucher Schemes", size=20, weight="bold", color="#1f2937"),
                ft.Text("Claim your vouchers below", size=14, color="grey"),
                ft.Container(height=20),
                *[scheme_card(name, vouchers) for name, vouchers in schemes.items()],
                ft.Container(height=20),
                # Show "Go to My Vouchers" button if any vouchers claimed
                ft.Container(
                    content=ft.ElevatedButton(
                        "🎫 Go to My Vouchers",
                        on_click=lambda _: household_dashboard(),
                        width=350,
                        height=50,
                        bgcolor="#10b981",
                        color="white",
                        style=ft.ButtonStyle(text_style=ft.TextStyle(size=16, weight="bold"))
                    ),
                    padding=ft.padding.only(bottom=20)
                ) if has_any_claimed else ft.Container(),
            ], horizontal_alignment="center", spacing=15, scroll=ft.ScrollMode.AUTO)
        )
        page.update()

    # HOUSEHOLD DASHBOARD
    def household_dashboard():
        page.controls.clear()
        
        response, status = api_client.get_balance(session["user_id"])
        vouchers = response.get("vouchers", {}) if status == 200 else {}
        
        # Check for notifications
        def check_notifications_once():
            notif_response, notif_status = api_client.get_notifications(session["user_id"])
            if notif_status == 200:
                notifications = notif_response.get("notifications", [])
                if notifications:
                    most_recent = notifications[0]
                    amount = most_recent.get("amount", 0)
                    merchant = most_recent.get("merchant_name", "Merchant")
                    show_snack(f"✅ ${amount} redeemed at {merchant}!", "green")
        
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
            
            total = sum(int(d) * c for d, c in selected.items())
            if total == 0:
                show_snack("Please select at least one voucher", "red")
                return
            
            for denom, count in selected.items():
                if count > 0:
                    found = False
                    for tranche, denoms in vouchers.items():
                        if denom in denoms and denoms[denom] >= count:
                            found = True
                            break
                    if not found:
                        show_snack(f"Insufficient ${denom} vouchers", "red")
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

        # Transaction history view
        def transaction_history_view():
            page.controls.clear()
            
            response, status = api_client.get_transactions(session["user_id"], limit=20)
            transactions = response.get("transactions", []) if status == 200 else []
            
            history_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
            
            if not transactions:
                history_column.controls.append(
                    ft.Container(
                        padding=40,
                        content=ft.Column([
                            ft.Icon("receipt_long", size=60, color="grey"),
                            ft.Text("No transactions yet", size=16, color="grey")
                        ], horizontal_alignment="center")
                    )
                )
            else:
                for txn in transactions:
                    amount = txn.get("amount", 0)
                    merchant = txn.get("merchant_name", "Merchant")
                    timestamp = txn.get("datetime", "")
                    vouchers = txn.get("vouchers", {})
                    voucher_text = ", ".join([f"${d}×{c}" for d, c in sorted(vouchers.items(), key=lambda x: int(x[0]))])
                    
                    history_column.controls.append(
                        ft.Container(
                            padding=15,
                            border_radius=10,
                            bgcolor="white",
                            border=ft.border.all(1, "#e5e7eb"),
                            width=350,
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon("store", color="#10b981", size=24),
                                    ft.Column([
                                        ft.Text(merchant, size=16, weight="bold"),
                                        ft.Text(timestamp, size=11, color="grey")
                                    ], expand=True),
                                    ft.Text(f"-${amount}", size=18, weight="bold", color="#dc2626")
                                ], alignment="spaceBetween"),
                                ft.Container(height=5),
                                ft.Container(
                                    padding=8,
                                    bgcolor="#f0f9ff",
                                    border_radius=6,
                                    content=ft.Text(f"Vouchers: {voucher_text}", size=11, color="#1e40af")
                                )
                            ], spacing=5)
                        )
                    )
            
            page.add(
                ft.AppBar(
                    title=ft.Row([ft.Text("📜", size=24), ft.Text("Transaction History", size=18, weight="bold")], spacing=10),
                    center_title=True, bgcolor="#3b82f6", color="white",
                    leading=ft.IconButton(icon="arrow_back", on_click=lambda _: household_dashboard(), icon_color="white"),
                    actions=[ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")]
                ),
                ft.Column([
                    ft.Container(height=10),
                    history_column
                ], horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)
            )
            page.update()

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
                    ft.ElevatedButton("Generate Redemption Code", on_click=generate_qr, width=350, height=50,
                                    bgcolor="blue", color="white"),
                    ft.Container(height=10),
                    code_display_container
                ], horizontal_alignment="center")
            )
        )
        page.update()

    page.add(login_view())

ft.app(target=main, port=8550)