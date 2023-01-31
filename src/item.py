class Item:
    def __init__(self, id, name, price, quantity, image, description, href):
        self.id = id
        self.name = name
        self.price = price
        self.quantity = quantity
        self.image = image
        self.description = description
        self.href = href
    
    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
            "image": self.image,
            "description": self.description,
            "href": self.href
        }