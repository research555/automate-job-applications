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
from utils import StringDict, Database

class HealthTech:
    """
    A class to scrape information from the Norwegian HealthTech website and insert it into a MySQL database.

    Attributes:
    -----------
    table_name : str
        The name of the table in the database where the scraped data will be inserted.

    Methods:
    --------
    __init__(self, table_name: str) -> None
        Initializes the database connection and sets up the Edge driver for scraping.

    scrape_healthtech_norway(limit=None) -> str
        Scrape information from the Norwegian HealthTech website and insert it into the specified table in the database.
        If a limit is specified, the function will only scrape the first `limit` links returned by the database query.
        Returns a message indicating the number of links inserted into the database.

    _insert_into_db() -> None
        Inserts the scraped data into the specified database table.

    _get_columns() -> list
        Returns a list of column names in the specified database table.

    _get_links(limit: int = 3000) -> list
        Returns a list of links from the specified database table, up to a specified limit.

    _update_info_points_healthtech() -> None
        Updates the dictionary of scraped information points with information from the HealthTech website.

    _get_info_points() -> list
        Returns a list of information points for the specified database table.

    close() -> None
        Quit the Edge driver used for scraping.

    """

    def __init__(self, table_name: str):
        """
        Initializes the database connection and sets up the Edge driver for web scraping.

        Args:
            table_name: Name of the table in the database to connect to.
        """

        self.table_name = table_name
        self.cursor, self.mydb = Database(table_name=self.table_name).db_auth()
        self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())

    def scrape_healthtech_norway(self, limit=None):
        """
            Scrapes the HealthTech Norway website for company information and inserts it into the connected database.

            Args:
                limit: (Optional) Limits the number of links to be scraped. Default is None.

            Yields:
                A string indicating the number of rows inserted into the database.
        """
        if limit:
            links = self._get_links(limit)
        else:
            links = self._get_links()

        for index, (link,) in enumerate(links):
            info_points = {
                'Company name': None,
                'Contact person': None,
                'Mobile': None,
                'Email': None,
                'Address': None,
                'Web': None,
                'Employees': None,
                'about': None
            }
            self.driver.get(link)
            time.sleep(2)
            self._update_info_points_healthtech()
            self.columns = ['name', 'contact_person', 'number', 'email', 'address', 'link', 'employees', 'about']
            self.info_points = StringDict(info_points)
            self._insert_into_db()
            yield f"Inserted {index + 1} of {len(links)}"

    def _insert_into_db(self):
        """
           Inserts the scraped information into the connected database.
        """

        placeholders = ', '.join(['%s'] * len(self.info_points.values()))
        query = f"INSERT INTO {self.table_name} ({', '.join(self.columns)}) VALUES ({placeholders})"
        self.cursor.execute(query, (self.info_points['Company name'], self.info_points['Contact person'], self.info_points['Mobile'],
                                    self.info_points['Email'], self.info_points['Address'], self.info_points['Web'], self.info_points['Employees'],
                                    self.info_points['about'],))
        self.mydb.commit()

    def _get_columns(self):
        """
        Retrieves the column names from the specified table in the connected database.

        Returns:
            A list of column names.
        """

        query = f"SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'{self.table_name}'"
        self.cursor.execute(query)
        columns = self.cursor.fetchall()
# return {column[3]: None for column in columns} use if you want to return a dictionary with column names as keys
        return [column[3] for column in columns]

    def _get_links(self, limit: int = 3000):
        """
        Retrieves a specified number of links from the specified table in the connected database.

        Args:
            limit: (Optional) Limits the number of links to be retrieved. Default is 3000.

        Returns:
            A list of links.
        """

        query = f"SELECT link FROM {self.table_name} LIMIT {limit}"
        try:
            self.cursor.execute(query)
            links = self.cursor.fetchall()
            return links
        except Exception as e:
            raise e

    def _update_info_points_healthtech(self):
        """
        Scrapes the HealthTech Norway website for information about a company.
        """

        self.info_points['Company name'] = self.driver.find_element(By.XPATH,
                                                               '/html/body/div[2]/div/article/div[1]/div[2]/div[2]/h1').text
        self.info_points['about'] = self.driver.find_element(By.CLASS_NAME, 'member-body').text
        info = self.driver.find_elements(By.CLASS_NAME, 'info')
        company_details = []
        for i in info:
            company_details.append([x for x in i.text.split('\n') if x != ''])
        # Appends new info points to the dictionary if the company_details list contains one of the keys
        # in the info_points dictionary
        # for the healthtech website, I use headers to inform my insertion. Other websites might not have headers so
        # this specific functionality is only useful for the healthtech website.
        for i in company_details:
            for j in i:
                if j in self.info_points.keys():
                    self.info_points[j] = i[i.index(j) + 1]
        # removes keys with None values which makes it easier to insert into the database
        for key, value in self.info_points.items():
            if value is None:
                self.info_points.pop(key)

    def _get_info_points(self):
        """
        Retrieves the column names from the specified table in the connected database.
        """

        self._get_columns()

    def close(self):
        """
        Closes the Edge driver instance.
        """

        self.driver.quit()


ht = HealthTech()