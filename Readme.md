# CDC Voucher Redemption System

A comprehensive voucher management system for households and merchants, built with Flask (backend API) and Flet (frontend applications).

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Applications](#running-the-applications)
- [User Guides](#user-guides)
  - [Household App](#household-app-guide)
  - [Merchant App](#merchant-app-guide)
  - [Web Interface](#web-interface-guide)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

## 🎯 System Overview

The CDC Voucher Redemption System consists of three main components:

1. **Flask API Server** (`app.py`) - Backend service handling all business logic and data storage
2. **Household App** (`household_app.py`) - Desktop application for households to manage vouchers
3. **Merchant App** (`merchant_app.py`) - Desktop application for merchants to redeem vouchers

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Household App  │         │  Merchant App   │
│   (Port 8550)   │         │   (Port 8551)   │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │    API Client             │
         └───────────┬───────────────┘
                     │
              ┌──────▼──────┐
              │  Flask API  │
              │ (Port 8000) │
              └─────────────┘
                     │
              ┌──────▼──────┐
              │   Storage   │
              │   (JSON)    │
              └─────────────┘
```

## 💻 Requirements

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection (for initial setup)

## 🚀 Installation

### Step 1: Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd cdc-voucher-system

# Or extract the zip file to a folder
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- Flask (web framework)
- Flet 0.28.3 (desktop UI framework)
- Requests (HTTP client)

### Step 3: Verify Installation

Check that all packages are installed:

```bash
pip list | grep -E "Flask|flet|requests"
```

## 🏃 Running the Applications

**IMPORTANT: Always start the Flask API server first!**

### 1. Start the Flask API Server

Open a terminal and run:

```bash
python app.py
```

You should see:
```
🚀 CDC VOUCHER API - Starting...
✅ Loaded X households
✅ Loaded X merchants
🚀 Starting Flask API Server...
🔗 URL: http://localhost:8000
```

**Keep this terminal window open.**

### 2. Start the Household App

Open a **new terminal** and run:

```bash
flet run household_app.py --port 8550
```

The Household App window will open automatically.

### 3. Start the Merchant App

Open **another new terminal** and run:

```bash
flet run merchant_app.py --port 8551
```

The Merchant App window will open automatically.

### Quick Start Commands

```bash
# Terminal 1: Flask API
python app.py

# Terminal 2: Household App
flet run household_app.py --port 8550

# Terminal 3: Merchant App
flet run merchant_app.py --port 8551
```

## 📱 User Guides

### Household App Guide

The Household App allows residents to register, claim vouchers, and generate redemption tokens.

#### 1. Registration

**First-time users:**

1. Launch the Household App
2. Click **"Register New Household"**
3. Enter household member names (comma-separated)
   - Example: `John Tan, Mary Tan, Peter Tan`
4. Enter your postal code (6 digits)
5. Click **"Register Household"**
6. **Save your Household ID** - you'll need it to log in!

#### 2. Login

1. Enter your Household ID (format: H12345678901)
2. Click **"Login"**

#### 3. Claiming Vouchers

After logging in:

1. Go to the **"Claim Vouchers"** tab
2. Select a voucher tranche (e.g., Jan2026, Feb2026)
3. Click **"Claim Vouchers"**
4. Your voucher balance will be updated

**Available Tranches:**
- **Jan2026**: $2 × 30, $5 × 20, $10 × 14 (Total: $300)
- **Feb2026**: $2 × 35, $5 × 25, $10 × 18 (Total: $375)

#### 4. Viewing Balance

1. Go to the **"View Balance"** tab
2. See all your available vouchers organized by tranche
3. Total value is displayed at the top

#### 5. Generating Redemption Token

When you're ready to make a purchase:

1. Go to the **"Generate Token"** tab
2. Select the vouchers you want to use:
   - Choose denomination ($2, $5, $10)
   - Enter quantity
3. Click **"Generate Token"**
4. A unique token will be displayed (e.g., TXN-ABC123)
5. **Share this token with the merchant**

**Important Notes:**
- Tokens expire after 5 minutes
- You can only have one active token at a time
- Tokens can only be used once

#### 6. Checking Notifications

1. Go to the **"Notifications"** tab
2. View redemption confirmations
3. Click **"Mark as Read"** to clear notifications
4. Use **"Refresh"** to check for new notifications

#### 7. Transaction History

1. Go to the **"Transactions"** tab
2. View all your past redemptions
3. See amount, merchant, date, and vouchers used

---

### Merchant App Guide

The Merchant App allows registered merchants to redeem voucher tokens from households.

#### 1. Merchant Login

1. Launch the Merchant App
2. Enter your **Merchant ID**
3. Click **"Login"**

**Don't have a Merchant ID?** You need to register first (see Registration section).

#### 2. Merchant Registration

**New merchants:**

1. Click **"Register New Merchant"**
2. Fill in all required fields:
   - Merchant ID (unique identifier)
   - Merchant Name
   - UEN (Unique Entity Number)
   - Bank Name
   - Bank Code
   - Branch Code
   - Account Number
   - Account Holder Name
3. Click **"Register Merchant"**
4. **Save your Merchant ID** for future logins

#### 3. Redeeming Vouchers

**When a customer presents a token:**

1. Ask the customer for their **redemption token** (e.g., TXN-ABC123)
2. Enter the token in the **"Redeem Vouchers"** tab
3. Click **"Redeem Token"**
4. The system will:
   - Validate the token
   - Display voucher details and total amount
   - Deduct vouchers from the household
   - Send a notification to the household
5. Confirm the redemption with the customer

**Successful Redemption Shows:**
- ✅ Success message
- Total amount redeemed
- Voucher breakdown
- Household ID (for verification)

**Error Messages:**
- ❌ "Invalid or expired token" - Token not found or already used
- ❌ "Token and merchant_id required" - Missing information
- ❌ "Merchant not found" - Invalid Merchant ID

---

### Web Interface Guide

You can also access the system through a web browser at `http://localhost:8000`

#### Available Pages:

1. **Home**: `http://localhost:8000/`
2. **Household Registration**: `http://localhost:8000/ui/household`
3. **Merchant Registration**: `http://localhost:8000/ui/merchant`
4. **Login**: `http://localhost:8000/ui/login`
5. **View Balance**: `http://localhost:8000/ui/balance/{household_id}`
6. **Claim Vouchers**: `http://localhost:8000/ui/claim/{household_id}`

## 🔌 API Documentation

### Base URL
```
http://localhost:8000
```

### Household Endpoints

#### Register Household
```http
POST /api/households
Content-Type: application/json

{
  "members": ["John Tan", "Mary Tan"],
  "postal_code": "123456"
}
```

#### Get Balance
```http
GET /api/households/{household_id}/balance
```

#### Claim Vouchers
```http
POST /api/households/{household_id}/claim
Content-Type: application/json

{
  "tranche": "Jan2026"
}
```

#### Generate Token
```http
POST /api/token/generate
Content-Type: application/json

{
  "household_id": "H12345678901",
  "vouchers": {
    "2": 5,
    "5": 2,
    "10": 1
  }
}
```

#### Get Transactions
```http
GET /api/households/{household_id}/transactions?limit=20
```

#### Get Notifications
```http
GET /api/households/{household_id}/notifications
```

### Merchant Endpoints

#### Register Merchant
```http
POST /api/merchants
Content-Type: application/json

{
  "merchant_id": "M001",
  "merchant_name": "Merchant Name",
  "uen": "123456789X",
  "bank_name": "DBS",
  "bank_code": "7171",
  "branch_code": "001",
  "account_number": "1234567890",
  "account_holder": "Company Name"
}
```

#### Get Merchant Details
```http
GET /api/merchants/{merchant_id}
```

#### Redeem Token
```http
POST /api/token/redeem
Content-Type: application/json

{
  "token": "TXN-ABC123",
  "merchant_id": "M001"
}
```

## 🗂️ File Structure

```
cdc-voucher-system/
├── app.py                      # Flask API server
├── household_app.py            # Household desktop app
├── merchant_app.py             # Merchant desktop app
├── api_client.py              # API communication layer
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── services/                   # Business logic
│   ├── household_service.py
│   ├── merchant_service.py
│   ├── voucher_service.py
│   ├── redemption_service.py
│   └── notification_service.py
│
├── storage/                    # Data storage
│   ├── households.json         # Household data
│   ├── households.txt          # Household backup
│   ├── merchants.json          # Merchant data
│   ├── merchants.txt           # Merchant backup
│   ├── notifications/          # Notification files
│   ├── transactions/           # Transaction history
│   └── redemptions/            # Redemption logs
│
└── templates/                  # Web UI templates
    ├── home.html
    ├── login.html
    ├── register_household.html
    ├── register_merchant.html
    ├── balance.html
    ├── claim_voucher.html
    └── redeem_voucher.html
```

## 🔧 Troubleshooting

### Flask API Won't Start

**Problem:** Port 8000 already in use

**Solution:**
```bash
# Check what's using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in app.py
```

### Household/Merchant App Connection Error

**Problem:** "Cannot connect to API server"

**Solutions:**
1. Make sure Flask API is running first
2. Check that Flask shows "Running on http://localhost:8000"
3. Try accessing `http://localhost:8000` in a web browser
4. Check firewall settings

### Flet App Won't Start

**Problem:** Error running flet command

**Solutions:**
```bash
# Reinstall flet
pip uninstall flet
pip install flet==0.28.3

# Run with python directly
python -m flet run household_app.py --port 8550
```

### "Merchant not found" Error

**Problem:** Merchant ID not recognized

**Solutions:**
1. Verify you registered the merchant first
2. Check the Merchant ID is entered correctly
3. Check `storage/merchants.json` for your merchant

### Token Already Expired

**Problem:** Token expired before merchant could redeem

**Solutions:**
- Generate a new token (old one is cancelled)
- Tokens are valid for 5 minutes
- Only one token can be active at a time

### Data Not Persisting

**Problem:** Data lost after restart

**Solutions:**
1. Check `storage/` folder exists
2. Verify write permissions
3. Look for error messages in Flask console

### Port Already in Use

**Problem:** Cannot start app on specified port

**Solutions:**
```bash
# Use different ports
flet run household_app.py --port 8552
flet run merchant_app.py --port 8553

# Or kill existing process
kill -9 $(lsof -t -i:8550)  # Mac/Linux
```

## 📞 Support

For issues or questions:
1. Check this README thoroughly
2. Review console logs for error messages
3. Check the `storage/` folder for data files
4. Verify all three components are running

## 🔐 Security Notes

**This is a development/demonstration system. For production use:**
- Add authentication and authorization
- Use HTTPS for API communication
- Implement proper database instead of JSON files
- Add input validation and sanitization
- Implement rate limiting
- Use environment variables for configuration

## 📝 License

AN6007 Group 13 - Academic Project

---

**Version:** 1.0  
**Last Updated:** February 2026  
**Developed by:** AN6007 Group 13