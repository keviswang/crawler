from google import search
import csv
import sqlite3

db = sqlite3.connect('result.db')
c = db.cursor()
c.execute("""create table if not exists websites (
        id    INTEGER PRIMARY KEY,
        url    text NOT NULL)""")
db.commit()

keywords = [line.rstrip('\n') for line in open('keywords.txt')]

for words in keywords:
    for url in search(words, num=1, start=0):
        c.execute("SELECT url FROM WEBSITES WHERE url = ?", (url,))
        data=c.fetchall()
        if len(data)==0:
            c.execute('INSERT INTO WEBSITES(url) VALUES(:url)', {'url': url})
            db.commit()
