from simplegmail import Gmail
import os
import mysql.connector
from dotenv import load_dotenv


class SendEmails:
    """
     A class for sending job application emails to companies in the health tech industry.

     Args:
     table_name (str): The name of the database table to query for company and contact details.

     Attributes:
     cursor: The database cursor object used to execute SQL queries.
     mydb: The database connection object.
     gmail: The Gmail API client used to send emails.
     path_to_cv (str): The file path to the applicant's CV.
     table_name (str): The name of the database table to query for company and contact details.
     details: A list of tuples containing company, contact person, and email information.

     Methods:
     DbAuth(): Authenticates the database connection and returns a cursor and connection object.
     send_email(): Sends job application emails to companies in the health tech industry.
     _get_details(): Queries the database for company and contact details and stores them in the `details` attribute.
     _change_label(): Changes the label of a sent email based on the job application stage.
     _insert_data(): Inserts data into the database after sending an email.

     """

    def __init__(self, table_name):
        self.cursor, self.mydb = self.DbAuth()
        self.gmail = Gmail()
        self.path_to_cv = r'C:\Users\imran\OneDrive\Desktop\Admin Documents\Job\CV\Final PDFs\CV Imran Nooraddin PYDS.pdf'
        self.table_name = table_name

    def DbAuth(self):
        # init database

        load_dotenv()

        # # # # Define auth details # # # #

        DB_HOSTNAME = os.getenv('DB_HOSTNAME')
        DB_USERNAME = os.getenv('DB_USERNAME')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_DATABASE = os.getenv('DB_DATABASE')

        # # # # Connect to MySQL Database# # # #

        self.mydb = mysql.connector.connect(
            host=DB_HOSTNAME,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )

        self.cursor = self.mydb.cursor(buffered=True)  # Name the cursor something simple for easier use

        return self.cursor, self.mydb

    def send_email(self):

        self._get_details()
        for index, (company, name, email) in enumerate(self.details):
            company = company.removesuffix(' AS')
            print(f'Company name: {company}\n Number: {index + 1}/{len(self.details)}\n email: {email}\n Name = {name}')
            body = f"""<p>Dear {name},</p>
            <p>I am a 26 year old Norwegian national who recently graduated from a Masters degree in Bioinformatics and Synthetic Biology from Paris. However, for the past two years, I have been working in Data Science and Python back-end development, specializing in NLP and classification. I have experience fine-tuning spacy models for various projects.</p>
            <p>I have recently moved back to Norway and am interested in building a career in Health Tech. I came across {company} and was impressed with what I found. I would love the opportunity to explore how I can contribute to your company.</p>
            <p>If possible, I would appreciate the chance to have a chat with you and learn more about the company and any potential opportunities. Please let me know if this would be possible, and if so, what dates/times work for you. I have attached my CV on the email for your reference.</p>
            <p>Thank you for your time and consideration. I look forward to hearing back from you.</p>
            <p>Best regards,</p>
            <p>Imran</p>"""

            self.message = self.gmail.send_message(sender='imran.nooraddin+jobapp@cri-paris.org',
                                         to=str(email),
                                         subject=f'Norwegian data scientist interested in {company}',
                                         msg_html=body,
                                         attachments=[self.path_to_cv])
            self._change_label(job_app=True)
            self.cursor.execute(f"UPDATE healthtech SET sent_email = 1 WHERE email = '{email}'")
            self.mydb.commit()

    def _get_details(self):
        query = f"SELECT name, contact_person, email FROM {self.table_name} WHERE email is not NULL LIMIT 5000"
        self.cursor.execute(query)
        self.details = self.cursor.fetchall()

    def _change_label(self, job_app=None, job_first_interview=None, job_second_interview=None , job_offer=None, job_reject=None):
        if job_app:
            self.message.add_label('Label_7243226149938612958')
        if job_first_interview:
            pass
        if job_second_interview:
            pass
        if job_offer:
            pass
        if job_reject:
            pass

    def _insert_data(self):
        #for after you figure out why self.email doesnt work.
        pass
        #cursor.execute(f"UPDATE healthtech SET sent_email = 1 WHERE email = '{self.email}'")
        #mydb.commit()




