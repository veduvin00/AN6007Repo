import csv
import os
import random
import string

# 1. 全局字典 (必须定义，否则 app3.py 无法导入)
households = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "..", "storage")
HOUSEHOLD_FILE = os.path.join(STORAGE_DIR, "households.txt")

def load_households():
    """从 CSV 文件加载住户数据到内存"""
    if not os.path.exists(HOUSEHOLD_FILE):
        return

    with open(HOUSEHOLD_FILE, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                hid = row[0]
                # 加载到内存中
                households[hid] = {
                    "household_id": hid,
                    "members": row[1].split(";"),
                    "postal_code": row[2]
                }

def register_household(data):
    """注册新住户"""
    # 生成随机 8 位 ID
    hid = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    os.makedirs(STORAGE_DIR, exist_ok=True)
    
    # 写入文件 (持久化)
    with open(HOUSEHOLD_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        members_str = ";".join(data.get("members", []))
        writer.writerow([
            hid,
            members_str,
            data.get("postal_code", "")
        ])
    
    # 更新内存 (确保无需重启即可登录)
    households[hid] = {
        "household_id": hid,
        "members": data.get("members", []),
        "postal_code": data.get("postal_code", "")
    }
    
    # 返回元组 (数据, 状态码)，修复前端解包错误
    return {"household_id": hid, "message": "Success"}, 200

def get_redemption_balance(household_id):
    """查询住户的余额 (被意外删除的函数，现已补回)"""
    if household_id not in households:
        return {"error": "Household not found"}, 404
    
    # 模拟返回该住户的可用券 (为了演示效果，默认给予满额券包)
    # 在真实逻辑中，这里应该读取数据库中该用户的剩余额度
    return {
        "vouchers": {
            "Jan2026": {"10": 5, "5": 8, "2": 15},
            "May2025": {"10": 2, "5": 4, "2": 10}
        }
    }, 200
