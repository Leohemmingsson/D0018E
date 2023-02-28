class Item:
    def __init__(self, product=None, **kwargs):
        if len(kwargs) == 0:
            self.id = product[0]
            self.description = product[2]
            self.name = product[1]
            self.quantity = product[3]
            self.price = product[4]
            self.image = product[5]
            self.href = f"/product/{product[0]}"
        else:
            self.id = kwargs["id"]
            self.description = kwargs["description"]
            self.name = kwargs["name"]
            self.quantity = kwargs["quantity"]
            self.price = kwargs["price"]
            self.image = kwargs["image"]
            self.href = f"/product/{kwargs['id']}"

        if len(self.description) > 50:
            self.summary = self.description[:50] + "..."
        else:
            self.summary = self.description
