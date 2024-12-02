import sqlite3
import os

# Define the base directory for the app
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))  # Moves one level up to 'app'

# Define the path to the data directory and the database file
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_NAME = os.path.join(DATA_DIR, "trades.db")

class DatabaseManager:
    """
    Utility class for interacting with the backups database.
    """

    @staticmethod
    def setup_database():
        """
        Create the database and table if they don't exist.
        """
        try:
            # Ensure the 'data' directory exists
            data_dir = os.path.join(BASE_DIR, 'data')
            os.makedirs(data_dir, exist_ok=True)

            # Debugging: Print the resolved database path
            print(f"Resolved database path: {DB_NAME}")

            # Connect to the database and create tables
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Create trades table
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
                    killzone TEXT
                )
            """)

            # Create accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT
                )
            """)

            conn.commit()
            conn.close()
            print(f"Database '{DB_NAME}' is ready.")
        except Exception as e:
            print(f"Error setting up database: {e}")

    @staticmethod
    def reset_database():
        """
        Reset the database by clearing all rows in the trades table.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            confirm = input(
                "Are you sure you want to reset the database? This will delete all rows but keep the schema. (yes/no): ").lower()
            if confirm == "yes":
                cursor.execute("DELETE FROM trades")
                cursor.execute("DELETE FROM accounts")
                conn.commit()
                print("All rows in the 'trades' and 'accounts' tables have been cleared.")
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
                trade_entry.account_id,  # Include account_id
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
    def insert_account(account_id, name, description):
        """
        Insert a new account into the database.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            sql = "INSERT INTO accounts (id, name, description) VALUES (?, ?, ?)"
            values = (account_id, name, description)

            cursor.execute(sql, values)
            conn.commit()
            conn.close()
            print(f"Account '{name}' inserted into the database.")
        except sqlite3.IntegrityError:
            print(f"Account '{name}' already exists in the database.")
        except Exception as e:
            print(f"Error inserting account '{name}': {e}")

    @staticmethod
    def view_all_entries(account_id, order_by_date=True):
        """
        Retrieve all entries for a specific account.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            if order_by_date:
                query = """
                    SELECT * FROM trades
                    WHERE account_id = ?
                    ORDER BY datetime(substr(opened, 7, 4) || '-' || substr(opened, 4, 2) || '-' || substr(opened, 1, 2) || 'T' || substr(opened, 12))
                """
            else:
                query = "SELECT * FROM trades WHERE account_id = ?"

            cursor.execute(query, (account_id,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"Error retrieving entries: {e}")
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


if __name__ == "__main__":
    while True:
        print("\nDatabase Utility:")
        print("1. Setup Database")
        print("2. Reset Database")
        print("3. View All Entries for Account")
        print("4. Delete Entry by ID")
        print("5. Add Account")
        print("6. Exit")

        choice = input("\nEnter your choice: ")

        if choice == "1":
            DatabaseManager.setup_database()
        elif choice == "2":
            confirm = input("Are you sure you want to reset the database? (yes/no): ")
            if confirm.lower() == "yes":
                DatabaseManager.reset_database()
        elif choice == "3":
            account_id = input("Enter the account ID: ")
            entries = DatabaseManager.view_all_entries(account_id)
            if entries:
                print("\nEntries for Account:")
                for entry in entries:
                    print(entry)
            else:
                print("\nNo entries found for this account.")
        elif choice == "4":
            account_id = input("Enter the account ID: ")
            entry_id = input("Enter the entry ID to delete: ")
            DatabaseManager.delete_entry_by_id(account_id, int(entry_id))
        elif choice == "5":
            account_id = input("Enter the account ID: ")
            name = input("Enter the account name: ")
            description = input("Enter a description: ")
            DatabaseManager.insert_account(account_id, name, description)
        elif choice == "6":
            print("Exiting the utility. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
