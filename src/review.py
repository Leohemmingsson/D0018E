class Review:
    __slots__ = ["id", "user_id", "username", "item_id", "rating", "comment"]

    def __init__(self, review, db=None) -> None:
        self.id = review[0]
        self.user_id = review[1]
        self.item_id = review[2]
        self.rating = review[3]
        self.comment = review[4]
        if db:
            self.username = db.get_username(self.user_id)
        else:
            self.username = None

    def to_json(self):
        return {
            "id" : self.id,
            "user_id" : self.user_id,
            "item_id" : self.item_id,
            "rating" : self.rating,
            "comment" : self.comment,
        }