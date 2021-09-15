from datetime import datetime
from flask import Flask, redirect, render_template, request
import sqlite3
from flask.globals import session

from flask.helpers import make_response

app = Flask(__name__)
app.secret_key = "fxlO9Etflj7jCbBRhMmSXGEKbHlgq1MWCBLpBYoJLMTQeWiy72r3IgNy49FuGsLS6X7NLMd4QtzVOBFs6uQvWmgmhSd8MyFSf9rneYYf1IQka9UelsAM0xhJJEbRLpOeIr3Wp87CnfvW8Qi0bOD16sKyrqNQDY5AIp1r2dXuJIKJ1NYYUgIt6OdaKyzCEbpQvuauOGNVQL6keo2eULXCDsyOYgL14WMLbUHs52UckcLwkOJMYOAWQ1V54G"


def get_conn():
    con = sqlite3.connect("./static/chessELO.db")
    cur = con.cursor()
    return con, cur


def select(txt, dat):
    con, cursor = get_conn()
    cursor.execute(txt, dat)
    ret = cursor.fetchall()
    con.close()
    return ret


def change(txt, dat):
    con, cursor = get_conn()
    cursor.execute(txt, dat)
    con.commit()
    con.close()


def hash(txt):
    # print(txt)
    out = ""
    for i in txt:
        out += str(ord(i))
    try:
        out = int(out)
        out = out ** 57
        out += 7235628437562983284375682437
        out = out // 72
        return str(out)
    except:
        return ""


@app.route('/')
def start():
    return redirect("/leaderboard")


@app.route('/leaderboard')
def leaderboard():
    # get all info of each member in the club
    info = select("""SELECT User.id, User.name, Member.score,
                    Attribute.name AS attribute, Statistic.win,
                    Statistic.loss, Statistic.draw
                    FROM User JOIN Member ON User.id = Member.uid
                    JOIN Statistic ON Member.id = Statistic.mid
                    JOIN Attribute ON Statistic.aid = Attribute.id
                    WHERE Member.cid = ?;""", ("1",))
    # print(info)

    # sort list for management
    info = sorted(info, key=lambda x: (-x[2], x[0], x[3]))

    # first iteration of the management - merge lists together
    temp = list(info.pop(0))
    try:
        board = [temp + [[temp[3], int(temp[4] / (temp[4] + temp[5]) * 100)]]]
    except:
        board = [temp + [[temp[3], 0]]]
    board[0].pop(3)

    # print(board)

    # rest of the iterations
    for i in range(len(info)):
        temp = list(info.pop(0))
        if temp[0] != board[-1][0]:
            # calc score
            try:
                board[-1][3] = int(board[-1][3]
                                   / (board[-1][3] + board[-1][4]) * 100)
            except:
                board[-1][3] = 0
            for i in range(2):
                board[-1].pop(4)
            board.append(temp)
            # remove the header for this since it
            # will be used as the overall score/winrate
            # and add the scores again
            try:
                board[-1] += [[temp[3],
                               int(temp[4] / (temp[4] + temp[5]) * 100)]]
            except:
                board[-1] += [[temp[3], 0]]
            board[-1].pop(3)
            # board[-1].append(int(board[i][3] / sum(board[i][x]
            #                 for x in [3,4,5]) * 100))
        else:
            try:
                board[-1] += [[temp[3],
                               int(temp[4] / (temp[4] + temp[5]) * 100)]]
            except:
                board[-1] += [[temp[3], 0]]
            # add to overall score calcs
            for i in range(3, 6):
                board[-1][i] += temp[i+1]

    try:
        board[-1][3] = int(board[-1][3]
                           / (board[-1][3] + board[-1][4]) * 100)
    except:
        board[-1][3] = 0
    for i in range(2):
        board[-1].pop(4)

    # print(board)

    # for i in range(5): board += board

    # board = ()

    return render_template("leaderboard.html", title="Leaderboard",
                           group_name="my group", page=0, rank=board)


@app.route("/matches")
def matches():
    info = select("""SELECT Event.id, Event.date, Event.result,
                    Member.id, User.name FROM Club
                    JOIN Event ON Club.id = Event.club
                    JOIN Player ON Event.id = Player.eid
                    JOIN Member ON Player.mid = Member.id
                    JOIN User ON Member.uid = User.id
                    WHERE Club.id = ?
                    ORDER BY Event.date DESC""", ("1",))

    matches = []
    date = []

    months = {'01': "January", '02': "Febuary", '03': "March", '04': "April",
              '05': "May", '06': "June", '07': "July", '08': "August",
              '09': "September", '10': "October", '11': "November",
              '12': "December"}

    if info != []:
        matches = [list(info.pop(0))]
        d = datetime.utcfromtimestamp(matches[0][1]).strftime("%d %m %Y")
        date.append([d, 1])
        matches[0][1] = datetime.utcfromtimestamp(
            matches[0][1]).time().strftime("%H:%M")

    for i in range(len(info)):
        temp = list(info.pop(0))
        if temp[0] == matches[-1][0]:
            matches[-1] += temp[-2:]
        else:
            d = datetime.utcfromtimestamp(temp[1]).strftime("%d %m %Y")
            if d == date[-1][0]:
                date[-1][1] += 1
            else:
                date.append([d, 1])
            temp[1] = datetime.utcfromtimestamp(
                temp[1]).time().strftime("%H:%M")
            matches.append(temp)

    for i in date:
        d = i[0].split()
        d[0] = str(int(d[0]))
        d[1] = months[d[1]]
        i[0] = " ".join(d)

    return render_template("matches.html", title="Matches", group_name="my group",
                           page=1, matches=matches, date=date)


@app.route("/autofill_matches/<int:caller>", methods=["POST"])
def autofill_matches(caller):
    form = request.form.get("player"+str(caller+1))

    info = select("""SELECT Member.id, User.name FROM Club
                    JOIN Member ON Club.id = Member.cid
                    JOIN User ON Member.uid = User.id
                    WHERE Club.id = ? AND User.name LIKE ?
                    ORDER BY User.name""", (1, str(form)+"%"))

    info += select("""SELECT Member.id, User.name FROM Club
                    JOIN Member ON Club.id = Member.cid
                    JOIN User ON Member.uid = User.id
                    WHERE Club.id = ? AND User.name LIKE ?
                    ORDER BY User.name""", (1, "%_"+str(form)+"%"))

    members = []
    for i in info:
        if i not in members:
            members.append(i)

    ret = ""
    for i in members:
        for j in i:
            ret += str(j) + "|"

    return ret


@app.route("/new_match", methods=["GET", "POST"])
def new_match():
    try:
        players = list(
            map(int, [request.form.get("p1"), request.form.get("p2")]))
        if players[0] == players[1]:
            raise Exception
    except:
        print("unidentified input")
        return "false"
    try:
        winner = players[int(request.form.get("winner"))]
    except Exception as err:
        winner = -1

    date = int(datetime.timestamp(datetime.utcnow()))

    # get id
    try:
        id = select("""SELECT id FROM Event ORDER BY id DESC""", ())[0][0] + 1
    except:
        id = 0

    # insert event
    change("""INSERT INTO Event (id, club, result, date)
            VALUES (?, ?, ?, ?)""", (id, 1, int(winner), date))
    for i in range(len(players)):
        change("""INSERT INTO Player (eid, mid, aid)
                VALUES (?, ?, ?)""", (id, int(players[i]), 1 if i == 0 else 2))

    scores = []

    # change player values
    for i in range(len(players)):
        p, = select("""SELECT * FROM Statistic
                        WHERE mid = ? AND aid = ?""", (players[i], i+1))
        a, = list(select(
            """SELECT score, development FROM Member WHERE id = ?""", (players[i],)))

        scores.append(list(map(int, a)))

        change("""UPDATE Statistic
                    SET win = ?, loss = ?, draw = ?
                    WHERE mid = ? AND aid = ?""",
               (p[2]+int(winner == players[i]), p[3]+int(winner != (players[i] or -1)),
                p[4]+int(winner == -1), players[i], i+1))

    for i in range(2):
        difference = scores[1][0] - scores[0][0]
        k = max(10, min(400, int(400/(scores[i][1] + 1))))
        if i == 1:
            difference = -difference
        ratio = difference / 400
        val = 10**ratio + 1
        expectedScore = 1/val
        # print(expectedScore, (1 if winner == players[i] else (
        #     0.5 if winner == -1 else 0)))
        change("""UPDATE Member
                    SET score = ?, development = ?
                    WHERE id = ?""",
               (round(scores[i][0] + k * ((1 if winner == players[i] else (
                   0.5 if winner == -1 else 0)) - expectedScore)), scores[i][1] + 1, players[i]))

    return "true"


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signin", methods=["POST"])
def signin():
    info = [request.form.get("username"), hash(request.form.get("password"))]
    (password, id), = select(
        """SELECT password, id FROM User WHERE name = ?""", (info[0],))
    # check password
    if password != info[1]:
        return redirect("/login")
    session["user"] = int(id)
    return redirect("/leaderboard")


@app.route("/signup", methods=["POST"])
def signup():
    info = [request.form.get("username"), hash(
        request.form.get("password")), hash(request.form.get("confirm"))]
    # check if passwords are the same
    if info[1] != info[2]:
        return redirect("/login")
        # check if name already exists
    password = select(
        """SELECT password FROM User WHERE name = ?""", (info[0],))
    if len(password) != 0:
        return redirect("/login")
    # add user into database and into the club
    change("""INSERT INTO User (name, password) VALUES (?,?)""",
           (info[0], info[1]))
    id, = select("""SELECT id FROM User WHERE name = ?""", (info[0],))[0]
    change("""INSERT INTO Member (uid, cid, admin, score, development) VALUES (?,?,?,?,?)""",
           (id, 1, 0, 1000, 0))
    # add stats
    id, = select(
        """SELECT id FROM Member WHERE uid = ? and cid = 1""", (id,))[0]
    change("""INSERT INTO Statistic VALUES (?,?,?,?,?)""", (id, 1, 0, 0, 0))
    change("""INSERT INTO Statistic VALUES (?,?,?,?,?)""", (id, 2, 0, 0, 0))
    return redirect("/leaderboard")


if __name__ == "__main__":
    app.run()
