import sqlite3
import os
from colorama import Fore, Style

# Define directories and database file
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_NAME = os.path.join(DATA_DIR, "trades.db")


def is_running_in_docker():
    """
    Check if the script is running inside a Docker container.
    """
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            if 'docker' in f.read() or 'containerd' in f.read():
                return True
    except FileNotFoundError:
        pass

    if os.path.exists('/run/.containerenv'):
        return True

    return False

def first_run():
    """
    Check if the script is running for the first time.
    """
    if not os.path.exists(DB_NAME):
        return True
    else:
        return False

def run():
    if is_running_in_docker() and first_run():
        print("Running in Docker. Initializing database with default Real account...")
        DatabaseManager.setup_database()
        DatabaseManager.create_account("Default", "Real")
        print("Default Real account created. Exiting.")
    else:
        while True:
            print("\nDatabase Utility:")
            print("1. Setup Database")
            print("2. Add account")
            print("3. View accounts & entires")
            print("4. Reset database [DANGEROUS]")
            print("5. Delete trade")
            print("6. Delete account")
            print("7. Exit")

            choice = input("\nEnter your choice: ")
            if choice == "1":
                DatabaseManager.setup_database()

            elif choice == "2":
                name = input("Enter account name: ")
                acc_type = input("Enter account type (Real/Paper): ")
                if acc_type in ["Real", "Paper"]:
                    DatabaseManager.create_account(name, acc_type)
                else:
                    print("Invalid account type.")
                    
            elif choice == "3":
                DatabaseManager.view_all()

            elif choice == "4":
                DatabaseManager.reset_database()

            elif choice == "5":
                accounts = DatabaseManager.get_all_accounts()
                print("\nAvailable accounts:")
                for account in accounts:
                    print(f"ID: {account[0]}, Name: {account[1]}, Type: {account[2]}")
                account_id = input("Enter the account ID to delete the trade from: ")
                DatabaseManager.view_all_entries(account_id)
                entry_id = input("Enter the entry ID to delete: ")
                DatabaseManager.delete_entry_by_id(account_id, int(entry_id))

            elif choice == "6":
                accounts = DatabaseManager.get_all_accounts()
                print("\nAvailable Accounts:")
                for account in accounts:
                    print(f"ID: {account[0]}, Name: {account[1]}, Type: {account[2]}")
                account_id = input("Enter the account ID to delete:")
                confirm = input("Are you completely sure to delete this account? (yes/no): ")
                if confirm.lower() == "yes":
                    DatabaseManager.delete_account(account_id)

            elif choice == "7":
                print("If you like this script you may consider offering me a coffee :D")
                print("Send BEP20, ERC20, BTC, BCH, CRO, LTC, DASH, CELO, ZEC, XRP to:")
                print(Fore.GREEN, "landifrancesco.wallet", Style.RESET_ALL)
                break
            else:
                print("Invalid choice. Please try again.")


class DatabaseManager:
    """
    Utility class for interacting with the database.
    """

    @staticmethod
    def setup_database():
        """
        Create the database and table if they don't exist.
        """
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            conn = sqlite3.connect(DB_NAME, timeout=5)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    filename TEXT UNIQUE,
                    position_size TEXT,
                    opened TEXT,
                    closed TEXT,
                    pips_gained_lost TEXT,
                    profit_loss TEXT,
                    risk_reward TEXT,
                    strategy_used TEXT,
                    open_day TEXT,
                    open_time TEXT,
                    trade_outcome TEXT,
                    open_month TEXT,
                    trade_duration_minutes REAL,
                    killzone TEXT,
                    time_writing TEXT
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT CHECK(type IN ('Real', 'Paper')) NOT NULL
                );
            """)

            conn.commit()
            conn.close()
            print(f"Database '{DB_NAME}' is ready.")
        except Exception as e:
            print(f"Error setting up database: {e}")

    @staticmethod
    def reset_database():
        """
        Reset the database by clearing all rows in the trades and accounts tables.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            confirm = input(
                "Are you sure you want to delete all accounts & trades from the database? (yes/no): "
            ).lower()
            if confirm == "yes":
                cursor.execute("DELETE FROM trades")
                cursor.execute("DELETE FROM accounts")
                conn.commit()
                print("Database reset was successful.")
            else:
                print("Reset cancelled.")
        except sqlite3.OperationalError as e:
            print(f"Error: {e}")
            DatabaseManager.setup_database()
        except Exception as e:
            print(f"Error resetting the database: {e}")
        finally:
            conn.close()

    @staticmethod
    def create_account(name, account_type):
        """
        Create a new account with a name and type (Real or Paper).
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO accounts (name, type) VALUES (?, ?)", (name, account_type))
            conn.commit()
            conn.close()
            print(f"Account '{name}' ({account_type}) created successfully.")
        except Exception as e:
            print(f"Error creating account: {e}")

    @staticmethod
    def get_next_account_id():
        """
        Get the next account ID (incremental).
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM accounts")
            result = cursor.fetchone()[0]
            conn.close()
            return 1 if result is None else result + 1
        except Exception as e:
            print(f"Error fetching next account ID: {e}")
            return 1

    @staticmethod
    def insert_account():
        print("\nCreate a New Account")
        print("1. Real Account")
        print("2. Paper Account")
        choice = input("Choose account type (1 or 2): ")

        account_type = "Real" if choice == "1" else "Paper" if choice == "2" else None
        if not account_type:
            print("Invalid choice. Please select 1 (Real) or 2 (Paper).")
            return

        account_id = DatabaseManager.get_next_account_id()
        account_name = input(f"Enter a name for the {account_type} account: ")
        full_name = f"{account_name} - {account_type}"  # Combine name with type

        # Save account to database
        DatabaseManager.create_account(full_name, account_type)
        print(f"Account ID: {account_id} | Name: {account_name} | Type: {account_type}")

    @staticmethod
    def view_all():
        """
        Display all accounts along with the count of trades linked to each account.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.id, a.name, a.type, COUNT(t.id) AS trade_count
                FROM accounts a
                LEFT JOIN trades t ON a.id = t.account_id
                GROUP BY a.id, a.name, a.type
                ORDER BY a.id;
            """)
            accounts = cursor.fetchall()
            conn.close()

            if accounts:
                print("\nAccounts:")
                print(f"{'ID':<5} {'Name':<20} {'Type':<10} {'Trade Count':<12}")
                print("-" * 50)
                for account in accounts:
                    print(f"{account[0]:<5} {account[1]:<20} {account[2]:<10} {account[3]:<12}")
            else:
                print("\nNo account found in the database.")
        except Exception as e:
            print(f"Error fetching accounts with trade counts: {e}")

    @staticmethod
    def get_all_accounts():
        """
        Fetch all accounts from the database.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, type FROM accounts")
            accounts = cursor.fetchall()
            conn.close()
            return accounts
        except Exception as e:
            print(f"Error fetching accounts: {e}")
            return []

    @staticmethod
    def insert_trade(trade_entry):
        """
        Insert a TradeEntry object into the database.
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
                trade_entry.account_id,
                trade_entry.filename,
                trade_entry.position_size,
                trade_entry.opened,
                trade_entry.closed,
                trade_entry.pips_gained_lost,
                trade_entry.profit_loss,
                trade_entry.risk_reward,
                trade_entry.strategy_used,
                trade_entry.open_day,
                trade_entry.open_time,
                trade_entry.trade_outcome,
                trade_entry.open_month,
                trade_entry.trade_duration_minutes,
                trade_entry.killzone
            )

            cursor.execute(sql, values)
            conn.commit()
            conn.close()
            print(f"Trade '{trade_entry.filename}' inserted into the database.")
        except sqlite3.IntegrityError:
            print(f"Trade '{trade_entry.filename}' already exists in the database.")
        except Exception as e:
            print(f"Error inserting trade '{trade_entry.filename}': {e}")

    @staticmethod
    def view_all_entries(account_id):
        """
        Fetch all trade entries for a given account ID.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades WHERE account_id = ?", (account_id,))
            entries = cursor.fetchall()
            conn.close()
            return entries
        except Exception as e:
            print(f"Error fetching entries: {e}")
            return []

    @staticmethod
    def delete_entry_by_id(account_id, entry_id):
        """
        Delete an entry by its unique ID for a specific account.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trades WHERE account_id = ? AND id = ?", (account_id, entry_id))
            conn.commit()
            conn.close()
            print(f"Entry with ID '{entry_id}' has been deleted.")
        except Exception as e:
            print(f"Error deleting entry with ID '{entry_id}': {e}")

    @staticmethod
    def delete_account(account_id):
        """
        Delete an account by its ID.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Delete all trades associated with the account
            cursor.execute("DELETE FROM trades WHERE account_id = ?", (account_id,))
            # Delete the account itself
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))

            print(f"Account with ID '{account_id}' has been deleted.")

        except Exception as e:
            print(f"Error deleting entry with ID '{account_id}': {e}")



if __name__ == "__main__":
    run()