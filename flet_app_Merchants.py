import flet as ft
import os
from datetime import datetime

from services.merchant_service import (
    merchants,
    load_merchants,
    register_merchant
)
from services.household_service import (
    households,
    load_households,
    save_households
)

def main(page: ft.Page):
    page.title = "CDC Merchant App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 0
    
    # Initialize data
    load_merchants()
    load_households()
    
    # Session
    session = {
        "merchant_id": None,
        "merchant_name": None,
        "transaction_history": []
    }

    def show_snack(text, color="blue"):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def logout():
        session.clear()
        session["transaction_history"] = []
        page.controls.clear()
        page.add(login_view())
        page.update()

    # =========================
    # 1. Login View
    # =========================
    def login_view():
        merchant_id_input = ft.TextField(
            label="Merchant ID", 
            width=350,
            hint_text="Enter your merchant ID",
            prefix_icon="store"
        )
        
        def do_login(e):
            mid = merchant_id_input.value.strip()
            if not mid:
                show_snack("Please enter Merchant ID", "red")
                return

            if mid in merchants:
                session["merchant_id"] = mid
                session["merchant_name"] = merchants[mid].get("merchant_name", "Merchant")
                merchant_terminal()
            else:
                show_snack("Merchant ID not found", "red")

        # Professional merchant logo header
        logo_header = ft.Container(
            width=350,
            padding=30,
            border_radius=15,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#10b981", "#059669"]
            ),
            content=ft.Column([
                # Logo icon
                ft.Container(
                    width=80,
                    height=80,
                    border_radius=40,
                    bgcolor="white",
                    content=ft.Text("🏪", size=45),
                    alignment=ft.alignment.center
                ),
                ft.Container(height=10),
                # App name
                ft.Text(
                    "MERCHANT POS",
                    size=28,
                    weight="bold",
                    color="white",
                    text_align="center"
                ),
                ft.Text(
                    "CDC Voucher Terminal",
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
            ft.Text("Merchant Login", size=24, weight="bold", color="#1f2937"),
            ft.Text("Enter your credentials", size=14, color="grey"),
            ft.Container(height=20),
            merchant_id_input,
            ft.Container(height=10),
            ft.ElevatedButton(
                "Login", 
                on_click=do_login, 
                width=350, 
                height=50,
                bgcolor="#10b981",
                color="white"
            ),
            ft.Container(height=10),
            ft.TextButton(
                "New Merchant? Register Here",
                on_click=lambda _: register_view()
            )
        ], horizontal_alignment="center", spacing=10)

    # =========================
    # 2. Register View
    # =========================
    def register_view():
        page.controls.clear()
        
        fields = {
            "merchant_id": ft.TextField(label="Merchant ID*", width=350),
            "merchant_name": ft.TextField(label="Business Name*", width=350),
            "uen": ft.TextField(label="UEN*", width=350),
            "bank_name": ft.TextField(label="Bank Name", width=350),
            "bank_code": ft.TextField(label="Bank Code", width=350),
            "branch_code": ft.TextField(label="Branch Code", width=350),
            "account_number": ft.TextField(label="Account Number", width=350),
            "account_holder": ft.TextField(label="Account Holder", width=350),
        }
        
        result_container = ft.Column(horizontal_alignment="center", spacing=10)

        def submit_registration(e):
            try:
                # Validate required fields
                if not fields["merchant_id"].value or not fields["merchant_name"].value or not fields["uen"].value:
                    show_snack("Please fill in required fields (*)", "red")
                    return

                data = {k: f.value.strip() for k, f in fields.items()}
                res, status = register_merchant(data)
                
                if status not in [200, 201]:
                    raise Exception(res.get("error", "Registration failed"))

                new_mid = data["merchant_id"]
                
                # Success display
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
                            ft.Text("YOUR MERCHANT ID:", size=14, weight="bold"),
                            ft.Container(
                                bgcolor="#f3f4f6",
                                padding=15,
                                border_radius=8,
                                content=ft.Text(new_mid, size=28, weight="bold", color="black", selectable=True)
                            ),
                            ft.Text("Please SAVE this ID now!", color="red", italic=True, size=12),
                            ft.Container(height=20),
                            ft.ElevatedButton(
                                "Go to Login", 
                                on_click=lambda _: (page.controls.clear(), page.add(login_view()), page.update()),
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
                    ft.Text("🏪", size=24),
                    ft.Text("Register Merchant", size=18, weight="bold")
                ], spacing=10),
                center_title=True,
                bgcolor="#10b981",
                color="white",
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout(), icon_color="white")
            ),
            ft.Column([
                ft.Text("Business Registration", size=18, weight="bold"),
                ft.Text("* Required fields", size=12, color="grey"),
                ft.Container(height=10),
                ft.Column(
                    controls=list(fields.values()),
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO
                ),
                ft.Container(height=10),
                ft.ElevatedButton("Register", on_click=submit_registration, width=350, height=50),
                result_container
            ], horizontal_alignment="center", spacing=15, scroll=ft.ScrollMode.AUTO)
        )
        page.update()

    # =========================
    # 3. Merchant Terminal (Token Redemption)
    # =========================
    def merchant_terminal():
        page.controls.clear()
        
        token_input = ft.TextField(
            label="",
            width=350,
            text_align="center",
            hint_text="Enter redemption code",
            text_size=20,
            height=70,
            border_color="#3b82f6",
            focused_border_color="#1e40af"
        )
        
        # Transaction history
        history_column = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment="center"
        )
        
        def refresh_history():
            history_column.controls.clear()
            
            if not session["transaction_history"]:
                history_column.controls.append(
                    ft.Container(
                        padding=20,
                        content=ft.Text("No transactions yet", size=14, color="grey", italic=True)
                    )
                )
            else:
                for txn in reversed(session["transaction_history"][-5:]):
                    history_column.controls.append(
                        ft.Container(
                            padding=12,
                            border_radius=8,
                            bgcolor="#f9fafb",
                            border=ft.border.all(1, "#e5e7eb"),
                            width=350,
                            content=ft.Row([
                                ft.Icon("check_circle", color="green", size=20),
                                ft.Column([
                                    ft.Text(f"${txn['amount']}", size=18, weight="bold", color="#059669"),
                                    ft.Text(txn['time'], size=10, color="grey")
                                ], spacing=2, expand=True),
                                ft.Text(txn['token'][:10] + "...", size=10, color="grey")
                            ], alignment="spaceBetween")
                        )
                    )
            page.update()
        
        def process_payment(e):
            token_val = token_input.value.strip()
            
            print(f"\n{'='*50}")
            print(f"🔍 DEBUGGING REDEMPTION")
            print(f"{'='*50}")
            print(f"Token entered: {token_val}")
            
            if not token_val:
                show_snack("Please enter a token", "red")
                print("❌ Empty token")
                return
            
            # RELOAD households to get latest data
            load_households()
            print(f"✅ Reloaded households: {len(households)} found")
            
            # Find matching household with this token
            target_hid = None
            token_data = None
            
            print(f"\n🔎 Searching for token in {len(households)} households...")
            for hid, h in households.items():
                active_token = h.get("active_token")
                if active_token:
                    print(f"  Household {hid}: has token {active_token}")
                    if active_token == token_val:
                        target_hid = hid
                        token_data = h.get("token_data")
                        print(f"  ✅ MATCH FOUND!")
                        break
            
            if not target_hid or not token_data:
                print(f"❌ Token not found or expired")
                print(f"   Searched {len(households)} households")
                show_snack("Invalid or Expired Token", "red")
                return
            
            print(f"\n✅ Token valid!")
            print(f"   Household: {target_hid}")
            print(f"   Vouchers: {token_data}")
            
            # Calculate total amount
            total_amt = sum(int(d) * c for d, c in token_data.items())
            print(f"   Total: ${total_amt}")
            
            # Deduct vouchers from household
            household = households[target_hid]
            for denom, count in token_data.items():
                for tranche in household.get("vouchers", {}).values():
                    if denom in tranche:
                        old_count = tranche[denom]
                        tranche[denom] = max(0, tranche[denom] - count)
                        print(f"   Deducted ${denom}: {old_count} → {tranche[denom]}")
                        break
            
            # Clear the token (single use)
            households[target_hid]["active_token"] = None
            households[target_hid]["token_data"] = None
            save_households()
            
            print(f"✅ Saved changes to households.json")
            print(f"{'='*50}\n")
            
            # Clear input immediately
            token_input.value = ""
            
            # Show immediate success message
            show_snack(f"✅ Payment Successful! ${total_amt}", "green")
            
            # Record transaction
            import time
            session["transaction_history"].append({
                "amount": total_amt,
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "token": token_val,
                "household": target_hid
            })
            
            # Refresh history immediately
            refresh_history()
            
            # Show success message on page instead of dialog
            success_container = ft.Container(
                width=350,
                padding=20,
                margin=ft.margin.only(top=20),
                border_radius=12,
                bgcolor="#ecfdf5",
                border=ft.border.all(2, "#10b981"),
                content=ft.Column([
                    ft.Icon("check_circle", color="green", size=60),
                    ft.Text("Payment Successful!", size=22, weight="bold", color="#059669"),
                    ft.Container(height=10),
                    ft.Text(f"${total_amt}", size=48, weight="bold", color="#059669"),
                    ft.Container(height=10),
                    ft.Container(
                        padding=10,
                        bgcolor="#f0fdf4",
                        border_radius=6,
                        content=ft.Column([
                            ft.Text("Vouchers Redeemed:", size=12, weight="bold"),
                            ft.Text(", ".join([f"${d}×{c}" for d, c in sorted(token_data.items(), key=lambda x: int(x[0]))]), size=14)
                        ], horizontal_alignment="center")
                    ),
                    ft.Container(height=5),
                    ft.Text(f"Token: {token_val[:12]}...", size=10, color="grey")
                ], horizontal_alignment="center", spacing=5)
            )
            
            # Insert success message at the top
            page.controls.insert(1, success_container)
            page.update()
            
            print("✅ Success message displayed")

        # Build terminal UI
        refresh_history()
        
        page.add(
            ft.AppBar(
                title=ft.Row([
                    ft.Text("🏪", size=24),
                    ft.Text(f"{session['merchant_name']}", size=18, weight="bold")
                ], spacing=10),
                center_title=True,
                bgcolor="#10b981",
                color="white",
                leading=ft.IconButton(icon="store", icon_color="white"),
                actions=[ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")]
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
                
                # Token input
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
                        on_click=process_payment, 
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
                ),
                
                ft.Divider(),
                
                # Transaction history
                ft.Container(
                    padding=10,
                    width=350,
                    content=ft.Column([
                        ft.Text("Recent Transactions", size=16, weight="bold", color="#374151"),
                        ft.Divider(height=1, color="#e5e7eb"),
                        history_column
                    ], spacing=10)
                )
                
            ], spacing=10, horizontal_alignment="center", expand=True)
        )
        page.update()

    # Start app
    page.add(login_view())

# Run in desktop mode on port 8551
print("\n" + "="*50)
print("🏪 MERCHANT APP RUNNING")
print("="*50)
print("Access at: http://localhost:8551")
print("Press Ctrl+C to stop")
print("="*50 + "\n")

ft.app(target=main, port=8551)