import sqlite3

conn = sqlite3.connect('mmu_xxchange.db')
cursor = conn.cursor()

# CREATE TABLES FIRST (add this section)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    email TEXT,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS listings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    price REAL,
    user_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER,
    requester_id INTEGER,
    status TEXT
)
""")

cursor.execute(
    "INSERT OR IGNORE INTO users (username, email, password) VALUES (?, ?, ?)",
    ("testuser", "test@email.com", "123456")
)

# insert listing
cursor.execute(
    "INSERT OR IGNORE INTO listings(title,price,user_id)VALUES(?,?,?)",
    ("Calculator",50,1)
)

#insert requests
cursor.execute(
    "INSERT OR IGNORE INTO requests (listing_id,requester_id,status)VALUES(?,?,?)",
    (1,1,"pending")
)
conn.commit()

#show data
print("Users:",cursor.execute("SELECT * FROM users").fetchall())
print("Listings:",cursor.execute("SELECT * FROM listings").fetchall())
print("Requests:",cursor.execute("SELECT * FROM requests").fetchall())


conn.close()