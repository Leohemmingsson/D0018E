class Order:
    def __init__(self, fields, sql=None) -> None:
        self.id = fields[0]
        self.user_id = fields[1]
        self.status = fields[2]
        self.date = fields[3]
        self.price = None

        if sql:
            self.price = sql.get_price_for_order(self.id)
