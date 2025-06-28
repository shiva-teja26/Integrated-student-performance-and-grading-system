import sqlite3

con = sqlite3.connect('studentrecords.db')
c = con.cursor()

try:
    c.execute("ALTER TABLE StudentData ADD COLUMN Grade TEXT")
    con.commit()
    print("Grade column added successfully.")
except sqlite3.OperationalError:
    print("Column already exists or another issue occurred.")

con.close()
