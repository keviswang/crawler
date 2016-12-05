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
        c.execute("SELECT count(url) FROM WEBSITES")
        count = c.fetchone()[0]
        if len(data)==0:
            c.execute('INSERT INTO WEBSITES(url) VALUES(:url)', {'url': url})
            print('新录入网址：' + url)
            count = count + 1
            print('当前已经录入：' + count + '个')
            db.commit()
