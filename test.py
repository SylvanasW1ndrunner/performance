import psycopg2

con = psycopg2.connect(database="postgres",
                       user="postgres",
                       password="123456",
                       host="172.22.0.43",
                       port="8000")
print(con)
print("Database opened successfully")
cur = con.cursor()
cur.execute('SELECT version()')
db_version = cur.fetchone()
print(db_version)
con.close()
