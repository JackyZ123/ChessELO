from flask import Flask, redirect, render_template, g, Response, abort, request
import sqlite3

app = Flask(__name__)

def select(txt):
    con = sqlite3.connect("./static/RankSystem.db")
    cursor = con.cursor()
    cursor.execute(txt)
    ret = cursor.fetchall()
    con.close()
    return ret

@app.route('/')
def leaderboard():
    print(select())
    return render_template("leaderboard.html", title="Leaderboard", group_name="my group", page=0)

if __name__ == "__main__":
    app.run(debug=True)