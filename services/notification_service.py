"""
Notification Service for Real-time Updates
Allows merchant app to send notifications to household app
"""
import json
import os
import time
from datetime import datetime

# Create directories
NOTIFICATIONS_DIR = "storage/notifications"
TRANSACTIONS_DIR = "storage/transactions"
os.makedirs(NOTIFICATIONS_DIR, exist_ok=True)
os.makedirs(TRANSACTIONS_DIR, exist_ok=True)

def log_transaction(household_id, amount, vouchers, merchant_name="Merchant"):
    """
    Log a transaction to the household's transaction history
    
    Args:
        household_id: Household ID
        amount: Total amount redeemed
        vouchers: Dict of vouchers (e.g., {"2": 5, "5": 2})
        merchant_name: Name of merchant
    """
    transaction = {
        "household_id": household_id,
        "amount": amount,
        "vouchers": vouchers,
        "merchant_name": merchant_name,
        "timestamp": time.time(),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "redemption"
    }
    
    # Load existing transactions
    transactions_file = os.path.join(TRANSACTIONS_DIR, f"{household_id}_transactions.json")
    transactions = []
    
    if os.path.exists(transactions_file):
        try:
            with open(transactions_file, 'r') as f:
                transactions = json.load(f)
        except Exception as e:
            print(f"Error loading transactions: {e}")
            transactions = []
    
    # Add new transaction at the beginning (most recent first)
    transactions.insert(0, transaction)
    
    # Keep only last 50 transactions
    transactions = transactions[:50]
    
    # Save
    try:
        with open(transactions_file, 'w') as f:
            json.dump(transactions, f, indent=2)
        print(f"📝 Transaction logged for {household_id}")
    except Exception as e:
        print(f"Error saving transaction: {e}")

def get_transaction_history(household_id, limit=10):
    """
    Get transaction history for a household
    
    Args:
        household_id: Household ID
        limit: Number of transactions to return
        
    Returns:
        List of transaction objects
    """
    transactions_file = os.path.join(TRANSACTIONS_DIR, f"{household_id}_transactions.json")
    
    if not os.path.exists(transactions_file):
        return []
    
    try:
        with open(transactions_file, 'r') as f:
            transactions = json.load(f)
        return transactions[:limit]
    except Exception as e:
        print(f"Error loading transactions: {e}")
        return []

def create_redemption_notification(household_id, amount, vouchers, merchant_name="Merchant"):
    """
    Create a notification for successful redemption AND log the transaction
    
    Args:
        household_id: Target household ID
        amount: Total amount redeemed
        vouchers: Dict of vouchers (e.g., {"2": 5, "5": 2})
        merchant_name: Name of merchant
    """
    # Log transaction to history
    log_transaction(household_id, amount, vouchers, merchant_name)
    
    notification = {
        "type": "redemption_success",
        "household_id": household_id,
        "amount": amount,
        "vouchers": vouchers,
        "merchant_name": merchant_name,
        "timestamp": time.time(),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
    }
    
    # Save notification file
    filename = f"{household_id}_{int(time.time())}.json"
    filepath = os.path.join(NOTIFICATIONS_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(notification, f, indent=2)
    
    print(f"📬 Created notification: {filename}")
    return notification

def get_unread_notifications(household_id):
    """
    Get all unread notifications for a household
    
    Args:
        household_id: Household ID to check
        
    Returns:
        List of notification objects
    """
    notifications = []
    
    if not os.path.exists(NOTIFICATIONS_DIR):
        return notifications
    
    for filename in os.listdir(NOTIFICATIONS_DIR):
        if not filename.startswith(household_id):
            continue
            
        filepath = os.path.join(NOTIFICATIONS_DIR, filename)
        
        try:
            with open(filepath, 'r') as f:
                notification = json.load(f)
            
            # Only return unread notifications
            if not notification.get("read", False):
                notifications.append({
                    "notification": notification,
                    "filepath": filepath
                })
        except Exception as e:
            print(f"Error reading notification {filename}: {e}")
    
    # Sort by timestamp (newest first)
    notifications.sort(key=lambda x: x["notification"]["timestamp"], reverse=True)
    
    return notifications

def mark_notification_as_read(filepath):
    """
    Mark a notification as read and delete it
    
    Args:
        filepath: Path to notification file
    """
    try:
        os.remove(filepath)
        print(f"✅ Notification marked as read and deleted")
    except Exception as e:
        print(f"Error deleting notification: {e}")

def clear_all_notifications(household_id):
    """
    Clear all notifications for a household
    
    Args:
        household_id: Household ID
    """
    if not os.path.exists(NOTIFICATIONS_DIR):
        return
    
    count = 0
    for filename in os.listdir(NOTIFICATIONS_DIR):
        if filename.startswith(household_id):
            filepath = os.path.join(NOTIFICATIONS_DIR, filename)
            try:
                os.remove(filepath)
                count += 1
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
    
    print(f"🗑️ Cleared {count} notifications for {household_id}")