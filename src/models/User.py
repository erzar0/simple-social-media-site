from werkzeug.security import check_password_hash

class User:
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get_user(db, username):
        query = "MATCH (u:User {username: $username}) RETURN u LIMIT 1"
        result = db.execute_query(query, {"username": username})
        if result:
            user = result[0]["u"]
            return User(user["username"], user["password_hash"])
        else:
            return None

    @staticmethod
    def get_all_usernames(db):
        query = "MATCH (u:User) RETURN u.username AS username"
        result = db.execute_query(query)
        return [record["username"] for record in result]

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_username_taken(self, db):
        query = "MATCH (u:User {username: $username}) RETURN u.username AS username"
        result = db.execute_query(query, {"username": self.username})
        return bool(result)

    def create_user(self, db):
        query = "CREATE (u:User {username: $username, password_hash: $password_hash})"
        params = {"username": self.username, "password_hash": self.password_hash}
        return db.execute_query(query, params)

    def is_friend(self, db, friend_username):
        query = (
            "MATCH (user:User {username: $current_user})-[:FRIENDS_WITH]-(friend:User {username: $friend_username}) "
            "RETURN COUNT(friend) > 0 AS is_friend"
        )
        params = {"current_user": self.username, "friend_username": friend_username}
        return db.execute_query(query, params)[0]["is_friend"]

    def add_friendship(self, db, friend_username):
        query = (
            "MATCH (user:User {username: $current_user}), (friend:User {username: $friend_username}) "
            "MERGE (user)-[:FRIENDS_WITH]->(friend)"
            "MERGE (friend)-[:FRIENDS_WITH]->(user)"
        )
        params = {"current_user": self.username, "friend_username": friend_username}
        return db.execute_query(query, params)
        
    def remove_friendship(self, db, friend_username):
        query = (
            "MATCH (user:User {username: $current_user})-[r:FRIENDS_WITH]-(friend:User {username: $friend_username}) "
            "DELETE r"
        )
        params = {"current_user": self.username, "friend_username": friend_username}
        return db.execute_query(query, params)

    def get_friend_usernames(self, db):
        query = (
            "MATCH (user:User {username: $username})-[:FRIENDS_WITH]->(friend:User) "
            "RETURN friend"
        )
        params = {"username": self.username}
        result = db.execute_query(query, params)
        return [record['friend']['username'] for record in result]

