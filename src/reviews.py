class Reviews:
    def __init__(self, review) -> None:
        self.id = review[0]
        self.user_id = review[1]
        self.item_id = review[2]
        self.rating = review[3]
        self.comment = review[4]
