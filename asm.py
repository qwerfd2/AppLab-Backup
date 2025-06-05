import requests
import json
import time
import os
import csv
from datetime import datetime

CSRF = ""
SESSION = ""
tables = []
key_value = {}
channel = ""
LOGIN_SESSION = ""
LOGIN_CSRF = ""

cwd = os.getcwd()
settings_file = os.path.join(cwd, "settings.cfg")

if os.path.exists(settings_file):
    try:
        with open(settings_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

        if len(lines) > 0:
            channel = lines[0].strip()
            print("Loaded channel:", channel)

        if len(lines) > 1 and lines[1].startswith("_learn_session=") and not lines[1].endswith(";"):
            LOGIN_SESSION = lines[1].strip()
            print("Loaded LOGIN_SESSION:", LOGIN_SESSION)

        if len(lines) > 2:
            LOGIN_CSRF = lines[2].strip()
            print("Loaded LOGIN_CSRF:", LOGIN_CSRF)

    except Exception as e:
        print(f"An error occurred while reading {settings_file}: {e}")
    
if channel == "":
        channel = input("Enter channel ID: ")


base_url = f"https://studio.code.org/datablock_storage/{channel}/"
csrf_url = f"https://studio.code.org/projects/applab/{channel}"
channel_url = f"https://studio.code.org/v3/channels/{channel}"
asset_url = f"https://studio.code.org/v3/assets/{channel}"
source_url = f"https://studio.code.org/v3/sources/{channel}"

# Get USER_CSRF and USER_SESSION from the regular page.
def init_data():
    global CSRF, SESSION

    if CSRF and SESSION:
        return

    response = requests.get(csrf_url)
    if response.status_code == 200:
        response_text = response.text

        # Extract CSRF token
        meta_start = response_text.find('<meta name="csrf-token" content="')
        if meta_start != -1:
            content_start = response_text.find('content="', meta_start) + 9
            content_end = response_text.find('"', content_start)
            CSRF = response_text[content_start:content_end]

        # Extract SESSION token
        set_cookie_header = response.headers.get('Set-Cookie', '')
        token_start = set_cookie_header.find('_learn_session=')
        token_end = set_cookie_header.find(';', token_start) + 1
        SESSION = set_cookie_header[token_start:token_end]

init_data()

print("Obtained USER_CSRF:", CSRF)
print("Obtained USER_SESSION:", SESSION)

def set_login_credential(learn_session, csrf):
    if learn_session[:15] != "_learn_session=" or learn_session[-1] != ";":
        print("cookie must start with '_learn_session=' and ends with the subsequent ';'. Aborted.")
        return
    global LOGIN_CSRF, LOGIN_SESSION
    LOGIN_CSRF = csrf
    LOGIN_SESSION = learn_session
    print("LOGIN credentials set.")

def remove_login_credential():
    global LOGIN_CSRF, LOGIN_SESSION
    LOGIN_CSRF = ""
    LOGIN_SESSION = ""
    print("LOGIN credentials removed.")

import os

def save_settings_config():
    global channel, LOGIN_SESSION, LOGIN_CSRF
    
    current_dir = os.getcwd()
    config_file = os.path.join(current_dir, "settings.cfg")
    backup_file = os.path.join(current_dir, "settings.cfg.bak")
    
    if os.path.exists(config_file):
        os.rename(config_file, backup_file)
        print(f"Existing 'settings.cfg' renamed to 'settings.cfg.bak'.")

    content_lines = [channel]
    if LOGIN_SESSION:
        content_lines.append(LOGIN_SESSION)
    if LOGIN_CSRF:
        content_lines.append(LOGIN_CSRF)
    
    try:
        with open(config_file, "w", encoding="utf-8") as file:
            file.write("\n".join(content_lines))
        print("Current configs saved to 'settings.cfg'.")
    except IOError as e:
        print(f"An error occurred while saving settings: {e}")

def get_all_table_names():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    global tables

    url = base_url + "get_table_names"

    headers = {
        "Content-Type": "application/json",
        "cookie": LOGIN_SESSION
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        tables_data = json.loads(response.text)
        if isinstance(tables_data, list):
            tables = tables_data
        else:
            tables = []
        print("Tables updated: ", tables)
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"An error occurred while fetching table names: {e}")
        tables = []

def get_all_key_value():
    global key_value
    url = f"{base_url}get_key_values"

    headers = {
        "Content-Type": "application/json",
        "cookie": LOGIN_SESSION
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        key_value_data = json.loads(response.text)
        if isinstance(key_value_data, dict):
            key_value = key_value_data
            print(f"key updated with length {len(key_value_data)}")
            for key, value in key_value.items():
                print(f"{key}: {value}")
        else:
            key_value = {}
            print("error: key not dict")
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"An error occurred while fetching key-value pairs: {e}")
        key_value = {}

def get_key_value(key):
    if not isinstance(key, str) or not key:
        print("Invalid key. Please provide a non-empty string.")
        return

    url = f"{base_url}get_key_value?key={key}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        print(response.text)
    except requests.RequestException as e:
        print(f"An error occurred while fetching the key value: {e}")

def set_key_value(key, value):
    value = str(value)

    url = f"{base_url}set_key_value"

    if value.isnumeric():
        value = f'{int(value)}'
    elif value.lower() == "true":
        value = "true"
    elif value.lower() == "false":
        value = "false"
    else:
        value = f'"{value}"'

    payload = {
        "key": key,
        "value": value
    }

    print(json.dumps(payload))

    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": CSRF,
        "cookie": SESSION
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            print("Key-value pair set successfully.")
        else:
            print(f"Failed to set key-value pair. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while setting the key-value pair: {e}")

def delete_key_value(key):

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    if not isinstance(key, str) or not key:
        print("Invalid key. Please provide a non-empty string.")
        return

    url = f"{base_url}delete_key_value"

    payload = {
        "key": key
    }

    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": LOGIN_CSRF,
        "cookie": LOGIN_SESSION
    }

    try:
        response = requests.delete(url, json=payload, headers=headers)
        
        if response.text == "true":
            print("Key-value pair deleted successfully.")
        else:
            print(f"Failed to delete key-value pair. Status code: {response.status_code}, result: {response.text}")
    except requests.RequestException as e:
        print(f"An error occurred while deleting the key-value pair: {e}")

def delete_all_key_value_official():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    get_all_key_value()

    if not isinstance(key_value, dict) or not key_value:
        print("No key-value pairs to delete.")
        return

    for key in list(key_value.keys()):
        print(f"Deleting key: {key}")
        delete_key_value(key)

    print("All key-value pairs have been deleted.")

def delete_all_key_value_unofficial():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    get_all_key_value()

    if not isinstance(key_value, dict) or not key_value:
        print("No key-value pairs to delete.")
        return

    for key in list(key_value.keys()):
        print(f"Deleting key: {key}")
        set_key_value(key, None)

    print("All key-value pairs have been deleted.")

def export_key_value():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    get_all_key_value()

    if not isinstance(key_value, dict) or not key_value:
        print("No key-value pairs to export.")
        return

    time_string = datetime.now().strftime("%Y-%m-%d %H%M")

    home_dir = os.getcwd()
    folder_path = os.path.join(home_dir, channel, "key_value")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{time_string}.csv")

    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow(["Key", "Value"])

            for key, value in key_value.items():
                writer.writerow([key, value])

        print(f"Key-value pairs exported successfully to {file_path}.")
    except IOError as e:
        print(f"An error occurred while exporting to {file_path}: {e}")

def import_key_value(filename):
    if not isinstance(filename, str) or not filename.endswith(".csv"):
        print("Invalid filename. Please provide a valid .csv file name.")
        return

    try:
        with open(filename, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)

            header = next(reader, None)
            if header != ["Key", "Value"]:
                print("Invalid CSV format. Expected header: 'Key,Value'.")
                return

            for row in reader:
                if len(row) != 2:
                    print(f"Skipping invalid row: {row}")
                    continue

                key, value = row
                print(f"Importing key: {key}, value: {value}")
                set_key_value(key, value)

        print(f"Key-value pairs imported successfully from {filename}.")
    except FileNotFoundError:
        print(f"File {filename} not found.")
    except IOError as e:
        print(f"An error occurred while reading {filename}: {e}")

def create_table(table_name):

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return

    url = f"{base_url}create_table"

    payload = {
        "table_name": table_name
    }

    payload_json = json.dumps(payload)

    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": LOGIN_CSRF,
        "cookie": LOGIN_SESSION
    }

    try:
        response = requests.post(url, data=payload_json, headers=headers)

        if response.text == "true":
            print(f"Table '{table_name}' created successfully.")
        else:
            print(f"Failed to create table '{table_name}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while creating the table: {e}")

def create_record(table_name, record_json):
    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return

    if not isinstance(record_json, str):
        print("Invalid record_json. Please provide a valid JSON string.")
        return
    try:
        json.loads(record_json)
    except json.JSONDecodeError:
        print("Invalid JSON string. Please provide a properly formatted JSON string.")
        return

    url = f"{base_url}create_record"

    payload = {
        "table_name": table_name,
        "record_json": record_json
    }

    payload_json = json.dumps(payload)
    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": CSRF,
        "cookie": SESSION
    }

    try:
        response = requests.post(url, data=payload_json, headers=headers)

        if response.status_code == 200:
            print(f"Record '{table_name}' created successfully.")
        else:
            print(f"Failed to create record '{table_name}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while creating the table: {e}")

def delete_table_official(table_name):

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return
    
    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return

    url = f"{base_url}delete_table"

    payload = {
        "table_name": table_name
    }

    payload_json = json.dumps(payload)

    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": LOGIN_CSRF,
        "cookie": LOGIN_SESSION
    }

    try:
        response = requests.delete(url, data=payload_json, headers=headers)

        if response.text == "true":
            print(f"Table '{table_name}' deleted successfully.")
        else:
            print(f"Failed to delete table '{table_name}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while deleting the table: {e}")

def delete_record(table_name, record_id):
    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return

    if not isinstance(record_id, int) or record_id < 0:
        print("Invalid record ID. Please provide a non-negative integer.")
        return

    url = f"{base_url}delete_record"

    payload = {
        "table_name": table_name,
        "record_id": record_id
    }

    payload_json = json.dumps(payload)

    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": CSRF,
        "cookie": SESSION
    }

    try:
        response = requests.delete(url, data=payload_json, headers=headers)

        if response.text == "null":
            print(f"Record with ID {record_id} deleted successfully from table '{table_name}'.")
        else:
            print(f"Failed to delete record with ID {record_id} from table '{table_name}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while deleting the record: {e}")

def read_table(table_name):
    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return

    url = f"{base_url}read_records?table_name={table_name}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            print(f"Records from table '{table_name}' read successfully.")
            try:
                records = response.json()
                print("Records:")
                print(json.dumps(records, indent=4))
            except json.JSONDecodeError:
                print("Failed to decode JSON response.")
        else:
            print(f"Failed to read records from table '{table_name}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while reading records: {e}")

def delete_table_unofficial(table_name):
    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return
    url = f"{base_url}read_records?table_name={table_name}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            try:
                records = response.json()

                if not isinstance(records, list):
                    print(f"Unexpected format for records in table '{table_name}'. Operation aborted.")
                    return

                for record in records:
                    record_id = record.get("id")
                    if isinstance(record_id, int):
                        delete_record(table_name, record_id)
                    else:
                        print(f"Invalid or missing 'id' in record: {record}. Skipping.")

                print(f"All rows in table '{table_name}' deleted successfully.")
            except json.JSONDecodeError:
                print(f"Failed to decode JSON response from table '{table_name}'.")
        else:
            print(f"Failed to read records from table '{table_name}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while processing table '{table_name}': {e}")

def update_record(table_name, record_json):
    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return

    if not isinstance(record_json, str):
        print("Invalid record_json (not string nor json). Please provide a valid JSON string.")
        return

    try:
        record_data = json.loads(record_json)
        record_id = record_data.get("id")

        if not isinstance(record_id, int):
            print("The 'id' field is missing or invalid in the record JSON. Operation aborted.")
            return

        url = f"{base_url}update_record"
        payload = {
            "table_name": table_name,
            "record_id": record_id,
            "record_json": json.dumps(record_data)
        }

        headers = {
            "Content-Type": "application/json",
            "x-csrf-token": CSRF,
            "cookie": SESSION
        }

        response = requests.put(url, data=json.dumps(payload), headers=headers)

        try:
            response_json = response.json()  # Attempt to parse the response as JSON
            if response_json["id"] == record_id:
                print(f"Record with ID {record_id} in table '{table_name}' updated successfully.")
            else:
                print(f"Failed to update record with ID {record_id} in table '{table_name}'. "
                f"Response JSON is not correct. Response text: {response.text}")
        except json.JSONDecodeError:
            print(f"Failed to update record with ID {record_id} in table '{table_name}'. "
                  f"Response is not a valid JSON object. Response text: {response.text}")

    except json.JSONDecodeError:
        print("Invalid JSON string provided. Please ensure the input is a valid JSON string.")
    except requests.RequestException as e:
        print(f"An error occurred while updating the record: {e}")

def delete_all_table_official():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    global tables

    get_all_table_names()

    if not tables:
        print("No tables found to delete.")
        return

    for table_name in tables:
        print(f"Attempting to delete table: {table_name}")
        delete_table_official(table_name)

    print("All tables deletion tried. Check log for result.")

def delete_all_table_unofficial():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    global tables

    get_all_table_names()

    if not tables:
        print("No tables found to delete.")
        return

    for table_name in tables:
        print(f"Attempting to delete table: {table_name}")
        delete_table_unofficial(table_name)

    print("All tables deletion tried. Check log for result.")

def export_table_official(table_name):

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    global channel, CSRF, SESSION
    url = f"{base_url}export_csv?table_name={table_name}"

    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": LOGIN_CSRF,
        "cookie": LOGIN_SESSION
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            home_dir = os.getcwd()

            time_string = datetime.now().strftime("%Y-%m-%d %H%M")
            folder_path = os.path.join(home_dir, channel, table_name)

            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, f"{time_string}.csv")

            with open(file_path, "wb") as file:
                file.write(response.content)

            print(f"Table '{table_name}' exported successfully and saved as '{file_path}'.")
        else:
            print(f"Failed to export table '{table_name}'. HTTP Status Code: {response.status_code}.")
    except Exception as e:
        print(f"An error occurred while exporting the table '{table_name}': {e}")

def export_table_unofficial(table_name):
    global base_url

    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return

    url = f"{base_url}read_records?table_name={table_name}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            print(f"Records from table '{table_name}' read successfully.")
            try:
                records = response.json()

                if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
                    print(f"Invalid data format for table '{table_name}'. Expected a list of dictionaries.")
                    return

                home_dir = os.getcwd()

                time_string = datetime.now().strftime("%Y-%m-%d %H%M")
                folder_path = os.path.join(home_dir, channel, table_name)

                os.makedirs(folder_path, exist_ok=True)
                file_path = os.path.join(folder_path, f"{time_string}.csv")

                with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
                    if records:
                        headers = records[0].keys()
                        writer = csv.DictWriter(csv_file, fieldnames=headers)

                        writer.writeheader()
                        writer.writerows(records)

                    print(f"Table '{table_name}' exported successfully to '{file_path}'.")
                return file_path

            except json.JSONDecodeError:
                print("Failed to decode JSON response.")
        else:
            print(f"Failed to read records from table '{table_name}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while reading records: {e}")

def export_all_table_official():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return
    
    global tables

    get_all_table_names()

    if not tables:
        print("No tables found to export.")
        return

    for table_name in tables:
        print(f"Attempting to export table: {table_name}")
        export_table_official(table_name)

    print("All tables deletion tried. Check log for result.")

def export_all_table_unofficial():
    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    global tables

    get_all_table_names()

    if not tables:
        print("No tables found to export.")
        return

    for table_name in tables:
        print(f"Attempting to export table: {table_name}")
        export_table_unofficial(table_name)

    print("All tables deletion tried. Check log for result.")

def import_table_official(table_name, file_path):
    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return
    
    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return

    if not isinstance(file_path, str) or not file_path.endswith(".csv"):
        print("Invalid file path. Please provide a valid .csv file.")
        return

    if not os.path.exists(file_path):
        print(f"The file {file_path} does not exist.")
        return

    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            csv_data = file.read()
    except IOError as e:
        print(f"An error occurred while reading the file {file_path}: {e}")
        return

    payload = {
        "table_name": table_name,
        "table_data_csv": csv_data
    }
    print(json.dumps(payload))
    url = f"{base_url}import_csv"

    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": LOGIN_CSRF,
        "cookie": LOGIN_SESSION
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Check the response
        if response.text == "true":
            print(f"Table '{table_name}' imported successfully from {file_path}.")
        else:
            print(f"Failed to import table '{table_name}'.")
    except requests.RequestException as e:
        print(f"An error occurred while importing the table: {e}")

def import_table_unofficial(table_name, file_path):
    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return

    if not isinstance(file_path, str) or not file_path.endswith(".csv"):
        print("Invalid file path. Please provide a valid .csv file.")
        return

    if not os.path.exists(file_path):
        print(f"The file {file_path} does not exist.")
        return

    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            csv_reader = csv.DictReader(file)

            rows = [row for row in csv_reader]

            if not rows:
                print(f"The CSV file {file_path} is empty or malformed.")
                return
    except IOError as e:
        print(f"An error occurred while reading the file {file_path}: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred while validating the file: {e}")
        return

    delete_table_unofficial(table_name)

    try:
        for row in rows:
            def parse_value(value):
                if value.isdigit():
                    return int(value)
                if value.lower() == "true":
                    return True
                if value.lower() == "false":
                    return False
                if value.lower() == "":
                    return None
                return value

            processed_row = {key: parse_value(value) for key, value in row.items()}
            record_json = json.dumps(processed_row)
            print(record_json)
            create_record(table_name, record_json)

        print(f"Table '{table_name}' imported successfully from {file_path} using the unofficial method.")
    except Exception as e:
        print(f"An error occurred while importing data to the table: {e}")

def clear_table(table_name):

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    if not isinstance(table_name, str) or not table_name:
        print("Invalid table name. Please provide a non-empty string.")
        return
    
    url = f"{base_url}clear_table"

    payload = {"table_name": table_name}
    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": LOGIN_CSRF,
        "cookie": LOGIN_SESSION,
    }

    try:
        response = requests.delete(url, json=payload, headers=headers)

        if response.text.strip() == "true":
            print(f"Table '{table_name}' cleared successfully.")
        else:
            print(f"Failed to clear table '{table_name}'. Response: {response.text}")
    except requests.RequestException as e:
        print(f"An error occurred while clearing table '{table_name}': {e}")

def delete_project():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    headers = {
        "cookie": LOGIN_SESSION,
    }

    try:
        response = requests.delete(channel_url, headers=headers)

        if response.status_code == 204:
            print("Project deleted successfully.")
        else:
            print(f"Failed to delete the project. Status code: {response.status_code}, Response: {response.text}")
    except requests.RequestException as e:
        print(f"An error occurred while deleting the project: {e}")

def print_metadata():
    str_output = ""

    try:
        base_response = requests.get(channel_url)
        if base_response.status_code == 200:
            base_info = base_response.json()
            str_output += f", project name: {base_info.get('name')}, frozen: {base_info.get('frozen')}, hidden: {base_info.get('hidden')}, Created: {base_info.get('createdAt')}, updated: {base_info.get('updatedAt')}, published: {base_info.get('publishedAt')}"
        else:
            str_output += "Error getting base information, "

        abuse_response = requests.get(f"{channel_url}/abuse")
        if abuse_response.status_code == 200:
            abuse_info = abuse_response.json()
            str_output += f", abuse score: {abuse_info.get('abuse_score')}"
        else:
            str_output += ", error getting abuse score, "

        assets_response = requests.get(asset_url)
        if assets_response.status_code == 200:
            assets = assets_response.json()
            total_size = sum(file.get('size', 0) for file in assets)
            str_output += f", files: {len(assets)}, asset size: {total_size} bytes, "
        else:
            str_output += ", error getting asset information, "

        sharing_response = requests.get(f"{channel_url}/sharing_disabled")
        if sharing_response.status_code == 200:
            sharing_info = sharing_response.json()
            str_output += f"sharing: {not sharing_info.get('sharing_disabled')}."
        else:
            str_output += "error getting sharing permission."

    except requests.RequestException as e:
        print(f"An error occurred: {e}")

    print(str_output)

def edit_metadata(field, value):

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    valid_fields = ["frozen", "hidden", "thumbnailUrl", "name", "projectType"]
    if field not in valid_fields:
        print(f"Invalid field '{field}'. Allowed fields are {valid_fields}.")
        return

    if field in ["frozen", "hidden"]:
        if value != True and value != False:
            print(f"Invalid value for '{field}'. Only 'true' or 'false' are allowed.")
            return

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "cookie": LOGIN_SESSION,
        "x-csrf-token": LOGIN_CSRF,
    }

    try:
        response = requests.get(channel_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch current metadata. Status code: {response.status_code}. Response: {response.text}")
            return
        
        metadata = response.json()

        metadata[field] = value

        print(f"New metadata: {json.dumps(metadata, indent=4)}")

        response = requests.post(channel_url, json=metadata, headers=headers)
        if response.status_code == 200:
            print(f"Successfully updated field '{field}' to '{value}'.")
        else:
            print(f"Failed to update field '{field}'. Status code: {response.status_code}. Response: {response.text}")
    except requests.RequestException as e:
        print(f"An error occurred while updating metadata: {e}")

def download_asset():
    try:
        response = requests.get(asset_url)
        if response.status_code != 200:
            print(f"Failed to fetch asset metadata. Status code: {response.status_code}. Response: {response.text}")
            return

        assets = response.json()
        if not isinstance(assets, list):
            print("Unexpected response format. Expected a list of asset metadata.")
            return
        date_string = datetime.now().strftime("%Y-%m-%d %H%M")
        save_dir = os.path.join(os.getcwd(), channel, date_string)
        os.makedirs(save_dir, exist_ok=True)

        for asset in assets:
            filename = asset.get("filename")
            if not filename:
                print("Filename missing in asset metadata. Skipping this asset.")
                continue

            file_url = f"{asset_url}/{filename}"
            save_path = os.path.join(save_dir, filename)

            try:
                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                    with open(save_path, "wb") as file:
                        file.write(file_response.content)
                    print(f"Downloaded '{filename}' to '{save_path}'.")
                else:
                    print(f"Failed to download '{filename}'. Status code: {file_response.status_code}.")
            except requests.RequestException as e:
                print(f"An error occurred while downloading '{filename}': {e}")
    except requests.RequestException as e:
        print(f"An error occurred while fetching asset metadata: {e}")

def upload_asset(file_path):

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    if not os.path.isfile(file_path):
        print(f"Invalid file: {file_path}")
        return

    supported_types = {"png", "jpg", "jpeg", "jfif", "gif", "mp3", "wav", "pdf", "doc", "docx"}
    file_extension = os.path.splitext(file_path)[-1][1:].lower()

    if file_extension not in supported_types:
        print(f"Unsupported file type: {file_extension}")
        return

    filename = os.path.basename(file_path)

    content_type = f"image/{file_extension}" if file_extension in {"png", "jpg", "jpeg", "jfif", "gif"} else \
                   f"audio/{file_extension}" if file_extension in {"mp3", "wav"} else \
                   f"application/{file_extension}"

    with open(file_path, "rb") as file:
        files = {
            "files[]": (filename, file, content_type)
        }

        headers = {
            "x-csrf-token": LOGIN_CSRF,
            "cookie": LOGIN_SESSION
        }

        response = requests.post(f"{asset_url}/", files=files, headers=headers)

    if response.status_code == 200:
        print(f"File {filename} uploaded successfully.")
    else:
        print(f"Failed to upload file. Status code: {response.status_code}, Response: {response.text}")

def delete_asset(asset_name):

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    if not asset_name:
        print("Invalid asset name. Please provide a valid asset name.")
        return

    delete_url = f"{asset_url}/{asset_name}"

    headers = {
        "cookie": LOGIN_SESSION
    }

    response = requests.delete(delete_url, headers=headers)

    if response.status_code == 204:
        print(f"Asset '{asset_name}' deleted successfully.")
    else:
        print(f"Failed to delete asset '{asset_name}'. Status code: {response.status_code}, Response: {response.text}")

def delete_all_asset():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    try:
        response = requests.get(asset_url)
        if response.status_code != 200:
            print(f"Failed to fetch asset metadata. Status code: {response.status_code}. Response: {response.text}")
            return

        assets = response.json()
        if not isinstance(assets, list):
            print("Unexpected response format. Expected a list of asset metadata.")
            return

        print("Deleting", len(assets), "Asset(s).")

        for asset in assets:
            delete_asset(asset["filename"])

        print("All asset delete attempted.")

    except requests.RequestException as e:
        print(f"An error occurred while fetching asset metadata: {e}")

def get_all_project():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    try:
        headers = {
            "x-csrf-token": LOGIN_CSRF,
            "cookie": LOGIN_SESSION
        }
        response = requests.get("https://studio.code.org/api/v1/projects/personal", headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch asset metadata. Status code: {response.status_code}. Response: {response.text}")
            return

        projects = response.json()
        if not isinstance(projects, list):
            print("Unexpected response format. Expected a list of asset metadata.")
            return

        print(json.dumps(projects, indent=4))
    except requests.RequestException as e:
        print(f"An error occurred while fetching asset metadata: {e}")

def restore_version(version_code):

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    if not version_code:
        print("Invalid version code. Please provide a valid version code.")
        return

    restore_url = f"{source_url}/main.json/restore?version={version_code}"

    headers = {
        "cookie": LOGIN_SESSION
    }

    response = requests.put(restore_url, headers=headers)

    if response.status_code == 200:
        print(f"Version '{version_code}' restored successfully.")
    else:
        print(f"Failed to restore version '{version_code}'. Status code: {response.status_code}, Response: {response.text}")

def get_version():

    if LOGIN_CSRF == "" or LOGIN_SESSION == "":
        print("LOGIN credential not set. Aborting.")
        return

    try:
        headers = {
            "cookie": LOGIN_SESSION
        }
        response = requests.get(source_url + "/main.json/versions", headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch asset metadata. Status code: {response.status_code}. Response: {response.text}")
            return

        assets = response.json()
        if not isinstance(assets, list):
            print("Unexpected response format. Expected a list of asset metadata.")
            return
        print(json.dumps(assets, indent=4))

    except requests.RequestException as e:
        print(f"An error occurred while fetching asset metadata: {e}")

time.sleep(1)

available_functions = {
    "set_login_credential": set_login_credential,
    "remove_login_credential": remove_login_credential,
    "save_settings_config": save_settings_config,
    "print_metadata": print_metadata,
    "edit_metadata": edit_metadata,
    "get_all_table_names": get_all_table_names,
    "get_all_key_value": get_all_key_value,
    "get_key_value": get_key_value,
    "set_key_value": set_key_value,
    "delete_key_value": delete_key_value,
    "delete_all_key_value_official": delete_all_key_value_official,
    "delete_all_key_value_unofficial": delete_all_key_value_official,
    "export_key_value": export_key_value,
    "import_key_value": import_key_value,
    "create_table": create_table,
    "create_record": create_record,
    "delete_table_official": delete_table_official,
    "delete_table_unofficial": delete_table_unofficial, 
    "clear_table": clear_table,
    "delete_record": delete_record,
    "read_table": read_table,
    "update_record": update_record,
    "delete_all_table_official": delete_all_table_official,
    "delete_all_table_unofficial": delete_all_table_unofficial,
    "export_table_official": export_table_official,
    "export_table_unofficial": export_table_unofficial,
    "export_all_table_official": export_all_table_official,
    "export_all_table_unofficial": export_all_table_unofficial,
    "import_table_official": import_table_official,
    "import_table_unofficial": import_table_unofficial,
    "get_all_project": get_all_project,
    "delete_project": delete_project,
    "download_asset": download_asset,
    "upload_asset": upload_asset,
    "delete_asset": delete_asset,
    "delete_all_asset": delete_all_asset,
    "get_version": get_version,
    "restore_version": restore_version,
}

command_descriptions = {
    "set_login_credential": "Set the LOGIN credentials useful for some operations. Browser log in to cdo, go to the project in question, open developer tool, network, look at the main request. Look for _learn_session in Cookie, and x-csrf-token. Enter the two when prompted.",
    "remove_login_credential": "Remove LOGIN credentials.",
    "save_settings_config": "Save the channel and LOGIN credentials to settings.cfg, which will be automatically loaded next time.",
    "print_metadata": "Print various metadata about the project. Requires no permission, Input: none",
    "edit_metadata": "Set various fields to metadata. Requires OWN LOGIN permission. Input: str:field, str:value. Supported fields: 'frozen', 'hidden', 'thumbnailUrl', 'name', 'projectType'",
    "get_all_table_names": "Obtain the names of all the tables under a project. Requires LOGIN credential. Input: none",
    "get_all_key_value": "Obtain all the key-value pairs under a project. Requires LOGIN credential. Input: none",
    "get_key_value": "Obtain a value given key. Requires no credential. Input: str:key",
    "set_key_value": "Set the value given key. Requires USER credential. Input: str:key, str:value",
    "delete_key_value": "Delete the key-value pair given key. Requires LOGIN credential. Input: str:key ",
    "delete_all_key_value_official": "Delete all key-value pair of the project using the official method. Requires LOGIN credential. Input: none",
    "delete_all_key_value_unofficial": "Delete all key-value pair of the project by nulling them. Part still need LOGIN credential. Input: none",
    "export_key_value": "Export all key value a csv file (channel/key_value/time.csv). Requires USER credential. Input: none",
    "import_key_value": "Import all key value from a csv file. Requires USER credential. Input: str:file_path_to_.csv",
    "create_table": "Official way to create a table. Requires LOGIN credential. create_record() does the same and is recommended. Input: str:table_name",
    "create_record": "Can be used to add record to existing table, or create new tables. Requires USER credential. Input: str:table_name, str:json_string",
    "delete_table_official": "Official way to delete a table. Requires LOGIN credential. Input: str:table_name",
    "delete_table_unofficial": "Delete a table unofficially by removing all its records. Requires USER credential. Input: str:table_name",
    "clear_table": "Clear a table using the official method. Functionally same to delete_table_unofficial(). Requires LOGIN credential. Input: str:table_name",
    "delete_record": "Delete a single record. Requires USER credential. Input: str:table_name, int:record_id",
    "read_table": "Read and print the content of a table. No credential required. Input: str:table_name",
    "update_record": "# Update a row of the table. Requires USER credential. Input: str:table_name, str:json_string",
    "delete_all_table_official": "Delete all tables using the official method. Requires LOGIN credential. Input: none",
    "delete_all_table_unofficial": "Delete all tables using the unofficial method. Could be slow. Part still need LOGIN credential. Input: none",
    "export_table_official": "Official way to export a table to csv (channel/table_name/time.csv). Requires LOGIN credential. Input: str:table_name",
    "export_table_unofficial": "Export a table to csv (channel/table_name/time.csv) unofficially. Requires USER credential. Input: str:table_name",
    "export_all_table_official": "# Export all tables using the official method. LOGIN credential required. Input: none",
    "export_all_table_unofficial": "Export all tables using the unofficial method. Part still need LOGIN credential. Input: none",
    "import_table_official": "Import the specified csv to table via official API. Requires LOGIN credential. Input: str:table_name, str:csv_path",
    "import_table_unofficial": "Import by deleting everything, then row by row add. csv won't preserve type differences so we attempt to mirror the official behavior. Requires USER credential. Input: str:table_name, str:csv_path",
    "get_all_project": "Get all the project under the account. Requires OWN LOGIN credential. Inupt: none",
    "delete_project": "Delete a project using the offical method. Requires OWN LOGIN credential. Input: none",
    "download_asset": "Download all assets to folder (channel/time/). Requires no credential. Input: none",
    "upload_asset": "Upload an asset. Requires OWN LOGIN credential. Input: str:path_to_asset",
    "delete_asset": "Delete an asset. Requires OWN LOGIN credential. Input str:asset_name",
    "delete_all_asset": "Delete all the asset. Requires OWN LOGIN credential. Input: none",
    "get_version": "Get all version of the project. Requires OWN LOGIN permission. Input: none",
    "restore_version": "Restore a version to the project. Requires OWN LOGIN credential. Input: str:version_code",
}

def cli():
    print("Welcome to the Applab Management v1.1. Enter a command to invoke a function.")
    print("For safety, we recommend creating dummy accounts for LOGIN credentials, and using a VPN.")
    print("Type 'help' to see the list of available functions or 'exit' to quit.\n")

    while True:
        command = input("Enter command: ").strip()

        if command.lower() == "exit":
            print("Exiting...")
            break

        if command.lower() == "help":
            print("\nAvailable Functions:")
            for func in available_functions:
                description = command_descriptions.get(func, "No description available.")
                print(f" - {func}: {description}")
            print()
            continue

        if command in available_functions:
            func = available_functions[command]
            func_args = func.__code__.co_varnames[:func.__code__.co_argcount]

            if func_args:
                inputs = []
                for arg in func_args:
                    value = input(f"Enter value for {arg}: ").strip()
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass
                    inputs.append(value)

                try:
                    result = func(*inputs)
                    if result is not None:
                        print("Result:", result)
                except Exception as e:
                    print(f"Error occurred: {e}")
            else:
                try:
                    result = func()
                    if result is not None:
                        print("Result:", result)
                except Exception as e:
                    print(f"Error occurred: {e}")
        else:
            print(f"Invalid command: {command}. Type 'help' to see available functions.\n")

if __name__ == "__main__":
    cli()
