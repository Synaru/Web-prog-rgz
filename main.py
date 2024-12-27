from datetime import datetime, timedelta
import pandas as pd
import json

from flask import Flask, render_template, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
import os
from os import path

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')

@app.route("/")
def root():
    if session.get('login') == None:
        return redirect("/register", code=302)
    else:
        return redirect("/calendar", code=302)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if session.get('login') != None:
        return redirect("/calendar", code=302)
    if request.method == 'GET':
        return render_template("register.html")

    name = request.form.get('name')
    login = request.form.get('login')
    password = request.form.get('password')

    if not (login or password or name):
        return render_template('register.html', error="Заполните все обязательные поля")

    conn, cur = db_connect()
    cur.execute("SELECT login FROM users WHERE login=?;", (login,))
    if cur.fetchone():
        db_close(conn, cur)
        return render_template('register.html', error="Такой пользователь уже есть")

    password_hash = generate_password_hash(password)
    cur.execute("INSERT INTO users (name, login, password) VALUES (?,?,?);", (name, login, password_hash))

    db_close(conn, cur)

    return redirect("/login", code=302)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('login') != None:
            return redirect("/calendar", code=302)
        return render_template("login.html")

    login = request.form.get('login')
    password = request.form.get('password')

    if not (login or password):
        return render_template('login.html', error="Заполните все обязательные поля")

    conn, cur = db_connect()
    cur.execute("SELECT * FROM users WHERE login = ?;", (login,))
    user = cur.fetchone()

    if not user:
        db_close(conn, cur)
        return render_template('login.html', error="Логин и\или пароль не верны")

    if not check_password_hash(user['password'], password):
        db_close(conn, cur)
        return render_template('login.html', error="Логин и\или пароль не верны")

    session['login'] = login
    db_close(conn, cur)
    return redirect("/calendar", code=302)

@app.route("/selectweek", methods=['POST'])
def selectweek():
    login = session.get('login')
    if login == None:
        return "", 401

    result = request.get_json()
    if not result['week'] or not result['year']:
        return "400"

    conn, cur = db_connect()
    cur.execute("SELECT * FROM users WHERE login = ?;", (login,))
    user = cur.fetchone()

    cur.execute("SELECT * FROM weeks WHERE user_id = ? AND year_id = ?;", (user['id'], result['year'],))
    alreadyTaken = cur.fetchall()

    takenThisYear = len(alreadyTaken)
    if takenThisYear >= 4:
        return "", 400

    cur.execute("UPDATE weeks SET user_id = ? WHERE id = ?;", (user['id'], result['week']))
    db_close(conn, cur)
    return "200"

@app.route("/deselectweek", methods=['POST'])
def deselectweek():
    login = session.get('login')
    if session.get('login') == None:
        return "", 401
    result = request.get_json()
    if not result['week']:
        return "400"

    conn, cur = db_connect()
    cur.execute("SELECT * FROM users WHERE login = ?;", (login,))
    user = cur.fetchone()

    cur.execute("SELECT * FROM weeks WHERE user_id = ? AND id = ?;", (user['id'],result['week'],))
    week = cur.fetchone()

    if not week:
        return "", 401

    cur.execute("UPDATE weeks SET user_id = NULL WHERE id = ?;", (result['week'],))
    db_close(conn, cur)
    return "200"

@app.route("/weekslist", methods=['GET'])
def weekslist():
    # if session.get('login') != None:
    #     return "", 401
    year = request.args.get('year')
    if not year:
        return "400"

    conn, cur = db_connect()
    cur.execute("""
    SELECT Weeks.id,start,end, user_id, year_id, name FROM 
    (Weeks LEFT JOIN Years ON year_id = Years.id)
    LEFT JOIN Users ON user_id = Users.id
    WHERE year_id = ?;
    """, (year,))
    weeks = cur.fetchall()
    json_data = [dict(zip([desc[0] for desc in cur.description], row)) for row in weeks]
    db_close(conn, cur)
    return json_data

@app.route("/calendar")
def calendar():
    year = 2025
    if session.get('login') == None:
        return redirect("/login", code=302)

    conn, cur = db_connect()
    cur.execute("SELECT * FROM users WHERE login = ?;", (session.get('login'),))
    user = cur.fetchone()
    db_close(conn, cur)

    return render_template("calendar.html", year=year, name=user['name'])

@app.route("/logout")
def logout():
    session['login'] = None
    return redirect("/login", code=302)

def db_connect():
    dir_path = path.dirname(path.relpath(__file__))
    db_path = path.join(dir_path, 'db.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    return conn, cur

def db_close(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()

def initializeYear(year):
    conn, cur = db_connect()
    # Start from January 1st of the current year
    start_date = datetime(year, 1, 1)

    while start_date.year == year:
        week_number = start_date.isocalendar()[1]

        # Insert a new row for each week
        insert_query = """
                INSERT INTO Weeks (start, end, year_id)
                VALUES (?, ?, ?)
            """

        cur.execute(insert_query, (
            start_date.isoformat(),
            (start_date + timedelta(weeks=1) - timedelta(days=start_date.weekday())).isoformat(),
            year
        ))

        start_date += timedelta(weeks=1)

    conn.commit()
    print(f"Inserted {week_number} weeks for the year {year}")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # initializeYear(2026)
    app.run(debug=True)





