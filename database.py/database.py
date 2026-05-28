import sqlite3

#create/connect database
conn = sqlite3.connect('mmu_xxchange.db')
cursor = conn.cursor()

#user table (NO EMAIL)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL

#create user table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE NOT NULL,
               email TEXT UNIQUE NOT NULL,password TEXT NOT NULL
                                  
               )
               ''' )

#listing table
cursor.execute('''
               CREATE TABLE IF NOT EXISTS listings(id INTEGER PRIMARY KEY AUTOINCREMENT,
               tittle TEXT NOT NULL,
               price REAL ,
               user_id INTEGER,
               FOREIGN KEY(user_id)REFERENCES users(id)
               )
               ''')

#request table
cursor.execute('''
               CREATE TABLE IF NOT EXISTS requests(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               listing_id INTEGER,
               requester_id INTEGER,
               status TEXT DEFAULT 'pending',
               FOREIGN KEY(listing_id) REFERENCES listings(id),
               FOREIGN KEY(requester_id) REFERENCES users(id)
             
               )
               ''')
#save changes
conn.commit()
conn.close()

print("Database created succesfully")