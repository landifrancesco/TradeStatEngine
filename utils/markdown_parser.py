import os
import re
import pytz
import sqlite3
import shutil
from datetime import datetime
from tkinter import Tk, filedialog, simpledialog, messagebox

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_NAME = os.path.join(DATA_DIR, "trades.db")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


# Helper: Clean Markdown Text
def clean_markdown_text(text):
    """
    Remove markdown formatting like bold, italic, and symbols.
    """
    if not text:
        return ""
    # Remove markdown emphasis (**bold**, *italic*, __bold__, _italic_)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    # Remove stray markdown characters, but not numbers/symbols next to digits
    text = re.sub(r'(?<!\d)[*_](?!\d)', '', text)
    return text.strip()


# Database Manager
class DatabaseManager:
    @staticmethod
    def get_accounts():
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
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            sql = """
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
            cursor.execute(sql, values)
            conn.commit()
            conn.close()
            print(f"Trade '{trade_entry.get('filename')}' inserted.")
        except sqlite3.IntegrityError:
            print(f"Trade '{trade_entry.get('filename')}' already exists.")
        except Exception as e:
            print(f"Error inserting trade: {e}")


# Parse Markdown File
def parse_markdown_file(file_path):
    """
    Parse a markdown file to extract trade details.
    """
    trade_entry = {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        fields = {
            "time_writing": r"Time\s*writing\s*:\s*(\d{2}:\d{2}\s\d{2}/\d{2}/\d{4})",
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

        # Check for missed trades
        if trade_entry.get("profit_loss") == "#" or not trade_entry.get("profit_loss"):
            return None

        # Ensure Time Writing exists
        if not trade_entry.get("time_writing"):
            while True:
                manual_input = input(
                    f"Enter 'Time Writing' (Format: HH:MM DD/MM/YYYY) for '{os.path.basename(file_path)}': ")
                try:
                    datetime.strptime(manual_input, "%H:%M %d/%m/%Y")
                    trade_entry["time_writing"] = manual_input
                    break
                except ValueError:
                    print("Invalid format. Try again.")

        # Parse opened and closed timestamps
        raw_opened = trade_entry.get("opened", "").strip()
        raw_closed = trade_entry.get("closed", "").strip()
        if raw_opened and raw_closed:
            try:
                opened_time = datetime.strptime(clean_markdown_text(raw_opened), "%d/%m/%Y %H:%M")
                closed_time = datetime.strptime(clean_markdown_text(raw_closed), "%d/%m/%Y %H:%M")

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
                trade_entry["trade_outcome"] = "Break Even"
            else:
                trade_entry["trade_outcome"] = "Loss"
        except ValueError:
            trade_entry["trade_outcome"] = "Unknown"

        trade_entry["filename"] = os.path.basename(file_path)

    except Exception as e:
        print(f"Error parsing file '{file_path}': {e}")
        return None

    return trade_entry


def determine_killzone(opened_time):
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
        try:
            account_selection = int(account_selection)
            valid_account_ids = [account[0] for account in accounts]
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

        for file_name in os.listdir(folder_path):
            if file_name.endswith(".md"):
                file_path = os.path.join(folder_path, file_name)
                trade_entry = parse_markdown_file(file_path)
                if trade_entry:
                    DatabaseManager.insert_trade(trade_entry, account_selection)
                    shutil.copy(file_path, os.path.join(BACKUP_DIR, f"Account_{account_selection}"))
                else:
                    print(f"Skipped '{file_name}' due to errors during parsing.")

        messagebox.showinfo("Success", "Trades imported successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


# Main Import Function
if __name__ == "__main__":
    import_trades()