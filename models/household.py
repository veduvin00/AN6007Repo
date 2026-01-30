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
        self.extra_data = {} 

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
        base = {
            "household_id": self.household_id,
            "members": self.members,
            "postal_code": self.postal_code,
            "vouchers": self.vouchers
        }
        base.update(self.extra_data)
        return base
    
    @classmethod
    def from_dict(cls, data):
        h = cls(
            household_id = data.get("household_id"),
            members = data.get("members"),
            postal_code = data.get("postal_code"),
            vouchers = data.get("vouchers", {})
        )
        known_keys = {"household_id", "members", "postal_code", "vouchers"}
        for k, v in data.items():
            if k not in known_keys:
                h.extra_data[k] = v
        return h

    
    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra_data.get(key)

    def __setitem__(self, key, value):
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.extra_data[key] = value

    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, AttributeError):
            return default

    def update(self, other_dict):
        for k, v in other_dict.items():
            self[k] = v
    
    def __contains__(self, key):
        return hasattr(self, key) or key in self.extra_data