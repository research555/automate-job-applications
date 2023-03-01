from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException, ElementClickInterceptedException, NoSuchElementException
import selenium.common.exceptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from dotenv import load_dotenv
import os
import time
import regex as re
import mysql.connector
from random import randint
import traceback
import sys
import pdb

"""

In webcruiter, the beginning of the link ie www.2006.webcruiter.com, denotes the id of the company in the database.
In this case the company ID is 2006.

Use this code to find it: company_id = re.search(r'www.(\d+).webcruiter.com', webcruiter_link).group(1)


"""


class WebcruiterScraper:
    load_dotenv()

    def __init__(self):
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.job_board_link = os.getenv('JOB_BOARD_LINK')
        self.job_search_bar_xpath = os.getenv('JOB_SEARCH_BAR_XPATH')
        self.job_cards_xpath = os.getenv('JOB_CARDS_XPATH')
        self.show_more_xpath = os.getenv('SHOW_MORE_BUTTON_XPATH')
        self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
        self.logged_in = False
        self.cursor, self.mydb = self.db_auth()
        self.applied = False

    @staticmethod
    def db_auth():
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

    # # # # SCRAPE JOB LINK METHODS # # # #

    # Refactor this method to be more efficient
    def scrape_jobs(self, job_title: str = None, job_type: bool = False):
        if not self.logged_in:
            self._login()

        if job_type:
            self._choose_job_by_type(job_type=True)
        else:
            self._choose_job_by_search(job_title=job_title)

        self._expose_all_jobs()
        job_cards_block = self.driver.find_elements(By.XPATH, self.job_cards_xpath)
        job_cards = job_cards_block[0].find_elements(By.TAG_NAME, 'a')

        for index, job in enumerate(job_cards):
            ad_link = job.get_attribute('href')
            pattern = r'(?<=Webcruiter-ID: )\d+'
            webcruiter_id = re.search(pattern, job.text).group(0)
            job_link = self._make_job_link(webcruiter_id)

            try:
                assert str(ad_link)
                assert str(webcruiter_id)
                self._insert_into_db(webcruiter_id=webcruiter_id, ad_link=ad_link, job_link=job_link)
                print(f'Inserted {webcruiter_id} into database. index {index - 1} of {len(job_cards)}')
            except mysql.connector.errors.IntegrityError:
                print(f'Job {webcruiter_id} already in database. index {index} of {len(job_cards)}')
            except (mysql.connector.errors.DataError, selenium.common.exceptions.WebDriverException) as e:
                print(e)
                webcruiter_id = str(self._random_id(n=6))
                self._insert_into_db(webcruiter_id=webcruiter_id, ad_link=ad_link, job_link=job_link, collection_error=True)
                print(f'Job {webcruiter_id} has a problem. Link inserted with random id')
            except AssertionError:
                print('Assertion error')
                pass

        return

    @staticmethod
    def _make_job_link(webcruiter_id):
        return f'https://candidate.webcruiter.com/cv?advertid={webcruiter_id}'


    @staticmethod
    def _random_id(n):
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        return randint(range_start, range_end)

    def _login(self):
        self.driver.get('https://candidate.webcruiter.com/en-gb')
        self.driver.find_element(By.TAG_NAME, 'input').send_keys(f'{self.email}', Keys.ENTER)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="Login_Password_show"]')))
        self.driver.find_element(By.XPATH, '//*[@id="Login_Password_show"]'
                                  ).send_keys(f'{self.password}', Keys.ENTER)
        time.sleep(5)
        self.logged_in = True

    # refactor this method to be more efficient
    def _choose_job_by_type(self, job_type): # job_type not implemented yet but can be later on.
        self.driver.get(self.job_board_link)
        time.sleep(5)
        try:
            self.driver.find_element(By.ID, 'expand-all').click()
        except ElementNotInteractableException:
            pass
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="facetList"]/li[3]/div[2]/ul/li[30]/label/input')))
        self.driver.find_element(By.XPATH, '//*[@id="facetList"]/li[3]/div[2]/ul/li[30]/label/input').click()  # Click on the job type (dev rn)
        time.sleep(5)

    # refactor this method to be more efficient
    def _choose_job_by_search(self, job_title):
        self.driver.get(self.job_board_link)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.job_search_bar_xpath)))
        self.driver.find_element(By.XPATH, self.job_search_bar_xpath).send_keys(f'{job_title}')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'search-button')))
        self.driver.find_element(By.ID, 'search-button').click()
        time.sleep(5)
        return

    def _expose_all_jobs(self):
        for i in range(1, 100):
            try:
                self.driver.find_element(By.XPATH, self.show_more_xpath).click()
                print(f'Clicked {i} times')
                time.sleep(2)
            except ElementNotInteractableException:
                break

    # # # # SCRAPE JOB LINK METHODS # # # #
    # # # # APPLY TO JOB METHODS # # # #

    def apply_to_jobs(self):
        if not self.logged_in:
            self._login()
        result = self._get_jobs_from_db()
        for index, (link, job_id) in enumerate(result):
            print('starting on job ', index, ' of ', len(result))
            self.driver.get(link)
            time.sleep(3)
            if index >= 1:
                self._wait_for_loading()
            if self._check_if_applied() is True:
                print('Already applied to job')
                self._set_job_status(job_id=str(job_id))

                continue
            panels = self._determine_panels_present()
            try:
                for function, value in panels.items():
                    if value:
                        function()

            except Exception:
                self._set_job_status(job_id=job_id, error=True)
                print(traceback.format_exc())
                continue
            self._set_job_status(job_id=job_id)
            print('waiting for loading')
            self._wait_for_loading()
            print('waiting for loading done')
            time.sleep(5)

    def _check_if_applied(self):

        try:
            self.driver.find_element(By.ID, 'contentTop2')
            self.applied = False
            return False
        except NoSuchElementException:
            self.applied = True
            return True

    def _determine_panels_present(self):
        try:
            personalia_master = self.driver.find_element(By.ID, 'contentTop2')
            personalia_panel = personalia_master.find_element(By.CLASS_NAME, 'panel')

            cover_master = self.driver.find_element(By.ID, 'contentApplicationLetter')
            cover_panel = cover_master.find_element(By.CLASS_NAME, 'panel')

            priority_master = self.driver.find_element(By.ID, 'priority-form')
            priority_panel = priority_master.find_element(By.XPATH, './/div[contains(@data-bind, "visible: isPriorityVisible")]')

            reference_master = self.driver.find_element(By.ID, 'contentReferences')
            reference_panel = reference_master.find_element(By.XPATH, './/div[contains(@data-bind, "showReferenceDetails")]')

            panels = {self._fill_personalia: personalia_panel.is_displayed(),
                      self._fill_cover_letter: cover_panel.is_displayed(),
                      self._fill_priority: priority_panel.is_displayed(),
                      self._fill_references: reference_panel.is_displayed(),
                      self._submit_application: True
                    }
            return panels
        except NoSuchElementException:
            return None

    def _wait_for_loading(self): # will go on forever so need a way to break out. maybe use a counter or time.
        time.sleep(1)
        loading = True
        start_time = time.time()
        while loading:
            try:
                loading_modal = self.driver.find_element(By.ID, 'loadingModal')
                loading = 'we-loading' in loading_modal.get_attribute('class')
                if time.time() - start_time > 120:
                    raise TimeoutError('Loading took too long')
            except NoSuchElementException:
                time.sleep(3)
                loading = False

    def _fill_personalia(self): #functional

        personalia_master = self.driver.find_element(By.ID, 'contentTop2')
        tab = personalia_master.find_element(By.CLASS_NAME, 'panel')
        confirm_permit = personalia_master.find_element(By.XPATH, '//input[@name="WorkingPermit" and @value="true"]')
        edit = personalia_master.find_element(By.XPATH, "//button[contains(@data-bind, 'click:editPersonalia')]")
        save = personalia_master.find_element(By.XPATH, '//button[contains(@data-bind, "click:save")]')

        if 'we-panel-collapsed' in tab.get_attribute('class'):
            tab.click()
            time.sleep(2)
            self._wait_for_loading()

        if not save.is_displayed():
            edit.click()
            self._wait_for_loading()

        if confirm_permit.is_displayed():
            self.driver.execute_script("arguments[0].click();", confirm_permit)  # clicks regardless of intercepted cuz fuck the police
        time.sleep(3)
        save.click()
        self._wait_for_loading()

    def _fill_cover_letter(self):

        cover_letter = f""" Jeg har nylig fullført en mastergrad i bioinformatikk og syntetisk biologi i Paris. Men de siste to årene har jeg jobbet med data science og Python back-end-utvikling, med spesialisering innen NLP og klassifisering. Jeg har erfaring med finjustering av spacy-modeller, hugging face transformers og web scraping for ulike prosjekter.
        \nJeg har nylig flyttet tilbake til Norge og er interessert i å bygge en karriere innen tek, maskinlæring, og AI. Jeg leste gjennom jobbannonsen på WebCruiter og så meg selv i mange av kravene. Jeg vil gjerne ha muligheten til å utforske hvordan jeg kan bidra til selskapet ditt.
        \nHvis det er mulig, ville jeg satt pris på sjansen til å snakke med deg og lære mer om dere, og hvordan mine ferdigheter kan komme til nytte her. """

        cover_master = self.driver.find_element(By.ID, 'contentApplicationLetter')
        panel = cover_master.find_element(By.CLASS_NAME, 'panel')
        edit = panel.find_element(By.XPATH, './/button[contains(@data-bind, "click:makeApplicationTextEditMode")]')
        save = panel.find_element(By.XPATH, './/button[contains(@data-bind, "click:saveCoverLetter")]')
        textbox = panel.find_element(By.XPATH, '//*[@id="ApplicationText"]')

        if 'we-panel-collapsed' in panel.get_attribute('class'):
            panel.click()
            time.sleep(2)

        if edit.is_displayed():
            self.driver.execute_script("arguments[0].click();", edit)  # clicks regardless of intercepted
            time.sleep(2)
            self._wait_for_loading()

        if textbox.get_attribute('value'):
            textbox.clear()

        textbox.send_keys(cover_letter)
        time.sleep(5)
        save.click()
        time.sleep(2)
        if save.is_displayed():
            save.click()

    def _fill_priority(self): #functional
        # get priority div
        priority_master = self.driver.find_element(By.ID, 'priority-form')
        checkbox = priority_master.find_element(By.XPATH, '//label[contains(@for, "PriorityForeign")]')
        collapsed = priority_master.find_element(By.XPATH, './/div[@data-bind="slide: isPriorityExpanded"]')
        save = priority_master.find_element(By.XPATH, './/button[contains(@data-bind, "click:savePriorityFlags")]')
        check_checkbox = priority_master.find_element(By.XPATH,'.//div[contains(@data-bind, "slide: isPiorityForeignInfoVisible")]')

        if 'none;' in collapsed.get_attribute('style'):
            priority_master.click()
            time.sleep(3)

        priority_master.click()  # allows checkbox to be visible
        time.sleep(2)
        self._wait_for_loading()
        if checkbox.is_displayed() and 'display: none;' in check_checkbox.get_attribute('style'):
            checkbox.click()  # always comes up as false for some reason even if its checked...
            time.sleep(2)
            print('added priority')
            self._wait_for_loading()

        save.click()

    def _fill_references(self):

        # expand references dropdown
        reference_master = self.driver.find_element(By.ID, 'contentReferences')
        display_state = self.driver.find_element(By.XPATH,
                                            '//*[contains(@data-bind, "slide: showReferenceDetails")]').get_attribute(
            'style')
        reference_selection = reference_master.find_element(By.TAG_NAME, 'select')
        nika_value = '4743588'
        bikard_value = '4988655'
        save = reference_master.find_element(By.XPATH, '//button[contains(@data-bind, "click:saveSelected")]')
        references = [nika_value, bikard_value]
        if 'display: none;' in display_state:
            reference_master.click()
            time.sleep(2)
            self._wait_for_loading()

        select_box = Select(reference_selection)
        for reference in references:
            select_box.select_by_value(reference)
            time.sleep(1)
            print(f'added {reference}')
            self._wait_for_loading()

            try:
                save.click()
            except NoSuchElementException:
                continue
            except (ElementClickInterceptedException, ElementNotInteractableException):
                self.driver.execute_script("arguments[0].click();", save)
            finally:
                time.sleep(1)

    def _submit_application(self):

        send_application_button = self.driver.find_element(By.XPATH, './/a[contains(@data-bind, "click:send")]')
        if send_application_button.is_displayed():
            send_application_button.click()
            print('application sent')
            time.sleep(5)
            self._wait_for_loading()
        else:
            # here you can first check if it is possible to maybe hit save on remaining fields and then try again.
            # if not then you can just raise an error.
            raise Exception('Application button not found')

    def _set_job_status(self, job_id: str, error: bool = False):
        if error:
            self.cursor.execute(f"UPDATE webcruiter_ads SET applied_error = '1' WHERE webcruiter_id = '{job_id}'")
            self.mydb.commit()
            return

        self.cursor.execute(f"UPDATE webcruiter_ads SET applied = 1 WHERE webcruiter_id = '{job_id}'")
        self.mydb.commit()

    def _get_jobs_from_db(self):
        #FIXME: this is a placeholder for now, but should be replaced with a query to the database
        self.cursor.execute("SELECT job_link, webcruiter_id FROM webcruiter_ads")
        results = self.cursor.fetchall()

        return results

    def _insert_into_db(self, ad_link: str, job_link: str,  webcruiter_id: str = None, scrape_error: bool = None,
                        collection_error: bool = None, applied_error: bool = None):

        if scrape_error is not None:
            pass
        elif collection_error is not None:
            self.cursor.execute(f'INSERT INTO webcruiter_ads (ad_link, webcruiter_id, collection_error) '
                                f'VALUES ("{ad_link}", "{webcruiter_id}", "{int(collection_error)}")')
            self.mydb.commit()

        elif applied_error is not None:
            pass
        try:
            self.cursor.execute(f'INSERT INTO webcruiter_ads (webcruiter_id, ad_link, job_link) VALUES ("{webcruiter_id}", "{ad_link}", "{job_link}")')
            self.mydb.commit()
            return True
        except mysql.connector.errors.IntegrityError:
            pass

    def temp_driver(self):
        return self.driver

    def close(self):
        self.driver.close()
        self.mydb.close()

if __name__ == '__main__':
    scraper = WebcruiterScraper()
    scraper.apply_to_jobs()


    """
    scraper.scrape_jobs(job_type=True)
    scraper.scrape_jobs(job_title='Software Engineer')
    scraper.scrape_jobs(job_title='datavitenskap')
    scraper.scrape_jobs(job_title='data science')
    scraper.scrape_jobs(job_title='data scientist')
    scraper.scrape_jobs(job_title='dataingeniør')
    scraper.scrape_jobs(job_title='data engineer')
    scraper.close()
    
    """









