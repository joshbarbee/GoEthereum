import json
import mysql.connector
import pprint

mydb = mysql.connector.connect(
  host="localhost",
  user="josh",
  password="password",
  database="blockchain"
)

curs = mydb.cursor()

curs.execute("SELECT * FROM traces WHERE id='1674209'")
print("fetched")

for i in curs.fetchall():
    pprint.pprint(json.load(i))


mydb.close()