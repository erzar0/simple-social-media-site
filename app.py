import os

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, flash, session)
from neo4j import GraphDatabase
from werkzeug.security import generate_password_hash
from src.models.User import User
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
print(app.secret_key)

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
    return render_template("home.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password_hash = generate_password_hash(password, method="sha256")

        query = "CREATE (u:User {username: $username, password_hash: $password_hash})"
        db.execute_query(query, {"username": username, "password_hash": password_hash})

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        query = "MATCH (u:User {username: $username}) RETURN u.password_hash AS password_hash"
        result = db.execute_query(query, {"username": username})

        if result:
            user = User(username, result[0]["password_hash"])
            if user.check_password(password):
                session["username"] = username
                flash("Login successful.")
                return redirect(url_for("profile"))
            else:
                flash("Invalid password. Please try again.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.")
    return redirect(url_for("home"))


if __name__ == '__main__':
   app.run(debug=True)
