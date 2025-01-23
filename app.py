from flask import Flask, request, redirect, session
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()  # Load environment variables from .env file
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Database setup
DATABASE = "tokens.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tumblr_username TEXT NOT NULL,
            oauth_token TEXT NOT NULL,
            oauth_token_secret TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return "Welcome to the Tumblr OAuth App!"

@app.route("/login")
def login():
    consumer_key = os.getenv("CONSUMER_KEY")
    consumer_secret = os.getenv("CONSUMER_SECRET")

    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)
    request_token_url = "https://www.tumblr.com/oauth/request_token"
    tokens = oauth.fetch_request_token(request_token_url)

    session["resource_owner_key"] = tokens.get("oauth_token")
    session["resource_owner_secret"] = tokens.get("oauth_token_secret")

    authorization_url = oauth.authorization_url("https://www.tumblr.com/oauth/authorize")
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    consumer_key = "uo5xuIXp4JE30ubqB0HDYCpqU072zhGRzNcPWg4Lla0MfLi1IA"
    consumer_secret = "8slLEVWtpDwfToDwjDwefKli8e5rm1u9T4z4tT04I3euLGSp45"
    verifier = request.args.get("oauth_verifier")

    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=session["resource_owner_key"],
        resource_owner_secret=session["resource_owner_secret"],
        verifier=verifier,
    )
    access_token_url = "https://www.tumblr.com/oauth/access_token"
    tokens = oauth.fetch_access_token(access_token_url)

    # Save the tokens to the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tokens (tumblr_username, oauth_token, oauth_token_secret)
        VALUES (?, ?, ?)
    """, (tokens.get("screen_name"), tokens.get("oauth_token"), tokens.get("oauth_token_secret")))
    conn.commit()
    conn.close()

    return "You are now authenticated! Your tokens have been securely stored."

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
