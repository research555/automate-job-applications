from selenium import webdriver
from selenium.webdriver.common.by import By
import random
import math
from dotenv import load_dotenv
import os
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time
import regex as re
import mysql.connector
import pdb

class WebsiteScraper:

    def __init__(self):
        self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
        self.cursor, self.mydb = self.db_auth()


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


    def healthtech(self):

        self.driver.get('https://www.norwayhealthtech.com/member')
        groups = self.driver.find_elements(By.CSS_SELECTOR, 'li.group')
        for index, group in enumerate(groups):
            links = group.find_elements(By.TAG_NAME, 'a')
            total_links = len(links) * len(groups)
            for link in links:
                final_url = link.get_attribute('href')
                query = 'INSERT INTO htwebsites (link) VALUES (%s)'
                self.cursor.execute(query, (final_url,))
                self.mydb.commit()
                print(f'Inserted {index + 1} of {total_links} links')

        self.driver.close()

    def webcruiter(self):
        pass

    def finn(self):
        pass
