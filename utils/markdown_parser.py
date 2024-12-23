import os
import re
import pytz  # Import pytz for timezone handling
import sqlite3
import shutil
from datetime import datetime
from tkinter import Tk, filedialog, simpledialog, messagebox

# Define the base directory for the app
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))

# Define the path to the data directory and the database file
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_NAME = os.path.join(DATA_DIR, "trades.db")

# Define the backups path under the `data` directory
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)  # Ensure the backups directory exists


# Helper function to clean markdown formatting
def clean_markdown_text(text):
    """
    Remove markdown formatting like bold, italic, and surrounding symbols.
    """
    if not text:
        return ""

    # Remove **bold**, *italic*, __bold__, _italic_
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)  # Remove bold
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)  # Remove italic

    # Remove stray asterisks or underscores
    text = re.sub(r'[*_]', '', text)

    # Strip extra whitespace
    return text.strip()


class DatabaseManager:
    @staticmethod
    def get_accounts():
        """
        Retrieve all accounts from the database.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM accounts")
            accounts = cursor.fetchall()
            conn.close()
            return accounts
        except Exception as e:
            print(f"Error fetching accounts: {e}")
            return []

    @staticmethod
    def insert_trade(trade_entry, account_id):
        """
        Insert a trade entry into the database for the specified account.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            sql = """
                INSERT INTO trades (
                    account_id, filename, position_size, opened, closed,
                    pips_gained_lost, profit_loss, risk_reward, strategy_used,
                    open_day, open_time, trade_outcome, open_month,
                    trade_duration_minutes, killzone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            )
            cursor.execute(sql, values)
            conn.commit()
            conn.close()
            print(f"Trade '{trade_entry.get('filename')}' inserted.")
        except sqlite3.IntegrityError:
            print(f"Trade '{trade_entry.get('filename')}' already exists.")
        except Exception as e:
            print(f"Error inserting trade: {e}")


def parse_markdown_file(file_path):
    """
    Parse a markdown file to extract trade details.
    Skips trades with invalid or missing critical fields.
    """
    trade_entry = {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Extract fields using regex
        fields = {
            "position_size": r"Position\s*Size\s*:\s*(.*)",
            "opened": r"Opened\s*:\s*(.*)",
            "closed": r"Closed\s*:\s*(.*)",
            "pips_gained_lost": r"Pips\s*Gained/Lost\s*:\s*(.*)",
            "profit_loss": r"Profit/Loss\s*:\s*(.*)",
            "risk_reward": r"R/R\s*:\s*(.*)",
            "strategy_used": r"Strategy\s*Used\s*:\s*(.*)",
        }

        for key, pattern in fields.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                trade_entry[key] = clean_markdown_text(match.group(1).strip())

        # Skip trades marked as missed or with missing profit_loss
        if not trade_entry.get("profit_loss") or trade_entry["profit_loss"].strip() == "#":
            print(f"Skipping missed or invalid trade: '{file_path}'")
            return None

        # Parse and clean 'opened' and 'closed' fields
        raw_opened = clean_markdown_text(trade_entry.get("opened", ""))
        raw_closed = clean_markdown_text(trade_entry.get("closed", ""))

        if raw_opened and raw_closed:
            try:
                opened_time = datetime.strptime(raw_opened, "%d/%m/%Y %H:%M")
                closed_time = datetime.strptime(raw_closed, "%d/%m/%Y %H:%M")
                trade_entry["trade_duration_minutes"] = max(0, (closed_time - opened_time).total_seconds() // 60)
                trade_entry["open_day"] = opened_time.strftime("%A")
                trade_entry["open_time"] = opened_time.strftime("%H:%M")
                trade_entry["open_month"] = opened_time.strftime("%B")
            except ValueError as e:
                print(f"Error parsing dates in file '{file_path}': {e}")
                return None

        # Determine killzone
        trade_entry["killzone"] = determine_killzone(raw_opened)

        # Clean and interpret 'profit_loss' to determine trade outcome
        profit_loss_cleaned = re.sub(r"[^\d\.\-\+]", "", trade_entry.get("profit_loss", ""))
        try:
            profit_loss_value = float(profit_loss_cleaned)
            trade_entry["profit_loss"] = profit_loss_cleaned
            if profit_loss_value > 0.5:
                trade_entry["trade_outcome"] = "Win"
            elif abs(profit_loss_value) < 0.5:
                trade_entry["trade_outcome"] = "Break Even"
            else:
                trade_entry["trade_outcome"] = "Loss"
        except ValueError:
            return None

        trade_entry["filename"] = os.path.basename(file_path)

    except Exception as e:
        print(f"Error parsing file '{file_path}': {e}")
        return None

    return trade_entry


def determine_killzone(opened_time):
    """
    Determine the killzone for the given opened time.
    """
    try:
        rome_tz = pytz.timezone("Europe/Rome")
        opened_time = datetime.strptime(clean_markdown_text(opened_time), "%d/%m/%Y %H:%M").astimezone(rome_tz)
        hour = opened_time.hour

        if 2 <= hour < 5:
            return "London"
        elif 7 <= hour < 10:
            return "New York"
        return "Other"
    except Exception as e:
        print(f"Error determining killzone: {e}")
        return "Unknown"


# GUI and file import logic
def import_trades():
    """
    Main function to handle trade import with GUI for account and folder selection.
    """
    try:
        root = Tk()
        root.withdraw()

        accounts = DatabaseManager.get_accounts()
        if not accounts:
            messagebox.showerror("Error", "No accounts found. Please create an account first.")
            return

        account_names = [f"{account[1]} ({account[0]})" for account in accounts]
        account_selection = simpledialog.askstring(
            "Select Account", "\n".join(account_names) + "\n\nEnter Account ID:"
        )
        # Validate the account selection
        try:
            account_selection = int(account_selection)  # Ensure it's an integer
            valid_account_ids = [account[0] for account in accounts]  # IDs from the database
            if account_selection not in valid_account_ids:
                messagebox.showerror("Error", "Invalid account selection. Please enter a valid Account ID.")
                return
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Invalid input. Please enter a numeric Account ID.")
            return

        folder_path = filedialog.askdirectory(title="Select Folder Containing Trades")
        if not folder_path:
            messagebox.showerror("Error", "No folder selected.")
            return

        account_name = next(account[1] for account in accounts if account[0] == account_selection)
        account_folder = os.path.join(BACKUP_DIR, account_name)
        os.makedirs(account_folder, exist_ok=True)

        for file_name in os.listdir(folder_path):
            if file_name.endswith(".md"):
                file_path = os.path.join(folder_path, file_name)
                trade_entry = parse_markdown_file(file_path)
                if trade_entry:
                    DatabaseManager.insert_trade(trade_entry, account_selection)
                    shutil.copy(file_path, account_folder)
                else:
                    print(f"Skipped '{file_name}' due to errors during parsing.")

        messagebox.showinfo("Success", "Trades imported successfully.")
        exit()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    import_trades()
