from flask import Flask, render_template, request, redirect, session
import mysql.connector
import requests
from bs4 import BeautifulSoup
import csv
from flask import Response
import webbrowser
import os
import threading
from urllib.parse import urljoin

app = Flask(__name__)
app.secret_key = "secretkey"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",   
    database="scraper_app"
)
cursor = db.cursor(dictionary=True)

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, email, password))
        db.commit()

        return redirect("/")

    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    sql = "SELECT * FROM users WHERE email=%s AND password=%s"
    cursor.execute(sql, (email, password))
    user = cursor.fetchone()

    if user:
        session["user"] = user["username"]
        return redirect("/dashboard")
    else:
        return "Invalid Credentials"


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    return render_template("dashboard.html", books=books, user=session["user"])


@app.route("/scrape", methods=["POST"])
def scrape():
    if "user" not in session:
        return redirect("/")

    url = request.form.get("url")
    if not url:
        return redirect("/dashboard")
    limit = int(request.form.get("limit", 50))
    clear = request.form.get("clear")
    pages_to_scrape = int(request.form.get("pages", 1))

    if clear:
        cursor.execute("TRUNCATE TABLE books")
        db.commit()

    count = 0
    current_url = url

    for _ in range(pages_to_scrape):
        if count >= limit or not current_url:
            break

        response = requests.get(current_url)
        soup = BeautifulSoup(response.text, "html.parser")

        books = soup.find_all("article", class_="product_pod")

        for book in books:
            if count >= limit:
                break

            title = book.h3.a["title"]
            price = book.find("p", class_="price_color").text
            availability = book.find("p", class_="instock availability").text.strip()
            rating = book.find("p")["class"][1]

            sql = """
            INSERT INTO books (title, price, rating, availability)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (title, price, rating, availability))
            count += 1
        
        next_button = soup.find("li", class_="next")
        if next_button:
            next_page_url = next_button.a["href"]
            current_url = urljoin(current_url, next_page_url)
        else:
            current_url = None

    db.commit()

    return redirect("/dashboard")

@app.route("/download")
def download():
    if "user" not in session:
        return redirect("/")

    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    def generate():
        data = csv.writer(open("books.csv", "w", newline=""))
        yield "Title,Price,Rating,Availability\n"
        for book in books:
            row = f"{book['title']},{book['price']},{book['rating']},{book['availability']}\n"
            yield row

    return Response(generate(),
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=books.csv"})
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=True)