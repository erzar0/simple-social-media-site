from datetime import datetime

class Post:
    def __init__(self, username, content, timestamp=None, id=None, comments=[]):
        self.username = username 
        self.content = content
        self.timestamp = timestamp 
        self.id = id
        self.comments = comments

    def create(self, db):
        self.timestamp = self.timestamp if self.timestamp is not None else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = (
            "MATCH (u:User {username: $username}) "
            "CREATE (p:Post {content: $content, username: $username, timestamp: $timestamp})-[:POSTED_BY]->(u)"
        )
        params = {
            "username": self.username
            , "content": self.content
            , "timestamp": self.timestamp
        }
        return db.execute_query(query, params)

    def get_user_posts(db, username):
        query = "MATCH (u:User {username: $username})<-[:POSTED_BY]-(p:Post) RETURN {p: p, post_id: id(p)} as result" 
        params = {"username": username}
        result = db.execute_query(query, params)
        posts = [{**record["result"]["p"], "id": record["result"]["post_id"]} for record in result]

        for post in posts:
            post['timestamp'] = datetime.fromisoformat(post['timestamp'])
        
        for post in posts:
            comments = Post.get_comments(db, post["id"])
            post["comments"] = comments

        return [Post(username, p["content"], p["timestamp"], p["id"], p["comments"]) for p in posts]

    def get_latest_posts_from_friends(db, username):
        query = (
            "MATCH (u:User {username: $username})<-[:FRIENDS_WITH]-(friend:User)<-[:POSTED_BY]-(post:Post) "
            "RETURN {p: post, post_id: id(post)} as result "
            "ORDER BY post.timestamp DESC "
            "LIMIT 10 "
            )
        params = {"username": username}
        result = db.execute_query(query, params)
        posts = [{**record["result"]["p"], "id": record["result"]["post_id"]} for record in result]

        for post in posts:
            post['timestamp'] = datetime.fromisoformat(post['timestamp'])
        
        for post in posts:
            comments = Post.get_comments(db, post["id"])
            post["comments"] = comments

        return [Post(p["username"], p["content"], p["timestamp"], p["id"], p["comments"]) for p in posts]
        

    def get_comments(db, post_id):
        query = (
            "MATCH (post:Post)-[:HAS_COMMENT]->(comment:Comment)-[:POSTED_BY]->(user:User) "
            "WHERE ID(post) = $post_id "
            "RETURN comment, user"
        )
        params = {"post_id": post_id}
        result = db.execute_query(query, params)
        return [{"comment": record["comment"], "user": record["user"]} for record in result]

    def add_comment(db, post_id, username, content):
        query = (
            "MATCH (post:Post) WHERE ID(post) = $post_id "
            "MATCH (user:User {username: $username}) "
            "CREATE (comment:Comment {content: $content, timestamp: $timestamp}) "
            "MERGE (user)<-[:POSTED_BY]-(comment) "
            "MERGE (post)-[:HAS_COMMENT]->(comment) "
            "RETURN comment"
        )
        params = {"username": username, "post_id": post_id, "content": content, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        result = db.execute_query(query, params)
        return result
    






