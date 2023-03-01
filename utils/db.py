import os
import regex as re

import mysql.connector
from dotenv import load_dotenv


class Database:
    #expand gradually as things make sense
    def __init__(self, table_name):
        self.cursor, self.mydb = self.db_auth()
        self.table_name = table_name

    def db_auth(self):
        # init database

        load_dotenv()

        # # # # Define auth details # # # #

        DB_HOSTNAME = os.getenv('DB_HOSTNAME')
        DB_USERNAME = os.getenv('DB_USERNAME')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_DATABASE = os.getenv('DB_DATABASE')

        # # # # Connect to MySQL Database# # # #

        mydb = mysql.connector.connect(
            host=DB_HOSTNAME,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )

        cursor = mydb.cursor(buffered=True)  # Name the cursor something simple for easier use

        return cursor, mydb

    def get_links(self, limit=None):
        if limit:
            self.cursor.execute(f"SELECT * FROM {self.table_name} LIMIT {limit}")
        else:
            self.cursor.execute(f"SELECT * FROM {self.table_name}")
        links = self.cursor.fetchall()
        return links
