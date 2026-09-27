import mysql.connector

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS scraper_app")
    cursor.execute("USE scraper_app")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            username VARCHAR(255), 
            email VARCHAR(255), 
            password VARCHAR(255)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            title VARCHAR(255), 
            price VARCHAR(255), 
            rating VARCHAR(255), 
            availability VARCHAR(255)
        )
    """)
    db.commit()
    print("Database and tables created successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'db' in locals():
        db.close()
