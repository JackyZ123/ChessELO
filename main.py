from flask import Flask, redirect, render_template, g, Response, abort, request
import sqlite3

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("leaderboard.html", title="Leaderboard")

if __name__ == "__main__":
    app.run(debug=True)