import mysql.connector

def get_db_connection():
    """
    Returns a MySQL connection for the Smart Course Registration System.
    Requires mysql-connector-python installed.
    """
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="jivansh1", 
        database="course_registration"
    )

def test_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Check if registrations exist
        cursor.execute("SELECT COUNT(*) FROM registrations")
        reg_count = cursor.fetchone()[0]
        
        print(f"Successfully connected to MySQL 'course_registration' database!")
        print(f"Found {user_count:,} users and {reg_count:,} registrations.")
        
        conn.close()
    except Exception as e:
        print("Database connection failed!")
        print(e)

if __name__ == "__main__":
    test_connection()
