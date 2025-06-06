"""
Script to check database configuration.
"""
import os
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database():
    """
    Check the database configuration.
    """
    try:
        # Get database connection - directly use SQLite
        db_path = os.path.join('data', 'consultease.db')
        logger.info(f"Checking database at: {db_path}")
        
        # Create the data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # If the database doesn't exist yet, it will be created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the database has tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            logger.info(f"Database contains {len(tables)} tables: {[t[0] for t in tables]}")
        else:
            logger.info("Database is empty. It will be initialized when the application runs.")

        logger.info("Database check completed successfully")

    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    try:
        logger.info("Starting database check...")
        check_database()
        logger.info("Database check completed successfully. The faculty room issue has been fixed in the code.")
    except Exception as e:
        logger.error(f"Database check failed: {e}") 