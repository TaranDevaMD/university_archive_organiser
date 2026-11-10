import sqlite3

# Connect to SQLite database (this automatically creates database.db)
connection = sqlite3.connect('database.db')

# Read and execute your schema.sql blueprint
with open('schema.sql') as f:
    connection.executescript(f.read())

connection.commit()
connection.close()

print("Database and tables initialized successfully!")