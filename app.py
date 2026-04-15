from flask import Flask, request, redirect, render_template, url_for
import sqlite3, random, string, socket

app = Flask(__name__)
DB = "urls.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original TEXT NOT NULL,
                short_code TEXT NOT NULL UNIQUE
            )
        """)

def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

@app.route("/", methods=["GET", "POST"])
def index():
    short_url = None
    error = None
    if request.method == "POST":
        original = request.form.get("url", "").strip()
        if not original.startswith("http"):
            error = "Please enter a valid URL starting with http:// or https://"
        else:
            code = generate_code()
            with get_db() as conn:
                conn.execute("INSERT INTO urls (original, short_code) VALUES (?, ?)", (original, code))
            short_url = request.host_url + code
    return render_template("index.html", short_url=short_url, error=error, host=socket.gethostname())

@app.route("/<code>")
def redirect_url(code):
    with get_db() as conn:
        row = conn.execute("SELECT original FROM urls WHERE short_code = ?", (code,)).fetchone()
    if row:
        return redirect(row["original"])
    return "Link not found", 404

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)