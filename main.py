from logging import error
from flask import Flask, redirect, render_template, g, Response, abort, request
import sqlite3
from random import shuffle

app = Flask(__name__)

def select(txt, dat):
    con = sqlite3.connect("./static/chessELO.db")
    cursor = con.cursor()
    cursor.execute(txt, dat)
    ret = cursor.fetchall()
    con.close()
    return ret


@app.route('/')
def start():
    return redirect("/leaderboard")


@app.route('/leaderboard')
def leaderboard():
    # get all info of each member in the club
    info = select("""SELECT User.id, User.name, Member.score, 
                    Attribute.name AS attribute, Statistics.win, 
                    Statistics.loss, Statistics.draw 
                    FROM User JOIN Member ON User.id = Member.uid 
                    JOIN Statistics ON Member.id = Statistics.mid 
                    JOIN Attribute ON Statistics.aid = Attribute.id
                    WHERE Member.cid = ?;""", ("1",))
    # print(board)

    # sort list for management
    info = sorted(info, key=lambda x: (-x[2], x[0], x[3]))

    # first iteration of the management - merge lists together
    temp = list(info.pop(0))
    board = [temp + [[temp[3], int(temp[4] / (temp[4] + temp[5]) * 100)]]]
    board[0].pop(3)

    # print(board)

    # rest of the iterations
    for i in range(len(info)):
        temp = list(info.pop(0))
        if temp[0] != board[-1][0]:
            # calc score
            board[-1][3] = int(board[-1][3] 
                            / (board[-1][3] + board[-1][4]) * 100)
            for i in range(2): board[-1].pop(4)
            board.append(temp)
            # remove the header for this since it 
            # will be used as the overall score/winrate 
            # and add the scores again
            board[-1] += [[temp[3], int(temp[4] / (temp[4] + temp[5]) * 100)]]
            board[-1].pop(3)
            # board[-1].append(int(board[i][3] / sum(board[i][x] 
            #                 for x in [3,4,5]) * 100))
        else:
            board[-1] += [[temp[3], int(temp[4] / (temp[4] + temp[5]) * 100)]]
            # add to overall score calcs
            for i in range (3, 6):
                board[-1][i] += temp[i+1]
    
    board[-1][3] = int(board[-1][3] 
                    / (board[-1][3] + board[-1][4]) * 100)
    for i in range(2): board[-1].pop(4)

    #print(board)

    #for i in range(5): board += board

    # board = ()

    return render_template("leaderboard.html", title="Leaderboard",
                            group_name="my group", page=0, rank=board)


@app.route("/matches")
def matches():
    info = select("""SELECT Event.id, Event.date, Event.result, 
                    User.id, User.name FROM Club 
                    JOIN Event ON Club.id = Event.club 
                    JOIN Player ON Event.id = Player.eid 
                    JOIN Member ON Player.mid = Member.id 
                    JOIN User ON Member.uid = User.id 
                    WHERE Club.id = ?
                    ORDER BY Event.date DESC""", ("1",))
    # print(info)

    matches = [list(info.pop(0))]

    for i in range(len(info)):
        temp = list(info.pop(0))
        if temp[0] == matches[-1][0]:
            matches[-1] += temp[-2:]
        else:
            matches.append(temp)
    
    # print(matches)

    # for i in range(5): matches += matches
    # shuffle(matches)

    return render_template("matches.html", title="Matches",
                            group_name="my group", page=1, matches=matches)


@app.route("/autofill_matches/<int:caller>", methods=["POST"])
def autofill_matches(caller):
    # print(caller)
    form = request.form.get("player"+str(caller+1))

    info = select("""SELECT User.id, User.name FROM Club
                    JOIN Member ON Club.id = Member.cid
                    JOIN User ON Member.uid = User.id
                    WHERE Club.id = ? AND User.name LIKE ?""", (1, "%"+str(form)+"%"))

    ret = ""
    for i in info:
        for j in i:
            ret += str(j) + "|"

    return ret


@app.route("/new_match")
def new_match():
    return redirect("/matches")

if __name__ == "__main__":
    app.run(debug=True)