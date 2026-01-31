import flet as ft
import time
from services.merchant_service import merchants, load_merchants
from services.household_service import get_redemption_balance, households, load_households
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
# App
# =========================
def main(page: ft.Page):
    page.title = "CDC Merchant Terminal"
    page.bgcolor = "#f5f5f5"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    load_merchants()
    load_households()

    # =========================
    # UI helpers
    # =========================
    def card(title, controls, width=600):
        return ft.Container(
            width=width,
            padding=24,
            border_radius=16,
            bgcolor="white",
            content=ft.Column(
                horizontal_alignment="center",
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
            content=ft.Text(text, color="green", weight="bold")
        )

    # =========================
    # Login
    # =========================
    def show_login():
        page.clean()

        merchant_input = ft.TextField(
            label="Merchant ID",
            width=350,
            prefix_icon="store"
        )

        msg = ft.Column()

        def login(e=None):
            msg.controls.clear()
            mid = merchant_input.value.strip()
            if mid in merchants:
                page.session.set("mid", mid)
                page.session.set(
                    "mname",
                    merchants[mid].get("merchant_name", "Merchant")
                )
                show_terminal()
            else:
                msg.controls.append(error_text("Merchant ID not found"))
                page.update()

        page.add(
            card(
                "Merchant Login",
                [
                    merchant_input,
                    ft.ElevatedButton("Enter", on_click=login, width=350),
                    msg
                ]
            )
        )

    # =========================
    # Terminal
    # =========================
    def show_terminal():
        page.clean()
        mid = page.session.get("mid")
        mname = page.session.get("mname")

        page.add(
            ft.AppBar(
                title=ft.Text(f"{mname} ({mid})"),
                leading=ft.Icon("store"),
                actions=[
                    ft.IconButton(
                        icon="logout",
                        on_click=lambda _: show_login()
                    )
                ]
            )
        )

        token_input = ft.TextField(
            label="Redeem Token",
            width=400,
            text_align="center"
        )
        qty_input = ft.TextField(label="Quantity", value="1", width=400)

        vouchers_ui = ft.Column(spacing=20)
        result_ui = ft.Column()

        sel = {"hid": None, "tranche": None, "amount": None}

        def load_vouchers(e):
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
                row = []
                for amt, cnt in denoms.items():
                    if cnt <= 0:
                        continue

                    def choose(e, t=tranche, a=amt):
                        sel.update({"tranche": t, "amount": a})
                        load_vouchers(None)

                    selected = sel["tranche"] == tranche and sel["amount"] == amt

                    row.append(
                        ft.Container(
                            width=160,
                            padding=16,
                            border_radius=12,
                            bgcolor="#dbeafe" if selected else "white",
                            border=ft.border.all(2 if selected else 1),
                            on_click=choose,
                            content=ft.Column(
                                horizontal_alignment="center",
                                controls=[
                                    ft.Text(tranche, size=12),
                                    ft.Text(f"${amt}", size=24, weight="bold"),
                                    ft.Text(f"{cnt} left")
                                ]
                            )
                        )
                    )

                vouchers_ui.controls.append(ft.Row(wrap=True, controls=row))

            page.update()

        def confirm(e):
            if not sel["hid"] or not sel["amount"]:
                result_ui.controls.append(error_text("Select a voucher"))
                page.update()
                return

            res, status = redeem_voucher(
                sel["hid"],
                {
                    "merchant_id": mid,
                    "voucher_code": sel["tranche"],
                    "denomination": str(sel["amount"]),
                    "amount": int(qty_input.value)
                }
            )

            if status == 200:
                result_ui.controls.append(
                    success_box(f"Success! TX: {res['transaction_id']}")
                )
            else:
                result_ui.controls.append(
                    error_text(res.get("error", "Error"))
                )

            page.update()

        page.add(
            card(
                "Redeem Voucher",
                [
                    token_input,
                    ft.ElevatedButton(
                        "Verify Token",
                        on_click=load_vouchers
                    ),
                    vouchers_ui,
                    qty_input,
                    ft.ElevatedButton(
                        "Confirm",
                        on_click=confirm,
                        width=400
                    ),
                    result_ui
                ],
                width=800
            )
        )

    show_login()

ft.app(target=main)
