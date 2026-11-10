import sqlite3
from flask import Flask, g

app = Flask(__name__)

# Helper function to connect to your database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('database.db')
        # This allows us to access columns by name (e.g., paper['title'])
        db.row_factory = sqlite3.Row
    return db

# Automatically close the database connection when the request finishes
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    # Fetch all papers from your new database
    db = get_db()
    papers = db.execute('SELECT * FROM papers').fetchall()
    
    return f"<h1>Academic Document Management System</h1><p>Connected to database successfully! Found {len(papers)} papers.</p>"

if __name__ == '__main__':
    app.run(debug=True, port=5000)