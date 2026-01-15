class Household:
    def __init__(self, household_id, members, postal_code):
        self.household_id = household_id
        self.members = members
        self.postal_code = postal_code
        self.vouchers = {}  # tranche -> denomination map

    def to_dict(self):
        return {
            "household_id": self.household_id,
            "members": self.members,
            "postal_code": self.postal_code,
            "vouchers": self.vouchers
        }
