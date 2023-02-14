class Item:
    def __init__(self, product):
        self.id = product[0]
        self.description = product[2]
        self.name = product[1]
        self.quantity = product[3]
        self.price = product[4]
        self.image = product[5]
        self.href = f"/product/{product[0]}"
