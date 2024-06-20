import pandas as pd
from joblib import load
import psycopg2
import re
from datetime import datetime, timedelta
import boto3
import joblib
import numpy as np

# Create a boto3 client for S3
s3 = boto3.client('s3',
                  region_name='us-east-1',
                  aws_access_key_id='REMOVED_FOR_SECURITY_REASONS',
                  aws_secret_access_key='REMOVED_FOR_SECURITY_REASONS')

# Get the latest file from S3
response = s3.list_objects_v2(Bucket='air-quality-data-totallyair', Prefix='gazs_data/')
all_objects = response['Contents']

# Filter out the files that start with "FR_E2_"
data_files = [obj for obj in all_objects if obj['Key'].startswith('gazs_data/FR_E2_')]
# Get the most recent file
latest_file = data_files[-1]

# Get the object key
object_key = latest_file['Key']

# Download the object from S3
s3.download_file('air-quality-data-totallyair', object_key, 'local.csv')

# Read the CSV file into a pandas DataFrame
today_df = pd.read_csv('local.csv', delimiter=';')

#-------------------------------------------------------
def custom_agg(x):
    if pd.api.types.is_string_dtype(x):
        return x.iloc[0]
    elif pd.api.types.is_numeric_dtype(x):
        return x.mean()
    else:
        return np.nan

# Filter rows based on 'Zas' column
#data = data[data['Zas'].isin(['ZR ILE-DE-FRANCE', 'ZAR SAINT-DENIS'])]

# Replace the pollutants as per the given conditions
today_df['Polluant'] = today_df['Polluant'].replace({'NO': 'NO2', 'NOX': 'NO2', 'NOX as NO2': 'NO2', 'PM2.5': 'PM25'})

# Remove rows with 'C6H6', 'SO2', and 'CO' in the 'Polluant' column
today_df = today_df[~today_df['Polluant'].isin(['C6H6', 'SO2', 'CO'])]

# Define the columns of interest
cols_of_interest = ['Date de début', 'Date de fin', 'Polluant', 'valeur', 'code qualité', 'unité de mesure']

# Remove rows with empty values in columns of interest
today_df = today_df.dropna(subset=cols_of_interest)

# Convert 'Date de fin' to datetime format and extract the date only
today_df['Date de fin'] = pd.to_datetime(today_df['Date de fin']).dt.date

# Group by 'Date de fin', 'Polluant', and 'Zas' and calculate the mean of 'valeur'
# Also keep the other columns by taking the first value in each group
grouped_data = today_df.groupby(['Date de fin', 'Polluant', 'Zas']).agg(custom_agg).reset_index()

# Drop the specified columns
grouped_data = grouped_data.drop(columns=['taux de saisie', 'couverture temporelle', 'couverture de données'])
grouped_data['unité de mesure'] = grouped_data['unité de mesure'].str.replace('Â', '')
# Select columns to keep based on the analysis
cols_to_keep = ['Date de fin', 'Polluant', 'Zas', "type d'implantation", "type d'influence", "type d'évaluation", 'procédure de mesure', 'valeur', 'code qualité', 'unité de mesure']

# Create a new DataFrame with only the columns to keep
today_df = grouped_data[cols_to_keep]

#-------------------------------------------------------
# Preprocess the 'today' data
today_df = today_df.iloc[:, :-1]
today_df['Date de fin'] = pd.to_datetime(today_df['Date de fin'])
today_df['code qualité'] = today_df['code qualité'].fillna('U')
today_df['Polluant'] = today_df['Polluant'].replace({'NO': 'NO2', 'NOX': 'NO2', 'NOX as NO2': 'NO2', 'PM2.5': 'PM25'})
today_df = today_df[~today_df['Polluant'].isin(['C6H6', 'SO2', 'CO'])]
# Also load the training column names
training_features = joblib.load('models2/features_sample.pkl')


# One-hot encode the 'today' data
encoded_today_df = pd.get_dummies(today_df)

# Get the features in the 'today' data after one-hot encoding
today_features = encoded_today_df.columns

# Find the missing and extra features
missing_features = set(training_features) - set(today_features)
extra_features = set(today_features) - set(training_features)

# Add the missing features to the 'today' data with a value of 0
encoded_today_df = pd.concat([encoded_today_df, pd.DataFrame(columns=list(missing_features))], axis=1).fillna(0)


# Remove the extra features from the 'today' data
encoded_today_df = encoded_today_df.drop(columns=list(extra_features))

# Ensure the 'today' data has the same feature order as the training data
encoded_today_df = encoded_today_df[training_features]

# Load the models from disk
loaded_linear_regressor = joblib.load('models2/linear_regressor_sample.pkl')
loaded_logistic_classifier = joblib.load('models2/logistic_classifier_sample.pkl')
loaded_label_encoder = joblib.load('models2/label_encoder_sample.pkl')

# Fill NaN values with zero
encoded_today_df = encoded_today_df.fillna(0)

# Make predictions
predictions_value = loaded_linear_regressor.predict(encoded_today_df)
predictions_quality_encoded = loaded_logistic_classifier.predict(encoded_today_df)


# Decode the predicted 'code qualité'
predictions_quality = loaded_label_encoder.inverse_transform(predictions_quality_encoded)


# Create a DataFrame for the predictions
predictions_df = pd.DataFrame({
    'Date de fin': today_df['Date de fin'] + pd.DateOffset(days=1),  # the date for the predictions is the next day
    'Polluant': today_df['Polluant'],
    'Zas': today_df['Zas'],
    'valeur': predictions_value,
    'code qualité': predictions_quality
})

# Append the predictions for the day after tomorrow
predictions_df_2 = predictions_df.copy()
predictions_df_2['Date de fin'] = predictions_df_2['Date de fin'] + pd.DateOffset(days=1)  # the date for the predictions is two days later
predictions_df = pd.concat([predictions_df, predictions_df_2])
# Filter the predictions for the 'Zas' value 'ZR ILE-DE-FRANCE'
predictions_df_filtered = predictions_df[predictions_df['Zas'] == 'ZR ILE-DE-FRANCE']

predictions_df_filtered = predictions_df_filtered.tail(4)

#--------------------------------------------------
#INJECT IN RDS TABLE AFTER CHECKING IF THE DATE IN DATAFRAME IS THE SUCCESSOR OF THE LAST DATE IN RDS OR NOT
# Establish the connection to RDS (fill with your actual credentials)
conn = psycopg2.connect(
    dbname="REMOVED_FOR_SECURITY_REASONS",
    user="REMOVED_FOR_SECURITY_REASONS",
    password="REMOVED_FOR_SECURITY_REASONS",
    host="REMOVED_FOR_SECURITY_REASONS",
    port="REMOVED_FOR_SECURITY_REASONS"
)

# Create a cursor object
cur = conn.cursor()

# Check the latest date in the RDS table
query = "SELECT MAX(\"Date de fin\") FROM predictions_gazs"

# Execute the query
cur.execute(query)

# Fetch the result of the query
latest_date = cur.fetchone()[0]

# Get the date in the DataFrame
df_date = predictions_df_filtered["Date de fin"].max()

if latest_date is None or df_date.date() >= (latest_date + timedelta(days=1)):
# Prepare the INSERT INTO SQL query
    query = """
        INSERT INTO predictions_gazs ("Date de fin", "Polluant", "Zas", "valeur", "code qualité")
        VALUES (%s, %s, %s, %s, %s)
    """

    # Convert 'Date de fin' to date and DataFrame to a list of tuples
    predictions_df_filtered['Date de fin'] = predictions_df_filtered['Date de fin'].dt.date
    records = predictions_df_filtered[['Date de fin', 'Polluant', 'Zas', 'valeur', 'code qualité']].to_records(index=False).tolist()

    # Execute the query for each record
    for record in records:
        cur.execute(query, record)

    # Commit the changes
    conn.commit()
else:
    print("The date in the DataFrame is not the next day of the latest date in the RDS table. Not inserting any data.")

# Close the cursor and the connection
cur.close()
conn.close()
