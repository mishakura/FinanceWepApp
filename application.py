import os
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    all_stocks = db.execute("SELECT DISTINCT stock FROM transactions WHERE id = ? and shares > 0 ORDER BY stock",session["user_id"])
    times_check_price = len(all_stocks)
    amount_shares = db.execute("SELECT SUM(shares) FROM transactions where id = ? GROUP by stock ORDER BY stock",session["user_id"])
    user_total = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    update_prices = []
    holdings = []
    names = []
    sharess = []
    cash = []
    checking_stock_exists = []

    date = datetime.now()


    cash.append(user_total[0]["cash"])
    totala = (cash[0])
    cash[0] = usd(cash[0])

    print(date)

    for i in range(times_check_price):
        ticker_symb = lookup(all_stocks[i]["stock"])
        update_prices.append(ticker_symb["price"])
        names.append(ticker_symb["name"])
        sharess.append(amount_shares[i]["SUM(shares)"])


    for i in range(times_check_price):
        holdings.append(update_prices[i] * amount_shares[i]["SUM(shares)"])
    for i in range(len(holdings)):
        totala += (holdings[i])
    totala = usd(totala)

    for i in range(len(holdings)):
        update_prices[i] = usd(update_prices[i])
        holdings[i] = usd(holdings[i])




    return render_template("index.html",total1=totala, cash=cash, ticket=all_stocks,names=names, j = times_check_price, shares=sharess, price= update_prices, total = holdings)




@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":

        return render_template("buy.html")

    else:
        date = datetime.now()
        ticker_symbol = lookup(request.form.get("symbol"))
        if not request.form.get("symbol"):
            return apology("Please enter a ticker symbol", 400)
        if not ticker_symbol:
            return apology("Stock not found", 400)
        if not request.form.get("shares").isdigit():
            return apology("Invalid number of stocks", 400)
        if not request.form.get("shares"):
            return apology("Invalid number of stocks", 400)




        total_to_pay = (ticker_symbol["price"]) * int(request.form.get("shares"))
        user_total = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        price = usd(ticker_symbol["price"])


        if total_to_pay > user_total[0]["cash"]:
            return apology("Not enough money for transaction", 400)
        else:
            new_total = user_total[0]["cash"] - total_to_pay
            db.execute("UPDATE users SET cash=? WHERE id = ?",new_total,session["user_id"] )
            amount = int(request.form.get("shares"))
            db.execute("INSERT INTO transactions (stock,shares,total,time, id, price) VALUES(?,?,?,?,?,?)",ticker_symbol["symbol"], amount,new_total,date,session["user_id"], price)
            return redirect("/")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT stock, shares,time, price FROM transactions where id =?", session["user_id"])
    return render_template("history.html", history = history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "GET":
        return render_template("quote.html")
    else:

        ticker_symbol = lookup(request.form.get("symbol"))

        if not ticker_symbol:
            return apology("Stock not found", 400)
        price = usd(ticker_symbol["price"])
        return render_template("quoted.html", t = ticker_symbol, price = price)



@app.route("/register", methods=["GET", "POST"])
def register():
    usern = request.form.get("username")
    userdb = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        if not request.form.get("username"):
            return apology("must provide username", 400)
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif request.form.get("password" )  !=   request.form.get("confirmation"):
            return apology("Passwords don't match", 400)
        elif len(request.form.get("password")) < 4 and len(request.form.get("confirmation")) < 4:
            return apology("Password must be longer than 4 characters", 400)
        elif len(userdb) == 1:
            return apology("Username already exists", 400)
    hashpass = generate_password_hash(request.form.get("password"))
    db.execute("INSERT INTO users (username, hash) VALUES(?,?)", usern ,hashpass)
    return redirect("/login")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    symbols = []
    sharess = []
    date = datetime.now()
    amount_shares = db.execute("SELECT SUM(shares) FROM transactions where id = ? GROUP by stock ORDER BY stock",session["user_id"])
    all_stocks = db.execute("SELECT DISTINCT stock FROM transactions WHERE id = ? ORDER BY stock",session["user_id"])
    for i in range(len(all_stocks)):
        symb = lookup(all_stocks[i]["stock"])
        symbols.append(symb["symbol"])
        sharess.append(amount_shares[i]["SUM(shares)"])


    if request.method == "GET":
        length = len(symbols)
        return render_template("sell.html", stocks = symbols,n = length, shares = sharess)
    else:

        user_stock_sell = request.form.get("symbol")
        if user_stock_sell not in symbols:
            return apology("You don't have that stock")
        number_sell = request.form.get("shares")
        total_stocks = db.execute("SELECT SUM(shares) FROM transactions where id = ? and stock = ? GROUP by stock",session["user_id"], user_stock_sell)
        print(number_sell)
        print(user_stock_sell)
        print(total_stocks)
        total = total_stocks[0]["SUM(shares)"]
        print(total)


        if float(number_sell) > float(total):
            return apology("You don't have enough stocks to make that transaction")
        price = lookup(user_stock_sell)
        price = price["price"]

        new_total = float(price) * float(number_sell)

        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        user_cash = user_cash[0]["cash"] + new_total
        print(user_cash)
        number_sell = - int(number_sell)
        print(number_sell)

        db.execute("INSERT INTO transactions (stock,shares,total,time,id,price) VALUES(?,?,?,?,?,?)", user_stock_sell,number_sell,  user_cash,date, session["user_id"], usd(price))
        db.execute("UPDATE users SET cash=? WHERE id = ?",user_cash,session["user_id"])
        return redirect("/")






    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
