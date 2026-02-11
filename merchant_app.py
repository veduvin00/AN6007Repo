"""
CDC Merchant App - Enhanced with Validation
UEN, Bank Code, and other field validations
FIXED: Voucher display logic updated to handle nested Tranche structure.
"""
import flet as ft
import re
import random
import time
from datetime import datetime

from api_client import api_client

def validate_uen(uen):
    """
    Validate Singapore UEN (Unique Entity Number)
    Format: 9 or 10 characters (digits and letters)
    Examples: 201234567A, T08GB0001A
    """
    if not uen:
        return False, "UEN is required"
    
    uen = uen.strip().upper()
    
    # UEN should be 9-10 characters
    if len(uen) < 9 or len(uen) > 10:
        return False, "UEN must be 9-10 characters"
    
    # Check format: starts with letter or digit, ends with letter
    if not re.match(r'^[A-Z0-9]{8,9}[A-Z]$', uen):
        return False, "Invalid UEN format (e.g., 201234567A or T08GB0001A)"
    
    return True, ""

def validate_bank_code(bank_code):
    """
    Validate Singapore bank code (4 digits)
    Common codes: DBS (7171), OCBC (7339), UOB (7375)
    """
    if not bank_code:
        return True, ""  # Optional field
    
    bank_code = bank_code.strip()
    
    if not re.match(r'^\d{4}$', bank_code):
        return False, "Bank code must be 4 digits"
    
    # Common Singapore bank codes
    valid_codes = {
        "7171": "DBS/POSB",
        "7339": "OCBC",
        "7375": "UOB",
        "6882": "Maybank",
        "7144": "Citibank",
        "7214": "Standard Chartered",
        "7232": "HSBC",
        "7302": "Bank of China"
    }
    
    if bank_code in valid_codes:
        return True, f"✓ {valid_codes[bank_code]}"
    else:
        return True, "⚠️ Uncommon bank code - please verify"

def validate_branch_code(branch_code):
    """Validate branch code (3 digits)"""
    if not branch_code:
        return True, ""  # Optional field
    
    branch_code = branch_code.strip()
    
    if not re.match(r'^\d{3}$', branch_code):
        return False, "Branch code must be 3 digits"
    
    return True, ""

def validate_account_number(account_number):
    """Validate bank account number (typically 7-12 digits)"""
    if not account_number:
        return True, ""  # Optional field
    
    account_number = account_number.strip()
    
    # Remove spaces and dashes
    account_number = account_number.replace(" ", "").replace("-", "")
    
    if not re.match(r'^\d{7,12}$', account_number):
        return False, "Account number must be 7-12 digits"
    
    return True, ""

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
                    ft.Text("Run: python app.py", size=14, color="blue"),
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

    # REGISTER WITH VALIDATION
    def register_view():
        page.controls.clear()
        
        # Input fields
        merchant_name_input = ft.TextField(label="Business Name*", width=350)
        uen_input = ft.TextField(label="UEN (Unique Entity Number)*", width=350, max_length=10)
        uen_error = ft.Text("", size=11, color="red", visible=False)
        uen_hint = ft.Text("Format: 201234567A or T08GB0001A", size=10, color="grey", italic=True)
        
        bank_name_input = ft.TextField(label="Bank Name", width=350)
        bank_code_input = ft.TextField(label="Bank Code (4 digits)", width=350, max_length=4)
        bank_code_status = ft.Text("", size=11, visible=False)
        bank_code_hint = ft.Text("DBS: 7171, OCBC: 7339, UOB: 7375", size=10, color="grey", italic=True)
        
        branch_code_input = ft.TextField(label="Branch Code (3 digits)", width=350, max_length=3)
        branch_error = ft.Text("", size=11, color="red", visible=False)
        
        account_number_input = ft.TextField(label="Account Number", width=350)
        account_error = ft.Text("", size=11, color="red", visible=False)
        
        account_holder_input = ft.TextField(label="Account Holder Name", width=350)
        
        result_container = ft.Column(horizontal_alignment="center", spacing=10)
        
        # Real-time validation functions
        def validate_uen_input(e):
            is_valid, message = validate_uen(uen_input.value)
            if uen_input.value and not is_valid:
                uen_error.value = message
                uen_error.visible = True
                uen_input.border_color = "red"
            else:
                uen_error.visible = False
                uen_input.border_color = "#10b981" if uen_input.value else None
            page.update()
        
        def validate_bank_code_input(e):
            if not bank_code_input.value:
                bank_code_status.visible = False
                bank_code_input.border_color = None
                page.update()
                return
            
            is_valid, message = validate_bank_code(bank_code_input.value)
            if is_valid and "✓" in message:
                bank_code_status.value = message
                bank_code_status.color = "green"
                bank_code_status.visible = True
                bank_code_input.border_color = "green"
            elif is_valid and "⚠️" in message:
                bank_code_status.value = message
                bank_code_status.color = "orange"
                bank_code_status.visible = True
                bank_code_input.border_color = "orange"
            else:
                bank_code_status.value = message
                bank_code_status.color = "red"
                bank_code_status.visible = True
                bank_code_input.border_color = "red"
            page.update()
        
        def validate_branch_input(e):
            is_valid, message = validate_branch_code(branch_code_input.value)
            if branch_code_input.value and not is_valid:
                branch_error.value = message
                branch_error.visible = True
                branch_code_input.border_color = "red"
            else:
                branch_error.visible = False
                branch_code_input.border_color = "#10b981" if branch_code_input.value else None
            page.update()
        
        def validate_account_input(e):
            is_valid, message = validate_account_number(account_number_input.value)
            if account_number_input.value and not is_valid:
                account_error.value = message
                account_error.visible = True
                account_number_input.border_color = "red"
            else:
                account_error.visible = False
                account_number_input.border_color = "#10b981" if account_number_input.value else None
            page.update()
        
        # Attach validators
        uen_input.on_change = validate_uen_input
        bank_code_input.on_change = validate_bank_code_input
        branch_code_input.on_change = validate_branch_input
        account_number_input.on_change = validate_account_input

        def submit_registration(e):
            # Validate required fields
            if not merchant_name_input.value or not merchant_name_input.value.strip():
                show_snack("Business name is required", "red")
                return
            
            # Validate UEN
            is_valid, message = validate_uen(uen_input.value)
            if not is_valid:
                show_snack(message, "red")
                uen_error.value = message
                uen_error.visible = True
                uen_input.border_color = "red"
                page.update()
                return
            
            # Validate bank code if provided
            if bank_code_input.value:
                is_valid, message = validate_bank_code(bank_code_input.value)
                if not is_valid:
                    show_snack(message, "red")
                    return
            
            # Validate branch code if provided
            if branch_code_input.value:
                is_valid, message = validate_branch_code(branch_code_input.value)
                if not is_valid:
                    show_snack(message, "red")
                    return
            
            # Validate account number if provided
            if account_number_input.value:
                is_valid, message = validate_account_number(account_number_input.value)
                if not is_valid:
                    show_snack(message, "red")
                    return

            # Generate unique merchant ID on frontend with collision check
            merchant_id = None
            max_attempts = 10
            
            for attempt in range(max_attempts):
                temp_id = f"M{random.randint(100, 999)}"
                # Check if ID exists by trying to get merchant
                check_response, check_status = api_client.get_merchant(temp_id)
                if check_status == 404:  # ID doesn't exist, it's unique!
                    merchant_id = temp_id
                    print(f"✅ Generated unique merchant ID: {merchant_id} (attempt {attempt + 1})")
                    break
                else:
                    print(f"⚠️  ID {temp_id} already exists, retrying... (attempt {attempt + 1})")
            
            if not merchant_id:
                # Fallback: use timestamp-based ID if all random attempts failed
                import time
                merchant_id = f"M{int(time.time()) % 1000:03d}"
                print(f"⚠️  Using timestamp-based ID: {merchant_id}")
            
            merchant_data = {
                "merchant_id": merchant_id,  # Add generated unique ID
                "merchant_name": merchant_name_input.value.strip(),
                "uen": uen_input.value.strip().upper(),
                "bank_name": bank_name_input.value.strip(),
                "bank_code": bank_code_input.value.strip(),
                "branch_code": branch_code_input.value.strip(),
                "account_number": account_number_input.value.strip(),
                "account_holder": account_holder_input.value.strip()
            }
            
            print(f"🔍 Registering merchant with ID: {merchant_id}")
            print(f"📝 Data: {merchant_data}")
            
            response, status = api_client.register_merchant(merchant_data)
            
            print(f"📬 Response: {response}, Status: {status}")
            
            if status in [200, 201]:
                new_mid = response.get("merchant_id", merchant_id)
                result_container.controls = [
                    ft.Container(padding=20, margin=ft.margin.only(top=20), border_radius=10,
                               bgcolor="#ecfdf5", border=ft.border.all(2, "#059669"), width=350,
                               content=ft.Column([
                                   ft.Icon("check_circle", color="green", size=50),
                                   ft.Text("Registration Successful!", size=20, weight="bold", color="green"),
                                   ft.Divider(),
                                   ft.Text("YOUR MERCHANT ID:", size=14, weight="bold"),
                                   ft.Container(bgcolor="#f3f4f6", padding=15, border_radius=8,
                                              content=ft.Text(new_mid, size=28, weight="bold", selectable=True)),
                                   ft.Text("SAVE THIS ID!", color="red", italic=True, size=12),
                                   ft.Container(height=10),
                                   ft.Container(
                                       padding=10,
                                       bgcolor="#f0f9ff",
                                       border_radius=8,
                                       content=ft.Column([
                                           ft.Text(f"Business: {merchant_data['merchant_name']}", size=12),
                                           ft.Text(f"UEN: {merchant_data['uen']}", size=12),
                                       ], spacing=5)
                                   ),
                                   ft.Container(height=20),
                                   ft.ElevatedButton("Go to Login", on_click=lambda _: (page.controls.clear(), page.add(login_view()), page.update()),
                                                   bgcolor="blue", color="white", width=280, height=50)
                               ], horizontal_alignment="center"))
                ]
            else:
                error_msg = response.get('error', 'Registration failed')
                print(f"❌ Registration failed: {error_msg}")
                show_snack(f"Error: {error_msg}", "red")
                
                # Also show error in the result container
                result_container.controls = [
                    ft.Container(
                        padding=20,
                        margin=ft.margin.only(top=20),
                        border_radius=10,
                        bgcolor="#fee2e2",
                        border=ft.border.all(2, "#dc2626"),
                        width=350,
                        content=ft.Column([
                            ft.Icon("error", color="red", size=50),
                            ft.Text("Registration Failed", size=20, weight="bold", color="red"),
                            ft.Divider(),
                            ft.Text(error_msg, size=14, color="#7f1d1d", text_align="center"),
                            ft.Container(height=10),
                            ft.Text("Please check your input and try again", size=12, color="grey", italic=True)
                        ], horizontal_alignment="center")
                    )
                ]
            page.update()

        page.add(
            ft.AppBar(title=ft.Row([ft.Text("🏪", size=24), ft.Text("Register Merchant", size=18, weight="bold")], spacing=10),
                     center_title=True, bgcolor="#10b981", color="white",
                     leading=ft.IconButton(icon="arrow_back", on_click=lambda _: logout(), icon_color="white")),
            ft.Column([
                ft.Text("Business Registration", size=20, weight="bold"),
                ft.Text("* Required fields", size=12, color="red", italic=True),
                ft.Container(height=10),
                
                # Business details
                ft.Container(
                    padding=15,
                    bgcolor="#f0fdf4",
                    border_radius=10,
                    width=350,
                    border=ft.border.all(1, "#10b981"),
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("business", color="#10b981", size=20),
                            ft.Text("Business Information", size=14, weight="bold", color="#065f46")
                        ]),
                        ft.Container(height=5),
                        merchant_name_input,
                        ft.Container(height=5),
                        uen_input,
                        uen_hint,
                        uen_error,
                    ], spacing=5)
                ),
                
                ft.Container(height=10),
                
                # Banking details
                ft.Container(
                    padding=15,
                    bgcolor="#f0f9ff",
                    border_radius=10,
                    width=350,
                    border=ft.border.all(1, "#3b82f6"),
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("account_balance", color="#3b82f6", size=20),
                            ft.Text("Banking Details (Optional)", size=14, weight="bold", color="#1e40af")
                        ]),
                        ft.Container(height=5),
                        bank_name_input,
                        ft.Container(height=5),
                        bank_code_input,
                        bank_code_hint,
                        bank_code_status,
                        ft.Container(height=5),
                        branch_code_input,
                        branch_error,
                        ft.Container(height=5),
                        account_number_input,
                        account_error,
                        ft.Container(height=5),
                        account_holder_input,
                    ], spacing=5)
                ),
                
                ft.Container(height=15),
                ft.ElevatedButton("Register Merchant", on_click=submit_registration, 
                                width=350, height=50, bgcolor="#10b981", color="white"),
                result_container
            ], horizontal_alignment="center", spacing=15, scroll=ft.ScrollMode.AUTO)
        )
        page.update()

    # ANALYTICS DASHBOARD
    def analytics_dashboard():
        page.controls.clear()
        
        # Read all CSV files from storage/redemptions
        import csv
        import os
        from datetime import datetime
        
        all_transactions = []
        merchant_transactions = []
        
        redemptions_dir = "storage/redemptions"
        
        if os.path.exists(redemptions_dir):
            csv_files = [f for f in os.listdir(redemptions_dir) if f.endswith('.csv')]
            
            for csv_file in csv_files:
                filepath = os.path.join(redemptions_dir, csv_file)
                try:
                    with open(filepath, 'r') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if len(row) >= 7:  # Ensure valid row
                                transaction_id = row[0]
                                household_id = row[1]
                                merchant_id = row[2]
                                timestamp = row[3]
                                token = row[4]
                                voucher_details = row[5]
                                total_amount = int(row[6]) if row[6].isdigit() else 0
                                
                                all_transactions.append({
                                    "transaction_id": transaction_id,
                                    "household_id": household_id,
                                    "merchant_id": merchant_id,
                                    "timestamp": timestamp,
                                    "token": token,
                                    "voucher_details": voucher_details,
                                    "amount": total_amount
                                })
                                
                                # Filter for current merchant
                                if merchant_id == session["merchant_id"]:
                                    merchant_transactions.append({
                                        "transaction_id": transaction_id,
                                        "household_id": household_id,
                                        "timestamp": timestamp,
                                        "token": token,
                                        "voucher_details": voucher_details,
                                        "amount": total_amount,
                                        "time": datetime.strptime(timestamp, "%Y%m%d%H%M%S").strftime("%H:%M:%S") if len(timestamp) == 14 else timestamp
                                    })
                except Exception as e:
                    print(f"Error reading {csv_file}: {e}")
        
        # Calculate analytics from merchant transactions
        total_transactions = len(merchant_transactions)
        total_revenue = sum(txn["amount"] for txn in merchant_transactions)
        
        # Today's transactions
        today = datetime.now().strftime("%Y%m%d")
        today_transactions = [txn for txn in merchant_transactions if txn["timestamp"].startswith(today)]
        today_count = len(today_transactions)
        today_revenue = sum(txn["amount"] for txn in today_transactions)
        
        # Average transaction value
        avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Voucher amount breakdown
        amount_breakdown = {}
        for txn in merchant_transactions:
            amount = txn["amount"]
            if amount in amount_breakdown:
                amount_breakdown[amount] += 1
            else:
                amount_breakdown[amount] = 1
        
        # Recent transactions list (last 10)
        recent_txns = sorted(merchant_transactions, key=lambda x: x["timestamp"], reverse=True)[:10]
        
        # Stats cards
        def stat_card(title, value, icon, color, subtitle=""):
            return ft.Container(
                width=165,
                height=140,
                padding=15,
                border_radius=12,
                bgcolor=f"{color}20",
                border=ft.border.all(2, color),
                content=ft.Column([
                    ft.Icon(icon, color=color, size=35),
                    ft.Container(height=5),
                    ft.Text(title, size=11, color="grey", weight="bold"),
                    ft.Text(str(value), size=28, weight="bold", color=color),
                    ft.Text(subtitle, size=10, color="grey", italic=True) if subtitle else ft.Container()
                ], horizontal_alignment="center", spacing=3)
            )
        
        page.add(
            ft.AppBar(
                title=ft.Row([ft.Text("📊", size=24), ft.Text("Analytics Dashboard", size=18, weight="bold")], spacing=10),
                center_title=True, bgcolor="#10b981", color="white",
                leading=ft.IconButton(icon="arrow_back", on_click=lambda _: merchant_terminal(), icon_color="white"),
                actions=[ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")]
            ),
            ft.Column([
                ft.Container(height=20),
                
                # Title
                ft.Text("Business Performance", size=22, weight="bold", color="#1f2937"),
                ft.Text(f"Merchant: {session['merchant_name']}", size=14, color="grey"),
                
                ft.Container(height=20),
                
                # Stats row
                ft.Row([
                    stat_card("Total Revenue", f"${total_revenue}", "attach_money", "#10b981", "All time"),
                    stat_card("Transactions", total_transactions, "receipt_long", "#3b82f6", "All time")
                ], spacing=10, wrap=True),
                
                ft.Container(height=10),
                
                ft.Row([
                    stat_card("Today's Sales", f"${today_revenue}", "trending_up", "#f59e0b", f"{today_count} transactions"),
                    stat_card("Avg Transaction", f"${avg_transaction:.2f}", "payments", "#8b5cf6", "Per redemption")
                ], spacing=10, wrap=True),
                
                ft.Container(height=25),
                
                # Voucher breakdown
                ft.Container(
                    width=350,
                    padding=20,
                    border_radius=12,
                    bgcolor="#f9fafb",
                    border=ft.border.all(1, "#e5e7eb"),
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("pie_chart", color="#10b981", size=24),
                            ft.Text("Amount Breakdown", size=16, weight="bold", color="#1f2937")
                        ]),
                        ft.Divider(),
                        ft.Column([
                            ft.Row([
                                ft.Container(
                                    padding=8,
                                    border_radius=6,
                                    bgcolor="#10b981",
                                    content=ft.Text(f"${amount}", size=14, weight="bold", color="white")
                                ),
                                ft.Text(f"{count} transactions", size=14, color="#6b7280", expand=True),
                                ft.Text(f"${amount * count}", size=14, weight="bold", color="#059669")
                            ], alignment="spaceBetween")
                            for amount, count in sorted(amount_breakdown.items(), reverse=True)
                        ], spacing=8) if amount_breakdown else ft.Text("No transactions yet", color="grey", italic=True)
                    ], spacing=10)
                ),
                
                ft.Container(height=25),
                
                # Recent transactions
                ft.Container(
                    width=350,
                    padding=20,
                    border_radius=12,
                    bgcolor="#f9fafb",
                    border=ft.border.all(1, "#e5e7eb"),
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("history", color="#3b82f6", size=24),
                            ft.Text("Recent Transactions", size=16, weight="bold", color="#1f2937")
                        ]),
                        ft.Divider(),
                        ft.Column([
                            ft.Container(
                                padding=12,
                                border_radius=8,
                                bgcolor="#ffffff",
                                border=ft.border.all(1, "#e5e7eb"),
                                content=ft.Row([
                                    ft.Column([
                                        ft.Text(f"${txn['amount']}", size=18, weight="bold", color="#059669"),
                                        ft.Text(txn['time'], size=10, color="grey")
                                    ], spacing=2),
                                    ft.Column([
                                        ft.Text(txn['token'][:12] + "...", size=11, color="#6b7280"),
                                        ft.Text(txn['household_id'][:15] + "...", size=10, color="grey")
                                    ], spacing=2, horizontal_alignment="end")
                                ], alignment="spaceBetween")
                            )
                            for txn in recent_txns
                        ], spacing=8) if recent_txns else ft.Text("No transactions yet", color="grey", italic=True)
                    ], spacing=10)
                ),
                
                ft.Container(height=20),
                
                # Back to terminal button
                ft.ElevatedButton(
                    "🏪 Back to Terminal",
                    on_click=lambda _: merchant_terminal(),
                    width=350,
                    height=50,
                    bgcolor="#10b981",
                    color="white",
                    style=ft.ButtonStyle(text_style=ft.TextStyle(size=16, weight="bold"))
                )
                
            ], horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)
        )
        page.update()

    # MERCHANT TERMINAL
    def merchant_terminal():
        page.controls.clear()
        
        token_input = ft.TextField(
            label="Enter Customer Token",
            width=350,
            height=60,
            text_size=18,
            prefix_icon="qr_code_scanner",
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
                vouchers_data = response["vouchers"] # Can be nested {Tranche: {Denom: Count}} or flat
                household_id = response["household_id"]
                
                print(f"✅ Success! ${total_amt}")
                
                # Add to local transaction history
                session["transactions"].append({
                    "amount": total_amt,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "token": token_val,
                    "household": household_id
                })
                
                # Clear input
                token_input.value = ""
                
                # Show success message
                show_snack(f"✅ Successfully redeemed ${total_amt}!", "green")
                
                # FIXED: Generate voucher breakdown text robustly (handling nested dicts)
                details = []
                # Check if nested (Tranche -> Denom) or flat (Denom)
                is_nested = any(isinstance(v, dict) for v in vouchers_data.values())
                
                if is_nested:
                    for tr, denoms in vouchers_data.items():
                            for d, c in denoms.items():
                                details.append(f"{tr}: ${d}x{c}")
                else:
                    for d, c in sorted(vouchers_data.items(), key=lambda x: int(x[0])):
                        details.append(f"${d}x{c}")
                
                voucher_text = "\n".join(details)
                
                # Rebuild page with success message
                page.controls.clear()
                
                page.add(
                    ft.AppBar(
                        title=ft.Row([ft.Text("🏪", size=24), ft.Text(session['merchant_name'], size=18, weight="bold")], spacing=10),
                        center_title=True, bgcolor="#10b981", color="white",
                        leading=ft.IconButton(icon="store", icon_color="white"),
                        actions=[
                            ft.IconButton(icon="analytics", on_click=lambda _: analytics_dashboard(), 
                                        tooltip="Analytics Dashboard", icon_color="white"),
                            ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")
                        ]
                    ),
                    ft.Column([
                        ft.Container(height=20),
                        
                        # SUCCESS MESSAGE CARD
                        ft.Container(
                            width=350,
                            padding=20,
                            border_radius=12,
                            bgcolor="#d1fae5",
                            border=ft.border.all(3, "#10b981"),
                            shadow=ft.BoxShadow(spread_radius=2, blur_radius=10, color="#86efac"),
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon("check_circle", color="#10b981", size=50),
                                    ft.Text("Payment Success!", size=24, weight="bold", color="#059669")
                                ], alignment="center", spacing=10),
                                
                                ft.Divider(color="#10b981"),
                                
                                # Amount
                                ft.Container(
                                    padding=20,
                                    bgcolor="#ecfdf5",
                                    border_radius=10,
                                    content=ft.Column([
                                        ft.Text("Amount Redeemed", size=14, color="#065f46"),
                                        ft.Text(f"${total_amt}", size=56, weight="bold", color="#059669")
                                    ], horizontal_alignment="center", spacing=5)
                                ),
                                
                                ft.Container(height=10),
                                
                                # Vouchers breakdown
                                ft.Container(
                                    padding=15,
                                    bgcolor="#f0fdf4",
                                    border_radius=8,
                                    border=ft.border.all(1, "#10b981"),
                                    content=ft.Column([
                                        ft.Text("Vouchers Used", size=12, weight="bold", color="#065f46"),
                                        ft.Text(voucher_text, size=14, color="#059669", weight="bold", text_align="center")
                                    ], horizontal_alignment="center", spacing=5)
                                ),
                                
                                ft.Container(height=10),
                                
                                # Transaction details
                                ft.Container(
                                    padding=12,
                                    bgcolor="#fef3c7",
                                    border_radius=8,
                                    content=ft.Column([
                                        ft.Text("Transaction Details", size=11, weight="bold", color="#92400e"),
                                        ft.Text(f"Token: {token_val}", size=11, color="#92400e"),
                                        ft.Text(f"Time: {datetime.now().strftime('%H:%M:%S')}", size=11, color="#92400e"),
                                        ft.Text(f"Household: {household_id}", size=11, color="#92400e")
                                    ], horizontal_alignment="center", spacing=3)
                                ),
                                
                                ft.Container(height=15),
                                
                                # Back button
                                ft.ElevatedButton(
                                    "Process Another Payment",
                                    on_click=lambda _: merchant_terminal(),
                                    width=310,
                                    height=50,
                                    bgcolor="#10b981",
                                    color="white",
                                    style=ft.ButtonStyle(text_style=ft.TextStyle(size=16, weight="bold"))
                                )
                            ], horizontal_alignment="center", spacing=10)
                        ),
                        
                        ft.Container(height=20),
                        
                        # Transaction history
                        ft.Container(
                            padding=15,
                            bgcolor="#f9fafb",
                            border_radius=10,
                            width=350,
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon("receipt_long", color="#1f2937", size=20),
                                    ft.Text("Recent Transactions", size=16, weight="bold", color="#1f2937")
                                ]),
                                ft.Container(height=10),
                            ] + [
                                ft.Container(
                                    padding=12,
                                    border_radius=8,
                                    bgcolor="#f0fdf4",
                                    border=ft.border.all(1, "#10b981"),
                                    width=350,
                                    content=ft.Row([
                                        ft.Icon("check_circle", color="#10b981", size=24),
                                        ft.Column([
                                            ft.Text(f"${txn['amount']}", size=18, weight="bold", color="#059669"),
                                            ft.Text(txn['time'], size=10, color="grey")
                                        ], spacing=2, expand=True),
                                        ft.Text(txn['token'][:10] + "...", size=10, color="grey")
                                    ], alignment="spaceBetween")
                                )
                                for txn in list(reversed(session["transactions"]))[:5]
                            ])
                        )
                        
                    ], horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)
                )
                
                page.update()
            else:
                error = response.get("error", "Unknown error")
                print(f"❌ {error}\n")
                show_snack(f"❌ {error}", "red")
        
        page.add(
            ft.AppBar(title=ft.Row([ft.Text("🏪", size=24), ft.Text(session['merchant_name'], size=18, weight="bold")], spacing=10),
                     center_title=True, bgcolor="#10b981", color="white",
                     leading=ft.IconButton(icon="store", icon_color="white"),
                     actions=[
                         ft.IconButton(icon="analytics", on_click=lambda _: analytics_dashboard(), 
                                     tooltip="Analytics Dashboard", icon_color="white"),
                         ft.IconButton(icon="logout", on_click=lambda _: logout(), icon_color="white")
                     ]),
            ft.Column([
                ft.Container(height=20),
                
                # Info card
                ft.Container(padding=15, bgcolor="#ecfdf5", border_radius=10, width=350,
                           border=ft.border.all(1, "#10b981"),
                           content=ft.Column([
                               ft.Row([
                                   ft.Icon("credit_card", color="#10b981", size=30),
                                   ft.Column([
                                       ft.Text("Voucher Redemption", size=18, weight="bold", color="#059669"),
                                       ft.Text("Scan or enter customer token", size=12, color="#065f46")
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
                        ft.Row([
                            ft.Icon("receipt_long", color="#1f2937", size=20),
                            ft.Text("Recent Transactions", size=16, weight="bold", color="#1f2937")
                        ]),
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