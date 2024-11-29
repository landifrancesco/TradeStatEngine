import sqlite3
import os

# Define the database name with an absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the current file
DB_NAME = os.path.join(BASE_DIR, 'data', 'trade_logs.db')

class DatabaseManager:
    """
    Utility class for interacting with the trade_logs database.
    """

    @staticmethod
    def setup_database():
        """
        Create the database and table if they don't exist.
        """
        if os.path.exists(DB_NAME):
            print(f"Database '{DB_NAME}' already exists. Setup skipped.")
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    trade_outcome TEXT
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

            # Confirm reset action
            confirm = input(
                "Are you sure you want to reset the database? This will delete all rows but keep the schema. (yes/no): ").lower()
            if confirm == "yes":
                cursor.execute("DELETE FROM trades")  # Clears the table but keeps schema
                conn.commit()
                print("All rows in the 'trades' table have been cleared.")
            else:
                print("Reset cancelled.")
        except sqlite3.OperationalError as e:
            print(f"No existing 'trades' table to reset. Error: {e}")
            DatabaseManager.setup_database()  # Ensure the schema is recreated
        except Exception as e:
            print(f"Error resetting the database: {e}")
        finally:
            conn.close()

    @staticmethod
    def setup_database():
        """
        Create the database and table if they don't exist.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    open_month TEXT,  -- Add month column
                    trade_duration_minutes REAL,  -- Add duration column
                    killzone TEXT  -- Add Killzone column
                )
            """)
            conn.commit()
            conn.close()
            print(f"Database '{DB_NAME}' is ready.")
        except Exception as e:
            print(f"Error setting up database: {e}")

    @staticmethod
    def insert_trade(trade_entry):
        """
        Insert a TradeEntry object into the database.
        Args:
        - trade_entry (TradeEntry): The trade entry to insert.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Prepare the SQL statement and values
            sql = """
                INSERT INTO trades (
                    filename, position_size, opened, closed, pips_gained_lost,
                    profit_loss, risk_reward, strategy_used, open_day,
                    open_time, trade_outcome, open_month,
                    trade_duration_minutes, killzone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
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
    def delete_entry_by_id(entry_id):
        """
        Delete an entry by its unique ID.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trades WHERE id = ?", (entry_id,))
            conn.commit()
            conn.close()
            print(f"Entry with ID '{entry_id}' has been deleted.")
        except Exception as e:
            print(f"Error deleting entry with ID '{entry_id}': {e}")

    @staticmethod
    def view_all_entries(order_by_date=True):
        """
        Retrieve all entries from the database, optionally ordered by the 'opened' date.

        Args:
            order_by_date (bool): If True, sorts entries by the 'opened' field in ascending order.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            if order_by_date:
                cursor.execute(
                    "SELECT * FROM trades ORDER BY datetime(substr(opened, 7, 4) || '-' || substr(opened, 4, 2) || '-' || substr(opened, 1, 2) || 'T' || substr(opened, 12))")
            else:
                cursor.execute("SELECT * FROM trades")

            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"Error retrieving entries: {e}")
            return []



    @staticmethod
    def delete_entry(filename):
        """
        Delete an entry by filename.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trades WHERE filename = ?", (filename,))
            conn.commit()
            conn.close()
            print(f"Entry for '{filename}' has been deleted.")
        except Exception as e:
            print(f"Error deleting entry '{filename}': {e}")

if __name__ == "__main__":
    while True:
        print("\nDatabase Utility:")
        print("1. Setup Database")
        print("2. Reset Database")
        print("3. View All Entries")
        print("4. Delete Entry by ID")
        print("5. Exit")

        choice = input("\nEnter your choice: ")

        if choice == "1":
            DatabaseManager.setup_database()
        elif choice == "2":
            confirm = input("Are you sure you want to reset the database? This will delete all data! (yes/no): ")
            if confirm.lower() == "yes":
                DatabaseManager.reset_database()
        elif choice == "3":
            entries = DatabaseManager.view_all_entries()
            if entries:
                print("\nAll Entries:")
                for entry in entries:
                    print(entry)  # Display all columns (ID, filename, etc.)
            else:
                print("\nNo entries found in the database.")
        elif choice == "4":
            # First, display all entries
            entries = DatabaseManager.view_all_entries()
            if entries:
                print("\nAll Entries:")
                for entry in entries:
                    print(entry)  # Display all columns (ID, filename, etc.)
                # Allow user to input IDs for deletion
                ids_to_delete = input("\nEnter the IDs to delete (comma-separated): ").strip()
                if ids_to_delete:
                    try:
                        # Split IDs by commas, strip spaces, and convert to integers
                        ids = [int(id.strip()) for id in ids_to_delete.split(",")]
                        for entry_id in ids:
                            DatabaseManager.delete_entry_by_id(entry_id)
                    except ValueError:
                        print("Invalid input. Please enter numeric IDs separated by commas.")
                else:
                    print("No IDs entered. Deletion cancelled.")
            else:
                print("\nNo entries found in the database.")
        elif choice == "5":
            print("Exiting the utility. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
