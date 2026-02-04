"""
API Client for CDC Voucher System
Complete version with ALL methods
"""
import requests

API_BASE_URL = "http://localhost:8000"

class CDCApiClient:
    """Client for communicating with Flask API"""
    
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
    
    # ==================
    # HOUSEHOLD METHODS
    # ==================
    
    def register_household(self, members, postal_code):
        """Register a new household"""
        try:
            response = requests.post(
                f"{self.base_url}/api/households",
                json={"members": members, "postal_code": postal_code}
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def get_balance(self, household_id):
        """Get household voucher balance"""
        try:
            response = requests.get(
                f"{self.base_url}/api/households/{household_id}/balance"
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def claim_vouchers(self, household_id, tranche):
        """Claim vouchers for a household"""
        try:
            response = requests.post(
                f"{self.base_url}/api/households/{household_id}/claim",
                json={"tranche": tranche}
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def generate_token(self, household_id, vouchers):
        """Generate redemption token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/token/generate",
                json={"household_id": household_id, "vouchers": vouchers}
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def get_transactions(self, household_id, limit=20):
        """Get transaction history"""
        try:
            response = requests.get(
                f"{self.base_url}/api/households/{household_id}/transactions",
                params={"limit": limit}
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def get_notifications(self, household_id):
        """Get unread notifications"""
        try:
            response = requests.get(
                f"{self.base_url}/api/households/{household_id}/notifications"
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/notifications/{notification_id}"
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    # ==================
    # MERCHANT METHODS
    # ==================
    
    def register_merchant(self, merchant_data):
        """Register a new merchant"""
        try:
            response = requests.post(
                f"{self.base_url}/api/merchants",
                json=merchant_data
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def get_merchant(self, merchant_id):
        """Get merchant details - THIS METHOD WAS MISSING!"""
        try:
            response = requests.get(
                f"{self.base_url}/api/merchants/{merchant_id}"
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def redeem_token(self, token, merchant_id):
        """Redeem a token at merchant"""
        try:
            response = requests.post(
                f"{self.base_url}/api/token/redeem",
                json={"token": token, "merchant_id": merchant_id}
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    # ==================
    # HELPER METHODS
    # ==================
    
    def check_connection(self):
        """Check if Flask API is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=2)
            return True
        except:
            return False

# Create singleton instance
api_client = CDCApiClient()