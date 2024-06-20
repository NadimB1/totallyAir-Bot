from http import client
import os
import sys
import time
import psycopg2
import requests
import boto3
from flask import Flask, request, render_template
from apscheduler.schedulers.blocking import BlockingScheduler
from psycopg2 import Error
import logging
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO


logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w', 
                    format='%(name)s - %(levelname)s - %(message)s')

app = Flask(__name__)


print("Script started")

# Function to retrieve data from Athena
def get_athena_data():
    athena = boto3.client('athena', 
                      region_name='us-east-1', 
                      aws_access_key_id='YOUR KEY', 
                      aws_secret_access_key='YOUR KEY')
    # Code to retrieve data from Athena goes here.
    # This function should return the data you want to send to the user.

# Function to send a message to the user
def send_message(recipient_id, message):
    data = {
        "messaging_type": "RESPONSE",
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message
        }
    }
    response = requests.post(nanananananananannanana)

# Function to get a connection to the database
def get_db_connection():
    try:
        return conn
    except Error as e:
        logging.error("Unable to connect to the database")
        logging.error(e)


@app.route("/privacy")
def privacy():
    return app.send_static_file('privacy.html')

@app.route("/", methods=['GET'])
def verify():
    logging.info('Entered verify()')
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == "your verify token here":
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return render_template('index.html'), 200


@app.route("/", methods=['POST'])
def receive_message():
    try:
        output = request.get_json()
        for event in output['entry']:
            messaging = event.get('messaging', [])
            for message in messaging:
                if message.get('message'):
                    recipient_id = message['sender']['id']
                    message_text = message['message'].get('text', '')

                    conn = get_db_connection()
                    cur = conn.cursor()

                    # check if user already exists in database
                    cur.execute("""
                    SELECT * FROM users WHERE user_id = %s
                    """, (recipient_id,))
                    user = cur.fetchone()

                    if message_text.lower() == 'subscribe':
                        if user:
                            send_message(recipient_id, "You are already subscribed.")
                        else:
                            cur.execute("""
                            INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING
                            """, (recipient_id,))
                            conn.commit()
                            send_message(recipient_id, "You are now subscribed.")

                    elif message_text.lower().startswith('update me'):
                        if user:
                            # Extract the department number from the message
                            try:
                                department_number = int(message_text.split(' ')[2])
                            except (IndexError, ValueError):
                                send_message(recipient_id, "Please specify a department number after 'update me'.")
                                return "Message Processed", 200

                            if department_number not in [75, 77, 78, 91, 92, 93, 94, 95]:
                                send_message(recipient_id, "Invalid department number. Please choose from 75, 77, 78, 91, 92, 93, 94, 95.")
                                return "Message Processed", 200


                            # Send an intermediate message to inform user that bot is fetching data
                            send_message(recipient_id, "Thank you, wait a moment while I check.")

                            # Create a message with the data
                            message = create_message(department_number)
                            # Send the message to the user
                            send_message(recipient_id, message)
                        else:
                            send_message(recipient_id, "You need to subscribe before requesting updates.")
                    else:
                        send_message(recipient_id, "I'm sorry, I didn't understand that. Please send 'subscribe' to subscribe or 'update me' to get instructions.")

                    cur.close()
                    conn.close()
    except Exception as e:
        logging.error("Error occurred while processing the message")
        logging.error(e)

    return "Message Processed", 200



def query_data_for_department(department_number):
    # Initialize the S3 client
    s3 = boto3.client('s3', 
                        region_name='us-east-1', 
                        aws_access_key_id='YOUR KEY', 
                        aws_secret_access_key='YOUR KEY')
    # Get today's date
    today = datetime.now()

    # Try to get the file for today's date, if it doesn't exist, try the previous day, and so on
    for i in range(7):
        date = today - timedelta(days=i)
        file_name = f'pollens_daily/csv_pollen_{date.strftime("%d-%m-%Y")}.csv'  # Include the folder name here

        try:
            # Get the object from S3
            s3_object = s3.get_object(Bucket='air-quality-data-totallyair', Key=file_name)
            # Get the body of the object (the CSV file)
            body = s3_object['Body']
            # Read the CSV file into a pandas DataFrame
            df = pd.read_csv(body)
            break
        except Exception as e:
            logging.error("Error occurred while reading data from S3")
            logging.error(e)
            continue

    # Filter the DataFrame for the specified department
    department_data = df[df['departement'] == department_number]

    # Return the data
    return department_data


def create_message(department_number):
    # Query the data for the specified department
    department_data = query_data_for_department(department_number)

    # Extract the date from the DataFrame
    date_de_fin = department_data['time'].values[0]

    # Define the levels of pollen
    levels = {
    0: "insignificant",
    1: "a little bit present",
    2: "present",
    3: "a lot present",
    4: "pollen crisis"
    }

    # Define the percentages of pollen
    percentages = {
    0: "0-25%",
    1: "25-50%",
    2: "50-75%",
    3: "75-100%"
    }
    messages = []

    pollen_columns = ['cypres', 'noisetier', 'aulne', 'peuplier', 'saule', 'frene', 'charme', 'bouleau', 'platane', 'chene', 'olivier', 'tilleul', 'chataignier', 'rumex', 'graminees', 'plantain', 'urticacees', 'armoises', 'ambroisies', 'pollens']

    for column in pollen_columns:
        level = department_data[column].values[0]
        # Only include the pollen type in the message if its level is 2, 3, or 4
        if level >= 2:
            percentage = percentages[level]
            level_description = levels[level]
            message = f"The {column} is {level_description} ({percentage})."
            messages.append(message)
    # Combine all the messages into one message
    message = f"On {date_de_fin} in department {department_number}, " + " ".join(messages) + " Stay safe and breathe easy!"
    return message



logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.info("Starting app")

def log(message):
    print(message)
    sys.stdout.flush()

if __name__ == "__main__":
    logging.info('Running the application')
    app.run(port=8080)
