class Household:

    TRANCHE_CONFIG = {
        "May2025":{2: 50, 5: 20, 10: 30},
        "Jan2026":{2: 30, 5: 20, 10: 14}
    }

    def __init__(self, household_id, members, postal_code, vouchers = None):
        self.household_id = household_id
        self.members = members
        self.postal_code = postal_code
        self.vouchers = vouchers if vouchers is not None else {}

    def claim_tranche(self, tranche_name):
        if tranche_name not in self.TRANCHE_CONFIG:
            return False, "Invalid tranche name."
        if tranche_name in self.vouchers:
            return False, "Tranche already claimed."
        
        self.vouchers[tranche_name] = self.TRANCHE_CONFIG[tranche_name].copy()
        return True, "Vouchers claimed successfully."

    def get_total_balance(self):
        total = 0
        for tranche in self.vouchers.values():
            for denomination, count in tranche.items():
                total += int(denomination) * count
        return total

    def to_dict(self):
        return {
            "household_id": self.household_id,
            "members": self.members,
            "postal_code": self.postal_code,
            "vouchers": self.vouchers
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            household_id = data["household_id"],
            members = data["members"],
            postal_code = data["postal_code"],
            vouchers = data.get("vouchers", {})
        )