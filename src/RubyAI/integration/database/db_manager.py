import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
import mysql.connector
from mysql.connector.errors import Error as MySQLError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DatabaseManager:
    """Core database manager handling connections and basic operations."""
    
    _instance = None

    def __new__(cls):
        """Ensure singleton pattern for database connections."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the database manager."""
        # Skip initialization if already initialized
        if hasattr(self, 'connection'):
            return
            
        self.logger = logging.getLogger(__name__)
        
        # Basic database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME')
        }
        
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.logger.info("Database connection initialized successfully")
        except MySQLError as e:
            self.logger.error(f"Failed to initialize database connection: {e}")
            raise

    def get_connection(self):
        """Get the database connection, reconnecting if necessary."""
        try:
            if not self.connection.is_connected():
                self.connection.reconnect()
            return self.connection
        except MySQLError as e:
            self.logger.error(f"Failed to get database connection: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Union[List[Dict], None]:
        """
        Execute a query and return results if any.
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch and return results
            
        Returns:
            List of dictionaries containing query results if fetch=True
            None if fetch=False or no results
        """
        connection = self.get_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                
                if fetch:
                    result = cursor.fetchall()
                    return result if result else None
                else:
                    connection.commit()
                    return None
                    
        except MySQLError as e:
            self.logger.error(f"Database error executing query: {e}")
            connection.rollback()
            raise

    def execute_many(self, query: str, params: List[tuple]) -> None:
        """Execute multiple similar queries efficiently."""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.executemany(query, params)
                connection.commit()
        except MySQLError as e:
            self.logger.error(f"Database error executing multiple queries: {e}")
            connection.rollback()
            raise

    def begin_transaction(self):
        """Begin a new transaction."""
        connection = self.get_connection()
        try:
            connection.start_transaction()
            return connection
        except MySQLError as e:
            self.logger.error(f"Failed to begin transaction: {e}")
            raise

    def execute_in_transaction(self, connection, query: str, params: tuple = None, 
                             fetch: bool = True) -> Union[List[Dict], None]:
        """Execute a query within an existing transaction."""
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                if fetch:
                    result = cursor.fetchall()
                    return result if result else None
                return None
        except MySQLError as e:
            self.logger.error(f"Database error in transaction: {e}")
            raise

    def health_check(self) -> bool:
        """Verify database connection and basic functionality."""
        try:
            self.execute_query("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False

    def __del__(self):
        """Ensure database connection is closed when object is destroyed."""
        if hasattr(self, 'connection') and self.connection.is_connected():
            self.connection.close()
