import os
import re
from datetime import datetime, timedelta
from pytz import timezone
from data_schema import TradeEntry
from database_utils import DatabaseManager

def parse_general_markdown(file_path):
    """
    Parse a markdown file to extract trade data flexibly and clean the output.
    Args:
    - file_path (str): Path to the markdown file.
    Returns:
    - dict: Parsed and cleaned data with extracted fields.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            template_text = file.read()

        # Define flexible regex patterns for each field
        patterns = {
            'position_size': r'Position\s*Size\s*:?\s*([^\n]+)',
            'opened': r'Opened\s*:?\s*([^\n]+)',
            'closed': r'Closed\s*:?\s*([^\n]+)',
            'pips_gained_lost': r'Pips\s*Gained/Lost\s*:?\s*([^\n]+)',
            'profit_loss': r'Profit/Loss\s*:?\s*([^\n]+)',
            'risk_reward': r'R/R\s*:?\s*([^\n]+)',
            'strategy_used': r'Strategy\s*Used\s*:?\s*([^\n]+)'
        }

        # Extract and clean the fields
        parsed_data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, template_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                value = re.sub(r'[\*\€]', '', value)  # Remove unwanted characters
                parsed_data[key] = value

        # Preserve original time formats for 'opened' and 'closed'
        raw_opened = parsed_data.get('opened', '').strip()
        raw_closed = parsed_data.get('closed', '').strip()
        parsed_data['opened_raw'] = raw_opened
        parsed_data['closed_raw'] = raw_closed

        # Parse and clean the 'opened' and 'closed' fields
        if raw_opened and raw_closed:
            try:
                opened_time = datetime.strptime(raw_opened, "%d/%m/%Y %H:%M")
                closed_time = datetime.strptime(raw_closed, "%d/%m/%Y %H:%M")
                parsed_data['trade_duration_minutes'] = max(0, round((closed_time - opened_time).total_seconds() / 60))
                parsed_data['open_day'] = opened_time.strftime("%A")  # Day of the week
                parsed_data['open_time'] = opened_time.strftime("%H:%M")  # Time only
            except ValueError as e:
                print(f"Error parsing dates in {file_path}: {e}")
                parsed_data['trade_duration_minutes'] = 0  # Default to 0 if parsing fails

        # Determine the killzone
        parsed_data['killzone'] = determine_killzone(raw_opened)

        # Clean and determine the trade outcome
        if 'profit_loss' in parsed_data:
            if parsed_data['profit_loss'] == '#':  # Skip missed trades
                print(f"Skipping missed trade in file: {file_path}")
                return None
            profit_loss_cleaned = re.sub(r'[^\d\.\-\+]', '', parsed_data['profit_loss'])
            try:
                profit_loss_value = float(profit_loss_cleaned)
                parsed_data['profit_loss'] = profit_loss_cleaned
                if profit_loss_value > 0:
                    parsed_data['trade_outcome'] = 'Win'
                elif abs(profit_loss_value) < 0.01:
                    parsed_data['trade_outcome'] = 'Break Even'
                else:
                    parsed_data['trade_outcome'] = 'Loss'
            except ValueError:
                parsed_data['trade_outcome'] = 'Unknown'

        return parsed_data

    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return {}

def determine_killzone(opened_time):
    """
    Determine the killzone for a given opened time.
    """
    try:
        rome_tz = timezone('Europe/Rome')
        ny_tz = timezone('America/New_York')
        opened_time = datetime.strptime(opened_time, "%d/%m/%Y %H:%M").astimezone(ny_tz)
        hour, minute = opened_time.hour, opened_time.minute

        killzones = {
            'London': (2, 5),
            'New York': (7, 10)
        }
        for zone, (start_hour, end_hour) in killzones.items():
            if start_hour <= hour < end_hour or (hour == end_hour and minute <= 15):
                return zone
        return None
    except Exception as e:
        print(f"Error determining killzone: {e}")
        return None


def process_and_store_markdown(directory):
    """
    Process markdown files, parse them, and store them in the database.
    """
    DatabaseManager.setup_database()  # Ensure the database is ready

    for file_name in os.listdir(directory):
        if file_name.endswith('.md'):
            file_path = os.path.join(directory, file_name)
            parsed_data = parse_general_markdown(file_path)

            if parsed_data:
                # Create a TradeEntry instance and store it
                entry = TradeEntry(
                    filename=file_name,
                    position_size=parsed_data.get('position_size'),
                    opened=parsed_data.get('opened'),
                    closed=parsed_data.get('closed'),
                    pips_gained_lost=parsed_data.get('pips_gained_lost'),
                    profit_loss=parsed_data.get('profit_loss'),
                    risk_reward=parsed_data.get('risk_reward'),
                    strategy_used=parsed_data.get('strategy_used'),
                    open_day=parsed_data.get('open_day'),
                    open_time=parsed_data.get('open_time'),
                    trade_outcome=parsed_data.get('trade_outcome'),
                    open_month=parsed_data.get('open_month'),  # Add month
                    trade_duration_minutes=parsed_data.get('trade_duration_minutes'),  # Duration
                    killzone=parsed_data.get('killzone')  # Killzone
                )
                DatabaseManager.insert_trade(entry)


if __name__ == "__main__":
    process_and_store_markdown("trade_logs")
