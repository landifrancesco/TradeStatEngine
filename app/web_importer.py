from flask import Flask, jsonify, request, render_template
import os
import sqlite3
import re
import pytz
import shutil
import requests
from datetime import datetime
from werkzeug.utils import secure_filename

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_NAME = os.path.join(DATA_DIR, "trades.db")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
ALLOWED_EXTENSIONS = {'md'}

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

# ------------------------------------------------------------------------------
# Helper function to fetch data from the backend (e.g. the list of accounts)
def fetch_data(endpoint, params=None):
    try:
        response = requests.get(f"http://127.0.0.1:5000{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Parse Markdown File
def parse_markdown_file(file_path):
    trade_entry = {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Define regex patterns for each field
        fields = {
            "position_size": r"Position\s*Size:\s*[\*_~]*([\d\.]+)[\*_~]*",
            "opened": r"Opened:\s*[\*_~]*(\d{2}/\d{2}/\d{4} \d{2}:\d{2})[\*_~]*",
            "closed": r"Closed:\s*[\*_~]*(\d{2}/\d{2}/\d{4} \d{2}:\d{2})[\*_~]*",
            "pips_gained_lost": r"Pips\s*Gained/Lost:\s*[\*_~]*([+-]?\d+)[\*_~]*",
            "profit_loss": r"Profit/Loss:\s*[\*_~]*([+-]?\d+(?:\.\d+)?[€$])[\*_~]*",
            "risk_reward": r"R/R:\s*[\*_~]*([\d\.]+)[\*_~]*",
            "strategy_used": r"Strategy\s*[Uu]sed:\s*[\*_~]*([^\n\*_~]+)[\*_~]*",
        }

        for key, pattern in fields.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                trade_entry[key] = match.group(1).strip()

        # Extract the first occurrence of the time of writing
        time_writing_match = re.search(r"Time writing:\s*(\d{2}:\d{2}) (\d{2}/\d{2}/\d{4})", content)
        if time_writing_match:
            raw_time = f"{time_writing_match.group(2)} {time_writing_match.group(1)}"
            # Parse into datetime and reformat as the other dates
            dt = datetime.strptime(raw_time, "%d/%m/%Y %H:%M")
            formatted_time_writing = dt.strftime("%d/%m/%Y %H:%M")
            trade_entry["time_writing"] = formatted_time_writing

        # Parse opened and closed timestamps
        raw_opened = trade_entry.get("opened", "").strip()
        raw_closed = trade_entry.get("closed", "").strip()
        if raw_opened and raw_closed:
            try:
                opened_time = datetime.strptime(raw_opened, "%d/%m/%Y %H:%M")
                closed_time = datetime.strptime(raw_closed, "%d/%m/%Y %H:%M")
                trade_entry["trade_duration_minutes"] = max(0, (closed_time - opened_time).total_seconds() // 60)
                trade_entry["open_day"] = opened_time.strftime("%A")
                trade_entry["open_time"] = opened_time.strftime("%H:%M")
                trade_entry["open_month"] = opened_time.strftime("%B")
                trade_entry["killzone"] = determine_killzone(raw_opened)
            except ValueError as e:
                print(f"Error parsing dates in file '{file_path}': {e}")
                return None

        # Determine trade outcome
        profit_loss_cleaned = re.sub(r"[^\d\.\-\+]", "", trade_entry.get("profit_loss", ""))
        try:
            profit_loss_value = float(profit_loss_cleaned)
            trade_entry["profit_loss"] = profit_loss_cleaned
            if profit_loss_value > 0.5:
                trade_entry["trade_outcome"] = "Win"
            elif abs(profit_loss_value) < 0.5:
                trade_entry["trade_outcome"] = "Break-even"
            else:
                trade_entry["trade_outcome"] = "Loss"
        except ValueError:
            trade_entry["trade_outcome"] = "Unknown"

        trade_entry["filename"] = os.path.basename(file_path)

    except Exception as e:
        print(f"Error parsing file '{file_path}': {e}")
        return None

    return trade_entry

# Determine Killzone
def determine_killzone(opened_time):
    try:
        rome_tz = pytz.timezone("Europe/Rome")
        opened_time = datetime.strptime(opened_time.strip(), "%d/%m/%Y %H:%M").astimezone(rome_tz)
        hour = opened_time.hour
        if 2 <= hour < 5:
            return "London"
        elif 7 <= hour < 10:
            return "New York"
        return "Other"
    except Exception as e:
        print(f"Error determining killzone: {e}")
        return "Unknown"

# Insert Trade into Database
def insert_trade_into_db(trade_entry, account_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        query = """
            INSERT INTO trades (
                account_id, filename, position_size, opened, closed, 
                pips_gained_lost, profit_loss, risk_reward, strategy_used,
                open_day, open_time, trade_outcome, open_month, 
                trade_duration_minutes, killzone, time_writing
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            account_id,
            trade_entry.get("filename"),
            trade_entry.get("position_size"),
            trade_entry.get("opened"),
            trade_entry.get("closed"),
            trade_entry.get("pips_gained_lost"),
            trade_entry.get("profit_loss"),
            trade_entry.get("risk_reward"),
            trade_entry.get("strategy_used"),
            trade_entry.get("open_day"),
            trade_entry.get("open_time"),
            trade_entry.get("trade_outcome"),
            trade_entry.get("open_month"),
            trade_entry.get("trade_duration_minutes"),
            trade_entry.get("killzone"),
            trade_entry.get("time_writing"),
        )
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error inserting trade into database: {e}")
        return False

# Move Processed File to Account-Specific Folder
def move_processed_file(file_path, account_id):
    try:
        account_folder = os.path.join(UPLOAD_DIR, f"Account_{account_id}")
        os.makedirs(account_folder, exist_ok=True)
        shutil.move(file_path, account_folder)
    except Exception as e:
        print(f"Error moving processed file: {e}")

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        # Fetch the list of accounts from the backend
        accounts = fetch_data('/accounts')
        if not accounts:
            print("No accounts fetched from backend. Please ensure the backend is running and accessible.")
            accounts = [{"id": 0, "name": "No Accounts Available"}]
        return render_template('upload.html', accounts=accounts)

    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            trade_entry = parse_markdown_file(file_path)

            # Ensure trade_entry includes all expected keys, even if empty
            expected_keys = [
                "position_size", "opened", "closed", "pips_gained_lost",
                "profit_loss", "risk_reward", "strategy_used", "open_day",
                "open_time", "trade_outcome", "open_month",
                "trade_duration_minutes", "killzone", "time_writing", "filename"
            ]
            trade_entry = {key: trade_entry.get(key, "") for key in expected_keys}

            # Include extracted values in the JSON response
            response_data = {
                "parsed_data": trade_entry,
                "message": "",
                "status": "success"
            }

            if trade_entry:
                account_id = request.form.get("account_id")
                if not account_id:
                    response_data["message"] = "Account ID is required"
                    response_data["status"] = "error"
                    return jsonify(response_data), 400

                if insert_trade_into_db(trade_entry, account_id):
                    move_processed_file(file_path, account_id)
                    response_data["message"] = "File uploaded and trade saved successfully"
                    return jsonify(response_data), 200
                else:
                    response_data["message"] = "Failed to save trade to database"
                    response_data["status"] = "error"
                    return jsonify(response_data), 500
            else:
                response_data["message"] = "Failed to parse the file"
                response_data["status"] = "error"
                return jsonify(response_data), 500
        return jsonify({"error": "Invalid file format"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)

