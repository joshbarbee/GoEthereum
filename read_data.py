import json
import mysql.connector
import pprint
import os
from dotenv import load_dotenv

load_dotenv()

mydb = mysql.connector.connect(
  host="localhost",
  user="josh",
  password=os.getenv('DBPASS'),
  database="blockchain"
)

curs = mydb.cursor()

id = 90000

curs.execute(f"SELECT * FROM traces WHERE id='{id}'")
for i in curs.fetchall():
  
  pprint.pprint(json.loads(list(i)[7]))


mydb.close()