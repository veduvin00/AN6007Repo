import flet as ft
from services.household_service import (
    register_household,
    get_redemption_balance,
    load_households,
)
from services.voucher_service import claim_voucher
from services.redemption_service import redeem_voucher
from services.merchant_service import register_merchant

# ==========================================
# Reusable UI Components & Styles
# ==========================================

APP_HEADER_COLOR = "#212529"  # Dark Grey/Black
BG_COLOR = "#f3f4f6"          # Light Grey Background
CARD_BG = "#ffffff"           # White
SUCCESS_GREEN = "#198754"     # Bootstrap Success Green
ACTION_BLUE = "#0d6efd"       # Bootstrap Primary Blue

def create_header():
    """Creates the top banner matching the screenshots."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.icons.CARD_GIFTCHARD, color="green400", size=30),
                ft.Text("CDC", size=24, weight="bold", color=ACTION_BLUE),
                ft.Text("Voucher System", size=24, weight="bold", color="green400"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=APP_HEADER_COLOR,
        padding=20,
        width=float("inf"), # Full width
    )

def create_card_container(content_control):
    """Wraps content in a white card with shadow."""
    return ft.Container(
        content=content_control,
        bgcolor=CARD_BG,
        padding=30,
        border_radius=10,
        shadow=ft.BoxShadow(
            blur_radius=15,
            spread_radius=1,
            color="#1A000000", # Hex for black with low opacity (10%)
            offset=ft.Offset(0, 4),
        ),
        margin=ft.margin.only(bottom=20)
    )

def create_input_field(label, hint_text=None, expand=False):
    """Standardized styled text field."""
    return ft.TextField(
        label=label,
        hint_text=hint_text,
        border_color="grey400",  # Changed to string
        text_size=14,
        content_padding=15,
        border_radius=5,
        expand=expand,
        filled=True,
        fill_color="white"       # Changed to string
    )

def create_voucher_display_card(amount, count, tranche_name="Jan2026"):
    """
    Creates the small denomination cards seen in the 'Balance' and 'Redeem' screenshots.
    Visual: White card, Green badge top right, Centered Amount.
    """
    return ft.Container(
        width=180,
        height=120,
        bgcolor="white", # Changed to string
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=5, color="#1A000000"), # Hex for shadow
        padding=0,
        content=ft.Stack([
            # Badge
            ft.Container(
                content=ft.Text(tranche_name, color="white", size=10, weight="bold"),
                bgcolor=SUCCESS_GREEN,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=ft.border_radius.only(top_right=10, bottom_left=5),
                right=0,
                top=0,
            ),
            # Content
            ft.Column([
                ft.Text(f"${amount}", size=28, weight="bold", color="black87"),
                ft.Text(f"{count}", size=18, weight="bold", color="black87"),
                ft.Text("vouchers available" if count != "remaining" else "remaining", size=12, color="grey600"),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        ], alignment=ft.Alignment(0, 0)) # Stack alignment
    )

# ==========================================
# Main Application
# ==========================================

def main(page: ft.Page):
    page.title = "CDC Voucher Mobile App"
    page.bgcolor = BG_COLOR
    page.padding = 0  # Remove default padding to allow header to touch edges
    page.theme_mode = ft.ThemeMode.LIGHT

    # Initialize Data
    load_households()

    # --- Shared Feedback Element ---
    snack_bar = ft.SnackBar(content=ft.Text(""))
    page.overlay.append(snack_bar)

    def show_message(message, is_error=False):
        snack_bar.content.value = str(message)
        snack_bar.bgcolor = "red600" if is_error else SUCCESS_GREEN # Changed to string
        snack_bar.open = True
        page.update()

    # ==========================================
    # VIEW 1: REGISTER HOUSEHOLD (Admin)
    # ==========================================
    rh_members = create_input_field("Household Members (comma-separated)")
    rh_postal = create_input_field("Postal Code")
    rh_result = ft.Column() 

    def register_household_click(e):
        if not rh_members.value or not rh_postal.value:
            show_message("Please fill in all fields", True)
            return
            
        data = {
            "members": [m.strip() for m in rh_members.value.split(",")],
            "postal_code": rh_postal.value
        }
        response, status = register_household(data)
        
        # Mimic the success screen in screenshot
        if status == 201: # Assuming 201 is success
            rh_result.controls = [
                ft.Container(height=20),
                ft.Icon(ft.icons.CHECK, color="black87", size=50),
                ft.Text("Household registered successfully", color=SUCCESS_GREEN, size=18, weight="bold"),
                ft.Row([
                    ft.Icon(ft.icons.HOME, size=16),
                    ft.Text(f"Household ID: {response.get('household_id', 'N/A')}", size=16, weight="bold")
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.OutlinedButton("Go to Claim Page", on_click=lambda _: page.go("/claim"))
            ]
            rh_members.value = ""
            rh_postal.value = ""
        else:
             show_message(f"Error: {response}", True)
        
        page.update()

    view_reg_household = ft.Column([
        ft.Text("Register Household", size=24, weight="bold", color="black87"),
        create_card_container(
            ft.Column([
                rh_members,
                ft.Container(height=10),
                rh_postal,
                ft.Container(height=20),
                ft.ElevatedButton("Register Household", on_click=register_household_click, bgcolor=ACTION_BLUE, color="white", height=45, width=200),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ),
        ft.Container(content=rh_result, alignment=ft.alignment.center)
    ], scroll=ft.ScrollMode.AUTO)


    # ==========================================
    # VIEW 2: CLAIM VOUCHER (User)
    # ==========================================
    cv_hid = create_input_field("Household ID", "e.g., H990...")
    cv_tranche = ft.Dropdown(
        label="Voucher Tranche",
        options=[ft.dropdown.Option("Jan2026"), ft.dropdown.Option("Jan2025")],
        border_color="grey400", # Changed to string
        content_padding=15,
        border_radius=5,
        filled=True,
        fill_color="white"
    )
    cv_result = ft.Text("", size=16, weight="bold", color=SUCCESS_GREEN)

    def claim_voucher_click(e):
        if not cv_hid.value or not cv_tranche.value:
            show_message("Please enter ID and select tranche", True)
            return

        response, status = claim_voucher(cv_hid.value, {"tranche": cv_tranche.value})
        show_message(f"Result: {response}")
        cv_result.value = f"Status: {response}"
        page.update()

    view_claim = ft.Column([
        ft.Text("Claim CDC Voucher", size=24, weight="bold", color="black87"),
        create_card_container(
            ft.Column([
                ft.Row([ft.Icon(ft.icons.HOME, color="brown"), cv_hid]),
                ft.Container(height=10),
                ft.Text("Voucher Tranche", size=14),
                cv_tranche,
                ft.Container(height=20),
                ft.ElevatedButton("Claim Voucher", on_click=claim_voucher_click, bgcolor=SUCCESS_GREEN, color="white", height=45, width=200),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ),
        cv_result
    ])

    # ==========================================
    # VIEW 3: VOUCHER BALANCE (User)
    # ==========================================
    vb_hid = create_input_field("Household ID")
    vb_cards_row = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=20)
    
    def check_balance_click(e):
        if not vb_hid.value:
            show_message("Please enter Household ID", True)
            return
            
        response, status = get_redemption_balance(vb_hid.value)
        vb_cards_row.controls.clear()
        
        # Assuming response is a dict like {'2': 10, '5': 5, '10': 2} or similar structure
        if isinstance(response, dict):
             # Sort keys to ensure $2, $5, $10 order
             sorted_keys = sorted(response.keys(), key=lambda x: int(x) if x.isdigit() else 0)
             for denom in sorted_keys:
                 count = response[denom]
                 vb_cards_row.controls.append(create_voucher_display_card(denom, count))
        else:
            vb_cards_row.controls.append(ft.Text(str(response)))

        page.update()

    view_balance = ft.Column([
        ft.Text("Voucher Balance", size=24, weight="bold", color="black87"),
        create_card_container(
            ft.Column([
                ft.Row([ft.Icon(ft.icons.SEARCH), vb_hid], alignment=ft.MainAxisAlignment.CENTER),
                ft.ElevatedButton("Check Balance", on_click=check_balance_click, bgcolor="grey800", color="white", height=40),
            ])
        ),
        ft.Divider(),
        ft.Text("Jan2026 Tranche", size=20, weight="bold", text_align=ft.TextAlign.CENTER),
        ft.Container(height=10),
        vb_cards_row
    ])

    # ==========================================
    # VIEW 4: REDEEM VOUCHER (User Transaction)
    # ==========================================
    rv_hid = create_input_field("Household ID")
    rv_mid = create_input_field("Merchant ID")
    rv_amt = create_input_field("Quantity/Amount") 
    
    # Placeholder for balance display within redeem view (as per screenshot)
    rv_balance_display = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    def load_balance_for_redeem(e):
        # Quick helper to show balance before redeeming
        if rv_hid.value:
            response, status = get_redemption_balance(rv_hid.value)
            rv_balance_display.controls.clear()
            if isinstance(response, dict):
                 sorted_keys = sorted(response.keys(), key=lambda x: int(x) if x.isdigit() else 0)
                 for denom in sorted_keys:
                     rv_balance_display.controls.append(create_voucher_display_card(denom, response[denom]))
            page.update()

    def redeem_click(e):
        if not all([rv_hid.value, rv_mid.value, rv_amt.value]):
             show_message("All fields are required", True)
             return

        data = {
            "merchant_id": rv_mid.value,
            "amount": rv_amt.value
        }
        response, status = redeem_voucher(rv_hid.value, data)
        
        if status == 200: # Assuming 200 success
             show_message("Redemption Successful!")
             # Refresh balance
             load_balance_for_redeem(None)
        else:
             show_message(f"Failed: {response}", True)
             
        page.update()

    view_redeem = ft.Column([
        ft.Text("Redeem CDC Voucher", size=24, weight="bold", color="black87"),
        # Balance Section at Top
        ft.Container(
            content=ft.Column([
                ft.Text("Current Balance (Enter ID to load)", size=14, color="grey600"),
                ft.Row([rv_hid, ft.IconButton(ft.icons.REFRESH, on_click=load_balance_for_redeem)]),
                rv_balance_display
            ]),
            padding=10
        ),
        # Form Section
        create_card_container(
            ft.Column([
                ft.Text("Merchant Details", weight="bold"),
                rv_mid,
                ft.Container(height=10),
                ft.Text("Redemption Details", weight="bold"),
                rv_amt,
                ft.Container(height=20),
                ft.ElevatedButton("Confirm Redemption", on_click=redeem_click, bgcolor=ACTION_BLUE, color="white", width=float("inf"), height=50),
            ])
        )
    ])

    # ==========================================
    # VIEW 5: REGISTER MERCHANT (Business)
    # ==========================================
    rm_id = create_input_field("Merchant ID")
    rm_name = create_input_field("Merchant Name")
    rm_uen = create_input_field("UEN")
    # Grouping Bank Details
    rm_bank_name = create_input_field("Bank Name", expand=True)
    rm_bank_code = create_input_field("Bank Code", expand=True)
    rm_branch_code = create_input_field("Branch Code")
    rm_acc_num = create_input_field("Account Number")
    rm_acc_hold = create_input_field("Account Holder")

    def register_merchant_click(e):
        data = {
            "merchant_id": rm_id.value,
            "merchant_name": rm_name.value,
            "uen": rm_uen.value,
            "bank_name": rm_bank_name.value,
            "bank_code": rm_bank_code.value,
            "branch_code": rm_branch_code.value,
            "account_number": rm_acc_num.value,
            "account_holder": rm_acc_hold.value
        }
        response, status = register_merchant(data)
        show_message(str(response))
        page.update()

    view_reg_merchant = ft.Column([
        ft.Text("Register Merchant", size=24, weight="bold", color="black87"),
        create_card_container(
            ft.Column([
                rm_id,
                rm_name,
                rm_uen,
                ft.Divider(),
                ft.Text("Bank Details", weight="bold", color="grey700"),
                ft.Row([rm_bank_name, rm_bank_code]),
                rm_branch_code,
                rm_acc_num,
                rm_acc_hold,
                ft.Container(height=20),
                ft.ElevatedButton("Register Merchant", on_click=register_merchant_click, bgcolor=SUCCESS_GREEN, color="white", height=50, width=200),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
    ], scroll=ft.ScrollMode.AUTO)

    # ==========================================
    # NAVIGATION LOGIC
    # ==========================================
    
    # We use a Dictionary to map NavRail indices to the Views
    views_map = {
        0: view_reg_household,
        1: view_claim,
        2: view_balance,
        3: view_redeem,
        4: view_reg_merchant
    }
    
    content_area = ft.Container(content=view_reg_household, expand=True, padding=30)

    def nav_change(e):
        selected_index = e.control.selected_index
        content_area.content = views_map[selected_index]
        page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.PERSON_ADD, 
                selected_icon=ft.icons.PERSON_ADD_ALT_1, 
                label="Register\nHousehold"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.CARD_GIFTCHARD, 
                selected_icon=ft.icons.CARD_GIFTCHARD_SHARP, 
                label="Claim"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.ACCOUNT_BALANCE_WALLET, 
                selected_icon=ft.icons.ACCOUNT_BALANCE_WALLET_SHARP, 
                label="Balance"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SHOPPING_CART, 
                selected_icon=ft.icons.SHOPPING_CART_SHARP, 
                label="Redeem"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.STORE, 
                selected_icon=ft.icons.STORE_MALL_DIRECTORY, 
                label="Register\nMerchant"
            ),
        ],
        on_change=nav_change,
        bgcolor="white", # Changed to string
    )

    # Layout Assembly
    page.add(
        create_header(),
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1, color="grey300"), # Changed to string
                content_area,
            ],
            expand=True,
        )
    )

# Use ft.app(main) which is the standard way to run
ft.app(main)