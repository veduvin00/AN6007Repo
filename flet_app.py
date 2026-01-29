import flet as ft
import random
import string
import time
import os
import qrcode

from services.household_service import (
    register_household,
    get_redemption_balance,
    load_households,
    households
)
from services.voucher_service import claim_voucher
from services.redemption_service import redeem_voucher
from services.merchant_service import register_merchant


# =========================
# Utils
# =========================
def generate_claim_token():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


def generate_redeem_token():
    return "RDM-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_qr(token, path):
    img = qrcode.make(token)
    img.save(path)


def resolve_household_from_redeem_token(token):
    now = time.time()
    for hid, h in households.items():
        if (
            getattr(h, "redeem_token", None) == token and
            getattr(h, "redeem_expiry", 0) > now
        ):
            return hid
    return None


# =========================
# App
# =========================
def main(page: ft.Page):
    page.title = "CDC Voucher System"
    page.bgcolor = "#f5f5f5"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    load_households()
    os.makedirs("tmp", exist_ok=True)

    # =========================
    # UI helpers
    # =========================
    def card(title, controls, width=900):
        return ft.Container(
            width=min(page.width - 32, width) if page.width else width,
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

    def success_box(text):
        return ft.Container(
            padding=16,
            border_radius=12,
            bgcolor="#ecfdf5",
            content=ft.Text(text, size=16, weight="bold", color="#15803d")
        )

    def error_text(text):
        return ft.Text(text, color="red")

    def tranche_badge(text):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=20,
            bgcolor="#15803d",
            content=ft.Text(text, size=12, color="white", weight="bold")
        )

    def voucher_card(tranche, amount, count, selected=None, on_select=None):
        disabled = count == 0
        is_selected = (
            selected
            and selected.get("tranche") == tranche
            and selected.get("amount") == amount
        )

        return ft.Container(
            width=180,
            padding=20,
            border_radius=16,
            bgcolor="#f3f4f6" if disabled else ("#e0f2fe" if is_selected else "white"),
            opacity=0.5 if disabled else 1,
            border=ft.border.all(2, "#2563eb") if is_selected else None,
            shadow=ft.BoxShadow(blur_radius=12, color="#0000001A"),
            on_click=None if (disabled or not on_select) else lambda e: on_select(tranche, amount, count),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    tranche_badge(tranche),
                    ft.Text(f"${amount}", size=30, weight="bold"),
                    ft.Text(
                        "Out of vouchers" if disabled else f"{count} available",
                        size=12
                    )
                ]
            )
        )

    # =========================
    # Header + Nav
    # =========================
    header = ft.Container(
        padding=16,
        bgcolor="#1f2933",
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Image(src="logo.png", width=70, height=70, scale=1.6),
                ft.Text("CDC Voucher System", size=28, weight="bold", color="white")
            ]
        )
    )

    def nav_button(label, view):
        return ft.TextButton(label, on_click=lambda e: navigate(view))

    nav = ft.Row(
        wrap=True,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=24,
        controls=[
            nav_button("Register Household", "household"),
            nav_button("Register Merchant", "merchant"),
            nav_button("Claim Voucher", "claim"),
            nav_button("Voucher Balance", "balance"),
            nav_button("Generate Redeem QR", "qr"),
            nav_button("Redeem Voucher", "redeem"),
        ]
    )

    content = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=24)
    page.add(header, nav, content)

    # =========================
    # Views
    # =========================
    def household_view():
        members = ft.TextField(label="Members (comma separated)", width=400)
        postal = ft.TextField(label="Postal Code", width=400)
        result = ft.Column()

        def submit(e):
            token = generate_claim_token()
            res, _ = register_household({
                "members": [m.strip() for m in members.value.split(",") if m.strip()],
                "postal_code": postal.value
            })

            households[res["household_id"]].claim_token = token
            households[res["household_id"]].has_claimed = False

            result.controls[:] = [
                success_box(
                    f"Household ID: {res['household_id']}\nClaim Token: {token}"
                )
            ]
            page.update()

        return card("Register Household", [
            members, postal,
            ft.ElevatedButton("Register Household", on_click=submit),
            result
        ])

    def merchant_view():
        fields = [
            ft.TextField(label=l, width=400) for l in [
                "Merchant ID", "Merchant Name", "UEN",
                "Bank Name", "Bank Code", "Branch Code",
                "Account Number", "Account Holder"
            ]
        ]
        result = ft.Column()

        def submit(e):
            register_merchant({
                "merchant_id": fields[0].value,
                "merchant_name": fields[1].value,
                "uen": fields[2].value,
                "bank_name": fields[3].value,
                "bank_code": fields[4].value,
                "branch_code": fields[5].value,
                "account_number": fields[6].value,
                "account_holder": fields[7].value,
            })
            result.controls[:] = [success_box("Merchant registered successfully")]
            page.update()

        return card("Register Merchant", fields + [
            ft.ElevatedButton("Register Merchant", on_click=submit),
            result
        ])

    def claim_view():
        claim_token = ft.TextField(label="Claim Token", width=400)
        tranche = ft.Dropdown(
            label="Voucher Tranche",
            width=400,
            options=[ft.dropdown.Option("Jan2026"), ft.dropdown.Option("May2025")]
        )
        result = ft.Column()

        def submit(e):
            hid = next(
                (i for i, h in households.items()
                 if getattr(h, "claim_token", None) == claim_token.value),
                None
            )

            if not hid:
                result.controls[:] = [error_text("Invalid claim token")]
                page.update()
                return

            if households[hid].has_claimed:
                result.controls[:] = [error_text("Vouchers already claimed")]
                page.update()
                return

            claim_voucher(hid, {"tranche": tranche.value})
            households[hid].has_claimed = True

            result.controls[:] = [success_box("Voucher claimed successfully")]
            page.update()

        return card("Claim CDC Voucher", [
            claim_token, tranche,
            ft.ElevatedButton("Confirm Claim", on_click=submit),
            result
        ])

    # =========================
    # BALANCE VIEW (RESTORED)
    # =========================
    def balance_view():
        household_id = ft.TextField(label="Household ID", width=400)
        result = ft.Column()

        def submit(e):
            result.controls.clear()

            if household_id.value not in households:
                result.controls.append(error_text("Household not registered"))
                page.update()
                return

            bal, _ = get_redemption_balance(household_id.value)

            for tranche, denoms in bal["vouchers"].items():
                cards = [
                    voucher_card(tranche, amt, cnt)
                    for amt, cnt in denoms.items()
                ]
                result.controls.append(
                    ft.Column(
                        controls=[
                            tranche_badge(tranche),
                            ft.Row(
                                wrap=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=16,
                                controls=cards
                            )
                        ]
                    )
                )
            page.update()

        return card("Voucher Balance", [
            household_id,
            ft.ElevatedButton("Check Balance", on_click=submit),
            result
        ])

    def qr_view():
        household_id = ft.TextField(label="Household ID", width=400)
        qr_image = ft.Image(width=200, height=200,
                            src="")
        result = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16)

        def generate(e):
            result.controls.clear()

            if household_id.value not in households:
                result.controls.append(error_text("Household not registered"))
                page.update()
                return

            token = generate_redeem_token()
            households[household_id.value].redeem_token = token
            households[household_id.value].redeem_expiry = time.time() + 300

            path = f"tmp/{token}.png"
            generate_qr(token, path)
            qr_image.src = path

            result.controls.extend([
                success_box(f"Redeem Token (valid 5 mins): {token}"),
                qr_image
            ])
            page.update()

        return card("Generate Redeem QR", [
            household_id,
            ft.ElevatedButton("Generate QR", on_click=generate),
            result
        ])

    def redeem_view():
        redeem_token = ft.TextField(label="Redeem QR Token", width=400)
        merchant_id = ft.TextField(label="Merchant ID", width=400)
        quantity = ft.TextField(label="Quantity", width=400)

        vouchers_ui = ft.Column(spacing=20)
        result = ft.Column()
        selected = {"tranche": None, "amount": None, "max": 0}
        resolved = {"hid": None}

        def load_vouchers(e=None):
            vouchers_ui.controls.clear()
            result.controls.clear()

            hid = resolve_household_from_redeem_token(redeem_token.value)
            if not hid:
                vouchers_ui.controls.append(error_text("Invalid or expired redeem token"))
                page.update()
                return

            resolved["hid"] = hid
            bal, _ = get_redemption_balance(hid)

            for tranche, denoms in bal["vouchers"].items():
                cards = []

                for amt, cnt in denoms.items():
                    def on_select(t=tranche, a=amt, c=cnt):
                        selected.update({"tranche": t, "amount": a, "max": c})
                        load_vouchers()

                    cards.append(voucher_card(tranche, amt, cnt, selected, on_select))

                vouchers_ui.controls.append(
                    ft.Column(
                        controls=[
                            tranche_badge(tranche),
                            ft.Row(
                                wrap=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=16,
                                controls=cards
                            )
                        ]
                    )
                )
            page.update()

        def submit(e):
            result.controls.clear()

            if not resolved["hid"]:
                result.controls.append(error_text("Load vouchers first"))
                page.update()
                return

            if not selected["amount"]:
                result.controls.append(error_text("Select a voucher"))
                page.update()
                return

            try:
                qty = int(quantity.value)
                if qty <= 0 or qty > selected["max"]:
                    raise ValueError
            except:
                result.controls.append(error_text("Invalid quantity"))
                page.update()
                return

            response, status = redeem_voucher(
                resolved["hid"],
                {
                    "merchant_id": merchant_id.value,
                    "voucher_code": selected["tranche"],
                    "denomination": str(selected["amount"]),
                    "amount": qty
                }
            )

            if status != 200:
                result.controls.append(error_text(response["error"]))
                page.update()
                return

            households[resolved["hid"]].redeem_token = None
            households[resolved["hid"]].redeem_expiry = 0

            selected.clear()
            vouchers_ui.controls.clear()

            result.controls.append(success_box("Voucher redeemed successfully"))
            page.update()

        return card("Redeem Voucher", [
            redeem_token,
            ft.ElevatedButton("Load Vouchers", on_click=load_vouchers),
            vouchers_ui,
            merchant_id,
            quantity,
            ft.ElevatedButton("Confirm Redemption", on_click=submit),
            result
        ], width=1100)

    # =========================
    # Navigation
    # =========================
    def navigate(view):
        content.controls.clear()
        content.controls.append({
            "household": household_view,
            "merchant": merchant_view,
            "claim": claim_view,
            "balance": balance_view,
            "qr": qr_view,
            "redeem": redeem_view
        }[view]())
        page.update()

    navigate("household")


# =========================
# Run
# =========================
ft.app(target=main, assets_dir="static/images")
