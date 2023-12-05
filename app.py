import os

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, flash, session)
from neo4j import GraphDatabase
from werkzeug.security import generate_password_hash
from src.models.User import User
from src.models.Post import Post
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET')
app.config['SESSION_TYPE'] = 'filesystem'
NEO4J_URI = os.environ.get('NEO4J_URI')
NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
AURA_INSTANCEID = os.environ.get('AURA_INSTANCEID')
AURA_INSTANCENAME = os.environ.get('AURA_INSTANCENAME')

class Neo4jDB:
    def __init__(self):
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    def close(self):
        self._driver.close()

    def execute_query(self, query, parameters=None):
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return result.data()

db = Neo4jDB()


@app.route("/")
@app.route("/home")
def home():
    if "username" not in session:
        latest_posts = []
    else:
        latest_posts = Post.get_latest_posts_from_friends(db, session["username"])
    ctx = {"posts": latest_posts}
    return render_template("home.django-html", ctx=ctx)

@app.route("/profile/<string:username>")
@app.route("/profile", defaults={'username': None}) 
def profile(username):
    if "username" not in session:
        current_user = None
    else:
        current_user = User.get_user(db, session["username"])

    is_my_profile = True if (current_user.username == username 
                                or username is None) else False
    username = username or session["username"]
    is_friend = current_user.is_friend(db, username)

    posts = Post.get_user_posts(db, username)
    sorted_posts = sorted(posts, key=lambda x: x.timestamp, reverse=True)

    ctx = {'username': username 
    , 'is_my_profile': is_my_profile
    , 'is_friend': is_friend
    , 'posts': sorted_posts}
    return render_template("profile.django-html", ctx=ctx)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password_hash = generate_password_hash(password, method="sha256")
        user = User(username, password_hash)

        if not user.is_username_taken(db):
            user.create_user(db)

            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))
        else:
            flash("Username already exists. ")

    return render_template("register.django-html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.get_user(db, username)
        if user:
            if user.check_password(password):
                session["username"] = username
                flash("Login successful.")
                return redirect(url_for("profile"))
            else:
                flash("Invalid password. Please try again.")
        else:
            flash("Username does not exist.")

    return render_template("login.django-html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.")
    return redirect(url_for("home"))

@app.route('/users')
def users_list():
    users = User.get_all_usernames(db)
    return render_template('users_list.django-html', users=users)

@app.route('/add_friend/<string:username>', methods=["POST"])
def add_friend(username):
    current_user = User.get_user(db, session["username"])
    if session["username"] != username:
        current_user.add_friendship(db, username)
        flash(f'Added {username} to your friends!')
    else:
        flash("You can't add yourself as a friend.")
    return redirect(url_for('profile', username=username))

@app.route('/remove_friend/<string:username>', methods=["POST"])
def remove_friend(username):
    user = User.get_user(db, session["username"])

    if user.is_friend(db, username):
        user.remove_friendship(db, username)
        flash(f'Removed {username} from your friends!')
    else:
        flash(f'{username} is not in your friends list.')

    return redirect(url_for('profile', username=username))

@app.route('/profile/<string:username>/friends')
def friends(username):
    user = User.get_user(db, username)
    friends = user.get_friend_usernames(db)
    are_my_friends = True if (session["username"] == username 
                                or username is None) else False
    ctx = {"friends": friends, "username": username, "are_my_friends": are_my_friends}
    return render_template('friends.django-html', ctx=ctx)

@app.route('/add_post', methods=['POST'])
def add_post():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    content = request.form.get('content')

    if content:
        post = Post(username, content)
        post.create(db)

    return redirect(url_for('profile'))

@app.route("/add_comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    if "username" not in session:
        flash("You need to be logged in to add a comment.")
        return redirect(url_for("login")) 

    username = session["username"]
    content = request.form["comment_content"]

    result = Post.add_comment(db, post_id, username, content)

    if result:
        flash("Comment added successfully.")
    else:
        flash("Failed to add comment. Please try again.")

    return redirect(request.referrer)  


if __name__ == '__main__':
   app.run(debug=True)
