import flet as ft
import time

# Note: Ensure these services are in your directory or mock them for testing
from services.merchant_service import (
    merchants,
    load_merchants,
    register_merchant
)
from services.household_service import (
    get_redemption_balance,
    households,
    load_households
)
from services.redemption_service import redeem_voucher

# =========================
# Utils
# =========================
def resolve_household_from_redeem_token(token):
    now = time.time()
    for hid, h in households.items():
        if (
            h.get("redeem_token") == token
            and h.get("redeem_expiry", 0) > now
        ):
            return hid
    return None

# =========================
# Main Application
# =========================
def main(page: ft.Page):
    page.title = "CDC Merchant Terminal"
    page.bgcolor = "#f5f5f5"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    load_merchants()
    load_households()

    # Temporary in-memory session
    current_merchant = {"mid": None, "mname": None}

    # =========================
    # UI Helpers
    # =========================
    def card(title, controls, width=700):
        return ft.Container(
            width=width,
            padding=24,
            border_radius=16,
            bgcolor="white",
            shadow=ft.BoxShadow(blur_radius=14, color="#0000001F"),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                controls=[ft.Text(title, size=26, weight="bold")] + controls
            )
        )

    def error_text(text):
        return ft.Text(text, color="red", weight="bold")

    def success_box(text):
        return ft.Container(
            padding=16,
            border_radius=12,
            bgcolor="#ecfdf5",
            content=ft.Text(text, color="#15803d", weight="bold")
        )

    # =========================
    # Navigation & Logout Logic
    # =========================
    def logout(e=None):
        # Reset state
        current_merchant["mid"] = None
        current_merchant["mname"] = None
        # Remove AppBar and redirect
        page.appbar = None
        show_login()

    # =========================
    # View: Login
    # =========================
    def show_login():
        page.clean()
        page.appbar = None # Ensure no appbar on login

        merchant_input = ft.TextField(
            label="Merchant ID",
            width=360,
            prefix_icon="store"
        )
        msg = ft.Column()

        def login(e=None):
            msg.controls.clear()
            mid = merchant_input.value.strip()

            if mid in merchants:
                current_merchant["mid"] = mid
                current_merchant["mname"] = merchants[mid].get("merchant_name", "Merchant")
                show_terminal()
            else:
                msg.controls.append(error_text("Merchant ID not found"))
                page.update()

        page.add(
            card(
                "Merchant Login",
                [
                    merchant_input,
                    ft.ElevatedButton("Login", width=360, on_click=login),
                    ft.TextButton("Register New Merchant", on_click=lambda _: show_register()),
                    msg
                ],
                width=500
            )
        )
        page.update()

    # =========================
    # View: Register
    # =========================
    def show_register():
        page.clean()
        
        fields = {
            "merchant_id": ft.TextField(label="Merchant ID"),
            "merchant_name": ft.TextField(label="Merchant Name"),
            "uen": ft.TextField(label="UEN"),
            "bank_name": ft.TextField(label="Bank Name"),
            "bank_code": ft.TextField(label="Bank Code"),
            "branch_code": ft.TextField(label="Branch Code"),
            "account_number": ft.TextField(label="Account Number"),
            "account_holder": ft.TextField(label="Account Holder"),
        }
        result = ft.Column()

        def submit(e):
            result.controls.clear()
            try:
                register_merchant({k: f.value for k, f in fields.items()})
                result.controls.append(success_box("Merchant registered successfully"))
            except Exception as ex:
                result.controls.append(error_text(str(ex)))
            page.update()

        page.add(
            card(
                "Register Merchant",
                list(fields.values()) + [
                    ft.ElevatedButton("Register", on_click=submit, width=360),
                    ft.TextButton("Back to Login", on_click=lambda _: show_login()),
                    result
                ],
                width=600
            )
        )
        page.update()

    # =========================
    # View: Merchant Terminal
    # =========================
    def show_terminal():
        page.clean()

        mid = current_merchant["mid"]
        mname = current_merchant["mname"]

        page.appbar = ft.AppBar(
            title=ft.Text(f"{mname} ({mid})"),
            bgcolor="#eeeeee",
            leading=ft.Icon("store"),
            actions=[
                # [Fix] Added 'icon=' parameter to fix the error
                ft.IconButton(icon = ft.Icons.LOGOUT, tooltip="Logout", on_click=logout)
            ]
        )

        token_input = ft.TextField(
            label="Redeem Token",
            width=420,
            text_align="center"
        )
        
        # [Design Update] Removed Quantity Input Field based on your feedback
        
        vouchers_ui = ft.Column(spacing=20)
        result_ui = ft.Column()
        sel = {"hid": None, "tranche": None, "amount": None}

        def load_vouchers(e=None):
            vouchers_ui.controls.clear()
            result_ui.controls.clear()

            hid = resolve_household_from_redeem_token(token_input.value.strip())
            if not hid:
                result_ui.controls.append(error_text("Invalid or expired token"))
                page.update()
                return

            sel["hid"] = hid
            bal, _ = get_redemption_balance(hid)

            for tranche, denoms in bal["vouchers"].items():
                cards = []
                for amt, cnt in denoms.items():
                    if cnt <= 0: continue

                    selected = (sel["tranche"] == tranche and sel["amount"] == amt)

                    def choose(e, t=tranche, a=amt):
                        sel.update({"tranche": t, "amount": a})
                        load_vouchers()

                    cards.append(
                        ft.Container(
                            width=160,
                            padding=16,
                            border_radius=14,
                            bgcolor="#dbeafe" if selected else "white",
                            border=ft.border.all(2, "#2563eb" if selected else "#e5e7eb"),
                            on_click=choose,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=6,
                                controls=[
                                    ft.Text(tranche, size=12, weight="bold"),
                                    ft.Text(f"${amt}", size=26, weight="bold"),
                                    ft.Text(f"{cnt} available", size=12)
                                ]
                            )
                        )
                    )

                vouchers_ui.controls.append(
                    ft.Column(
                        controls=[
                            ft.Text(tranche, weight="bold"),
                            ft.Row(wrap=True, spacing=16, controls=cards)
                        ]
                    )
                )
            page.update()

        def confirm(e):
            result_ui.controls.clear()
            if not sel["hid"] or not sel["amount"]:
                result_ui.controls.append(error_text("Please select a voucher first"))
                page.update()
                return

            # [Logic Update] Default quantity to 1 since we removed the input
            qty = 1

            res, status = redeem_voucher(
                sel["hid"],
                {
                    "merchant_id": mid,
                    "voucher_code": sel["tranche"],
                    "denomination": str(sel["amount"]),
                    "amount": qty
                }
            )

            if status == 200:
                result_ui.controls.append(success_box(f"Redeemed 1 Voucher!\nTX: {res['transaction_id']}"))
                # Clear selection after success
                sel["tranche"] = None
                sel["amount"] = None
                load_vouchers() # Refresh balance
            else:
                result_ui.controls.append(error_text(res.get("error", "Redemption failed")))
            page.update()

        page.add(
            card(
                "Redeem Voucher",
                [
                    token_input,
                    ft.ElevatedButton("Verify Token", on_click=load_vouchers),
                    
                    # Vouchers display area
                    vouchers_ui,
                    
                    # [Design Update] Removed Quantity Input from UI
                    
                    ft.ElevatedButton("Confirm Redemption (1 Qty)", on_click=confirm, width=420),
                    result_ui
                ],
                width=900
            )
        )
        page.update()

    # Initial view
    show_login()

if __name__ == "__main__":
    ft.app(target=main)