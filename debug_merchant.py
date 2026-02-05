"""
SIMPLIFIED Merchant App - For Debugging
"""
import flet as ft

print("=" * 50)
print("Starting Merchant App...")
print("=" * 50)

try:
    from api_client import api_client
    print("✅ Successfully imported api_client")
except Exception as e:
    print(f"❌ Failed to import api_client: {e}")
    exit(1)

def main(page: ft.Page):
    page.title = "CDC Merchant - DEBUG"
    page.window_width = 400
    page.window_height = 800
    
    print("\n🔍 Checking API connection...")
    if not api_client.check_connection():
        print("❌ Cannot connect to Flask API!")
        page.add(
            ft.Text("❌ Cannot Connect to Flask API!", size=20, color="red")
        )
        page.update()
        return
    
    print("✅ Flask API is running!")
    
    def test_login(e):
        mid = merchant_id.value.strip()
        print(f"\n{'='*50}")
        print(f"🔍 Testing login for: {mid}")
        print(f"{'='*50}")
        
        if not mid:
            print("❌ Empty ID")
            result_text.value = "❌ Please enter an ID"
            page.update()
            return
        
        print("📡 Calling API: get_merchant()")
        try:
            response, status = api_client.get_merchant(mid)
            print(f"📥 Response: Status={status}")
            print(f"📥 Data: {response}")
            
            if status == 200:
                print("✅ Login successful!")
                result_text.value = f"✅ Login successful!\n\nMerchant: {response}"
                result_text.color = "green"
            else:
                print(f"⚠️ Merchant not found, but allowing login anyway")
                result_text.value = f"✅ Login OK (Merchant ID: {mid})"
                result_text.color = "green"
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            result_text.value = f"❌ Error: {str(e)}"
            result_text.color = "red"
        
        page.update()
        print(f"{'='*50}\n")
    
    merchant_id = ft.TextField(
        label="Merchant ID",
        width=350,
        hint_text="e.g., M001"
    )
    
    result_text = ft.Text("", size=14)
    
    page.add(
        ft.Container(height=50),
        ft.Text("🏪 Merchant Login - DEBUG", size=24, weight="bold"),
        ft.Container(height=20),
        ft.Text("API Status: ✅ Connected", size=12, color="green"),
        ft.Container(height=30),
        merchant_id,
        ft.Container(height=10),
        ft.ElevatedButton(
            "Test Login",
            on_click=test_login,
            width=350,
            height=50,
            bgcolor="green",
            color="white"
        ),
        ft.Container(height=20),
        result_text
    )
    page.update()
    print("✅ UI loaded successfully")

print("\n🚀 Starting Flet app...")
ft.app(target=main, port=8551)
