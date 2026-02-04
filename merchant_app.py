"""
CDC Merchant App - COMPLETE VERSION
Better terminal UI + Transaction history display
"""
import flet as ft
from datetime import datetime

from api_client import api_client

def main(page: ft.Page):
    print("="*50)
    print("🚀 Starting Merchant App...")
    print("="*50)
    
    page.title = "CDC Merchant App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 0
    
    print("✅ Page configured")
    
    # Check API
    print("🔍 Checking API connection...")
    try:
        api_connected = api_client.check_connection()
        print(f"{'✅' if api_connected else '❌'} API: {api_connected}")
    except Exception as e:
        print(f"❌ API error: {e}")
        api_connected = False
    
    if not api_connected:
        print("⚠️  Showing error page")
        page.add(
            ft.Container(
                padding=40,
                content=ft.Column([
                    ft.Icon("error", size=80, color="red"),
                    ft.Text("Cannot Connect to API", size=20, color="red"),
                    ft.Text("Run: python api_server.py", size=14, color="blue"),
                ], horizontal_alignment="center", spacing=10)
            )
        )
        page.update()
        return
    
    print("✅ API connected")
    
    session = {"merchant_id": None, "merchant_name": None, "transactions": []}

    def show_snack(text, color="blue"):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def logout():
        session.clear()
        session["transactions"] = []
        page.controls.clear()
        page.add(login_view())
        page.update()

    # LOGIN
    def login_view():
        merchant_id_input = ft.TextField(label="Merchant ID", width=350, prefix_icon="store")
        
        def do_login(e):
            mid = merchant_id_input.value.strip()
            if not mid:
                show_snack("Please enter ID", "red")
                return

            response, status = api_client.get_merchant(mid)
            session["merchant_id"] = mid
            session["merchant_name"] = response.get("merchant_name", "Merchant") if status == 200 else "Merchant"
            merchant_terminal()

        logo_header = ft.Container(
            width=350, padding=30, border_radius=15,
            gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=["#10b981", "#059669"]),
            content=ft.Column([
                ft.Container(width=80, height=80, border_radius=40, bgcolor="white", content=ft.Text("🏪", size=45), alignment=ft.alignment.center),
                ft.Container(height=10),
                ft.Text("MERCHANT POS", size=28, weight="bold", color="white", text_align="center"),
                ft.Text("CDC Voucher Terminal", size=14, color="white", opacity=0.9, text_align="center"),
            ], horizontal_alignment="center")
        )

        return ft.Column([
            ft.Container(height=40), logo_header, ft.Container(height=30),
            ft.Text("Merchant Login", size=24, weight="bold", color="#1f2937"),
            ft.Text("Enter your credentials", size=14, color="grey"), ft.Container(height=20), merchant_id_input, ft.Container(height=10),
            ft.ElevatedButton("Login", on_click=do_login, width=350, height=50, bgcolor="#10b981", color="white"),
            ft.Container(height=10),
            ft.TextButton("New Merchant? Register Here", on_click=lambda _: register_view())
        ], horizontal_alignment="center", spacing=10)

    # REGISTER
    def register_view():
        page.controls.clear()
        
        merchant_name_input = ft.TextField(label="Business Name*", width=350)
        uen_input = ft.TextField(label="UEN*", width=350)
        bank_name_input = ft.TextField(label="Bank Name", width=350)
        bank_code_input = ft.TextField(label="Bank Code", width=350)
        branch_code_input = ft.TextField(label="Branch Code", width=350)
        account_number_input = ft.TextField(label="Account Number", width=350)
        account_holder_input = ft.TextField(label="Account Holder", width=350)
        result_container = ft.Column(horizontal_alignment="center", spacing=10)

        def submit_registration(e):
            if not merchant_name_input.value or not uen_input.value:
                show_snack("Please fill required fields", "red")
                return

            merchant_data = {
                "merchant_name": merchant_name_input.value.strip(),
                "uen": uen_input.value.strip(),
                "bank_name": bank_name_input.value.strip(),
                "bank_code": bank_code_input.value.strip(),
                "branch_code": branch_code_input.value.strip(),
                "account_number": account_number_input.value.strip(),
                "account_holder": account_holder_input.value.strip()
            }
            
            response, status = api_client.register_merchant(merchant_data)
            
            if status in [200, 201]:
                new_mid = response.get("merchant_id")
                result_container.controls = [
                    ft.Container(padding=20, margin=ft.margin.only(top=20), border_radius=10,
                               bgcolor="#ecfdf5", border=ft.border.all(2, "#059669"), width=350,
                               content=ft.Column([
                                   ft.Icon("check_circle", color="green", size=50),
                                   ft.Text("Success!", size=20, weight="bold", color="green"),
                                   ft.Divider(),
                                   ft.Text("YOUR MERCHANT ID:", size=14, weight="bold"),
                                   ft.Container(bgcolor="#f3f4f6", padding=15, border_radius=8,
                                              content=ft.Text(new_mid, size=28, weight="bold", selectable=True)),
                                   ft.Text("SAVE THIS ID!", color="red", italic=True, size=12),
                                   ft.Container(height=20),
                                   ft.ElevatedButton("Go to Login", on_click=lambda _: (page.controls.clear(), page.add(login_view()), page.update()),
                                                   bgcolor="blue", color="white", width=280, height=50)
                               ], horizontal_alignment="center"))
                ]
            else:
                show_snack(f"Error: {response.get('error', 'Failed')}", "red")
            page.update()

        page.add(
            ft.AppBar(title=ft.Row([ft.Text("🏪", size=24), ft.Text("Register", size=18, weight="bold")], spacing=10),
                     center_title=True, bgcolor="#10b981", color="white",
                     leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout(), icon_color="white")),
            ft.Column([
                ft.Text("Business Registration", size=18, weight="bold"),
                ft.Text("* Required | Merchant ID auto-generated", size=10, color="blue", italic=True),
                ft.Container(height=10),
                merchant_name_input, uen_input, bank_name_input, bank_code_input,
                branch_code_input, account_number_input, account_holder_input,
                ft.Container(height=10),
                ft.ElevatedButton("Register", on_click=submit_registration, width=350, height=50, bgcolor="#10b981", color="white"),
                result_container
            ], horizontal_alignment="center", spacing=15, scroll=ft.ScrollMode.AUTO)
        )
        page.update()

    # MERCHANT TERMINAL - IMPROVED UI
    def merchant_terminal():
        page.controls.clear()
        
        token_input = ft.TextField(
            label="Redemption Code",
            width=350,
            text_align="center",
            hint_text="Enter code from customer",
            text_size=24,
            height=80,
            border_color="#10b981",
            focused_border_color="#059669",
            border_width=2
        )
        
        # Transaction history display
        history_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center")
        
        def refresh_history():
            history_column.controls.clear()
            
            if not session["transactions"]:
                history_column.controls.append(
                    ft.Container(padding=20, content=ft.Text("No transactions yet", size=14, color="grey", italic=True))
                )
            else:
                # Show last 5 transactions
                for txn in list(reversed(session["transactions"]))[:5]:
                    history_column.controls.append(
                        ft.Container(padding=12, border_radius=8, bgcolor="#f0fdf4",
                                   border=ft.border.all(1, "#10b981"), width=350,
                                   content=ft.Row([
                                       ft.Icon("check_circle", color="#10b981", size=24),
                                       ft.Column([
                                           ft.Text(f"${txn['amount']}", size=18, weight="bold", color="#059669"),
                                           ft.Text(txn['time'], size=10, color="grey")
                                       ], spacing=2, expand=True),
                                       ft.Text(txn['token'][:10] + "...", size=10, color="grey")
                                   ], alignment="spaceBetween"))
                    )
            page.update()
        
        refresh_history()
        
        def process_payment(e):
            token_val = token_input.value.strip()
            
            print(f"\n{'='*50}")
            print(f"🔍 PROCESSING: {token_val}")
            print(f"{'='*50}")
            
            if not token_val:
                show_snack("Enter a token", "red")
                return
            
            response, status = api_client.redeem_token(token_val, session["merchant_id"])
            
            if status == 200:
                total_amt = response["amount"]
                vouchers = response["vouchers"]
                household_id = response["household_id"]
                
                print(f"✅ Success! ${total_amt}")
                print(f"{'='*50}\n")
                
                # Add to local transaction history
                session["transactions"].append({
                    "amount": total_amt,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "token": token_val,
                    "household": household_id
                })
                
                # Clear input and refresh
                token_input.value = ""
                refresh_history()
                
                # Show success
                voucher_text = ", ".join([f"${d}×{c}" for d, c in sorted(vouchers.items(), key=lambda x: int(x[0]))])
                
                def close_success(e):
                    page.dialog.open = False
                    page.update()
                
                page.dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Row([ft.Icon("check_circle", color="#10b981", size=40),
                                ft.Text("Success!", size=22, weight="bold", color="#059669")],
                               alignment="center", spacing=10),
                    content=ft.Container(width=300, content=ft.Column([
                        ft.Container(height=10),
                        ft.Container(padding=20, bgcolor="#d1fae5", border_radius=10,
                                   content=ft.Column([
                                       ft.Text("Total", size=12, color="#065f46"),
                                       ft.Text(f"${total_amt}", size=48, weight="bold", color="#059669")
                                   ], horizontal_alignment="center", spacing=2)),
                        ft.Container(height=10),
                        ft.Container(padding=15, bgcolor="#ecfdf5", border_radius=8, border=ft.border.all(1, "#10b981"),
                                   content=ft.Column([
                                       ft.Text("Vouchers", size=12, weight="bold", color="#065f46"),
                                       ft.Text(voucher_text, size=14, color="#059669")
                                   ], horizontal_alignment="center", spacing=5)),
                        ft.Container(height=10),
                        ft.Container(padding=10, bgcolor="#fef3c7", border_radius=6,
                                   content=ft.Text(f"Token: {token_val[:12]}...", size=10, color="#92400e", text_align="center"))
                    ], horizontal_alignment="center")),
                    actions=[ft.Container(
                        content=ft.ElevatedButton("Done", on_click=close_success, bgcolor="#10b981", color="white", width=250, height=45),
                        alignment=ft.alignment.center
                    )]
                )
                page.dialog.open = True
                page.update()
            else:
                error = response.get("error", "Unknown error")
                print(f"❌ {error}\n")
                show_snack(f"❌ {error}", "red")
        
        page.add(
            ft.AppBar(title=ft.Row([ft.Text("🏪", size=24), ft.Text(session['merchant_name'], size=18, weight="bold")], spacing=10),
                     center_title=True, bgcolor="#10b981", color="white",
                     leading=ft.IconButton(icon="store", icon_color="white"),
                     actions=[ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")]),
            ft.Column([
                ft.Container(height=20),
                
                # Info card
                ft.Container(padding=15, bgcolor="#ecfdf5", border_radius=10, width=350,
                           border=ft.border.all(1, "#10b981"),
                           content=ft.Column([
                               ft.Row([
                                   ft.Icon("credit_card", color="#10b981", size=30),
                                   ft.Column([
                                       ft.Text("Customer Redemption", size=18, weight="bold", color="#059669"),
                                       ft.Text("Enter voucher code", size=12, color="#065f46")
                                   ], expand=True)
                               ], spacing=10)
                           ])),
                
                ft.Container(height=20),
                
                # Token input
                token_input,
                
                ft.Container(height=15),
                
                # Process button
                ft.ElevatedButton("💳 Process Payment", on_click=process_payment, width=350, height=60,
                                bgcolor="#10b981", color="white",
                                style=ft.ButtonStyle(text_style=ft.TextStyle(size=18, weight="bold"))),
                
                ft.Container(height=30),
                
                # Transaction history
                ft.Container(
                    padding=15,
                    bgcolor="#f9fafb",
                    border_radius=10,
                    width=350,
                    content=ft.Column([
                        ft.Text("Recent Transactions", size=16, weight="bold", color="#1f2937"),
                        ft.Container(height=10),
                        history_column
                    ])
                )
                
            ], horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)
        )
        page.update()

    print("✅ All functions defined")
    print("🎨 Loading login view...")
    try:
        page.add(login_view())
        print("✅ Login view loaded")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("="*50)
print("🚀 Starting Flet on port 8551...")
print("="*50)
ft.app(target=main, port=8551)