from flask import Flask, jsonify
import sqlite3, os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the current file
DB_NAME = os.path.join(BASE_DIR, 'data', 'trade_logs.db')

def query_database(query, params=()):
    """
    Helper function to query the database and return results.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


@app.route('/stats/summary', methods=['GET'])
def summary_stats():
    """
    Endpoint to provide summary statistics including break-even trades.
    """
    # Total trades, wins, losses, break-even, and unknowns
    query = """
    SELECT 
        COUNT(*) AS total_trades,
        SUM(CASE WHEN trade_outcome = 'Win' THEN 1 ELSE 0 END) AS total_wins,
        SUM(CASE WHEN trade_outcome = 'Loss' THEN 1 ELSE 0 END) AS total_losses,
        SUM(CASE WHEN trade_outcome = 'Break Even' THEN 1 ELSE 0 END) AS total_break_even,
        SUM(CASE WHEN trade_outcome = 'Unknown' THEN 1 ELSE 0 END) AS total_unknowns
    FROM trades
    """
    # Execute the query and fetch the results
    stats = query_database(query)[0]

    # Return the response with the new break-even metric
    return jsonify({
        'total_trades': stats[0],
        'total_wins': stats[1],
        'total_losses': stats[2],
        'total_break_even': stats[3],
        'total_unknowns': stats[4]
    })

@app.route('/stats/pnl', methods=['GET'])
def pnl_stats():
    """
    Endpoint to provide profit and loss stats over time.
    """
    query = "SELECT opened, profit_loss FROM trades WHERE profit_loss != '#' ORDER BY datetime(substr(opened, 7, 4) || '-' || substr(opened, 4, 2) || '-' || substr(opened, 1, 2))"
    rows = query_database(query)
    pnl = []
    cumulative_pnl = 0.0

    for row in rows:
        try:
            profit_loss = float(row[1])
            cumulative_pnl += profit_loss
            pnl.append({
                'date': row[0],
                'profit_loss': profit_loss,
                'cumulative_pnl': cumulative_pnl
            })
        except ValueError:
            continue

    return jsonify(pnl)

@app.route('/stats/rr', methods=['GET'])
def rr_stats():
    """
    Endpoint to provide risk/reward ratio distribution.
    """
    query = "SELECT risk_reward FROM trades WHERE risk_reward != ''"
    rows = query_database(query)
    rr_distribution = []

    for row in rows:
        try:
            rr_value = float(row[0].split('->')[0].strip())  # Handles multi-value RRs
            rr_distribution.append(rr_value)
        except ValueError:
            continue

    return jsonify(rr_distribution)

@app.route('/stats/duration_heatmap', methods=['GET'])
def duration_heatmap():
    """
    Endpoint to provide trade outcomes and durations for heatmap generation.
    """
    query = """
    SELECT
        trade_outcome,
        trade_duration_minutes
    FROM trades
    WHERE trade_duration_minutes IS NOT NULL AND trade_outcome IN ('Win', 'Loss', 'Break Even')
    """
    rows = query_database(query)

    # Prepare the data for the response
    duration_data = []
    for row in rows:
        outcome, duration = row
        duration_data.append({
            "outcome": outcome,
            "duration": duration
        })

    return jsonify(duration_data)


@app.route('/stats/monthly', methods=['GET'])
def monthly_performance():
    query = """
    SELECT 
        open_month,
        SUM(CAST(profit_loss AS FLOAT)) AS total_profit
    FROM trades
    WHERE profit_loss != '#'
    GROUP BY open_month
    ORDER BY datetime(substr(open_month, 4, 4) || '-' || substr(open_month, 1, 2) || '-01')
    """
    rows = query_database(query)
    monthly_profit = {row[0]: row[1] for row in rows}
    return jsonify(monthly_profit)

@app.route('/stats/daily', methods=['GET'])
def daily_performance():
    # Use the same query as the debug function
    query = """
    SELECT 
        open_day,
        trade_outcome
    FROM trades
    """

    # Execute the query
    rows = query_database(query)

    # Initialize a dictionary with all days of the week
    performance = {
        "Monday": {"wins": 0, "losses": 0, "break_even": 0},
        "Tuesday": {"wins": 0, "losses": 0, "break_even": 0},
        "Wednesday": {"wins": 0, "losses": 0, "break_even": 0},
        "Thursday": {"wins": 0, "losses": 0, "break_even": 0},
        "Friday": {"wins": 0, "losses": 0, "break_even": 0},
        "Saturday": {"wins": 0, "losses": 0, "break_even": 0},
        "Sunday": {"wins": 0, "losses": 0, "break_even": 0},
    }

    # Populate the dictionary by counting trade outcomes
    for row in rows:
        day, trade_outcome = row  # Extract day and trade outcome
        if day in performance:  # Ensure valid day
            if trade_outcome == "Win":
                performance[day]["wins"] += 1
            elif trade_outcome == "Loss":
                performance[day]["losses"] += 1
            elif trade_outcome == "Break Even":
                performance[day]["break_even"] += 1

    # Return the aggregated data as JSON
    return jsonify(performance)

@app.route('/stats/daily_debug', methods=['GET'])
def daily_performance_debug():
    """
    Endpoint to provide performance grouped by day of the week with detailed file-level debug info.
    """
    query = """
    SELECT 
        open_day,
        filename,
        trade_outcome
    FROM trades
    """

    # Execute the query
    rows = query_database(query)

    # Initialize a dictionary to include file-level information
    daily_performance_debug = {
        "Monday": {"wins": [], "losses": [], "break_even": []},
        "Tuesday": {"wins": [], "losses": [], "break_even": []},
        "Wednesday": {"wins": [], "losses": [], "break_even": []},
        "Thursday": {"wins": [], "losses": [], "break_even": []},
        "Friday": {"wins": [], "losses": [], "break_even": []},
        "Saturday": {"wins": [], "losses": [], "break_even": []},
        "Sunday": {"wins": [], "losses": [], "break_even": []},
    }

    # Populate the dictionary with actual data from the query
    for row in rows:
        day, filename, trade_outcome = row
        if day in daily_performance_debug:  # Ensure only valid days are updated
            if trade_outcome == "Win":
                daily_performance_debug[day]["wins"].append(filename)
            elif trade_outcome == "Loss":
                daily_performance_debug[day]["losses"].append(filename)
            elif trade_outcome == "Break Even":
                daily_performance_debug[day]["break_even"].append(filename)

    # Print detailed debug output for each day
    for day, outcomes in daily_performance_debug.items():
        print(f"{day}: Wins - {outcomes['wins']}, Losses - {outcomes['losses']}, Break Even - {outcomes['break_even']}")

    # Return the detailed data as JSON for analysis
    return jsonify(daily_performance_debug)


@app.route('/stats/profit_by_day', methods=['GET'])
def profit_by_day():
    query = """
    SELECT 
        open_day,
        SUM(CAST(profit_loss AS FLOAT)) AS total_profit
    FROM trades
    WHERE profit_loss != '#'
    GROUP BY open_day
    ORDER BY CASE
        WHEN open_day = 'Monday' THEN 1
        WHEN open_day = 'Tuesday' THEN 2
        WHEN open_day = 'Wednesday' THEN 3
        WHEN open_day = 'Thursday' THEN 4
        WHEN open_day = 'Friday' THEN 5
        ELSE 6
    END
    """
    rows = query_database(query)
    profit_by_day = {row[0]: row[1] for row in rows}
    return jsonify(profit_by_day)

@app.route('/stats/killzone_outcomes', methods=['GET'])
def performance_killzone_outcomes():
    """
    Endpoint to provide trade outcomes (Wins, Losses, Break-even) grouped by killzone.
    """
    query = """
    SELECT 
        killzone,
        trade_outcome,
        COUNT(*) AS trade_count
    FROM trades
    WHERE profit_loss != '#' AND killzone IS NOT NULL
    GROUP BY killzone, trade_outcome
    ORDER BY killzone, trade_outcome
    """
    rows = query_database(query)

    # Initialize a dictionary to store outcomes by killzone
    performance = {}

    for row in rows:
        killzone, outcome, count = row

        # Skip "Unknown" killzones if present
        if killzone == "Unknown" or outcome == "Unknown":
            continue

        if killzone not in performance:
            performance[killzone] = {"wins": 0, "losses": 0, "break_even": 0}

        if outcome == "Win":
            performance[killzone]["wins"] += count
        elif outcome == "Loss":
            performance[killzone]["losses"] += count
        elif outcome == "Break Even":
            performance[killzone]["break_even"] += count

    return jsonify(performance)

@app.route('/stats/killzone', methods=['GET'])
def performance_killzone():
    query = """
    SELECT
        killzone,
        open_day,
        COUNT(*) AS trade_count
    FROM trades
    WHERE profit_loss != '#' AND killzone IS NOT NULL AND open_day IS NOT NULL
    GROUP BY killzone, open_day
    ORDER BY killzone, open_day;
    """
    rows = query_database(query)

    # Initialize a nested dictionary to organize the data
    performance = {}

    for row in rows:
        try:
            # Extract query results
            killzone, day, count = row

            # Skip any entries with "Unknown" values
            if not killzone or not day or killzone == "Unknown" or day == "Unknown":
                continue

            # Initialize nested dictionary for killzone if not present
            if killzone not in performance:
                performance[killzone] = {}

            # Assign the trade count for the specific day
            performance[killzone][day] = count
        except Exception as e:
            print(f"Error processing row {row}: {e}")

    # Return the data as JSON
    return jsonify(performance)


@app.route('/stats/reward_ratios', methods=['GET'])
def reward_ratios():
    """
    Endpoint to provide reward ratios grouped by trade outcome.
    """
    query = """
    SELECT 
        trade_outcome,
        CAST(risk_reward AS FLOAT) AS reward_ratio
    FROM trades
    WHERE risk_reward != '' AND risk_reward IS NOT NULL
    """
    rows = query_database(query)

    # Prepare data for the response
    reward_ratios = []
    for row in rows:
        trade_outcome, reward_ratio = row
        reward_ratios.append({
            "outcome": trade_outcome,
            "reward_ratio": reward_ratio
        })

    return jsonify(reward_ratios)

@app.route('/stats/average_trade_duration', methods=['GET'])
def average_trade_duration():
    query = """
    SELECT 
        trade_outcome,
        AVG(trade_duration_minutes) AS avg_duration
    FROM trades
    WHERE trade_duration_minutes IS NOT NULL
    GROUP BY trade_outcome
    """
    rows = query_database(query)
    avg_duration = {row[0]: row[1] for row in rows}
    return jsonify(avg_duration)

@app.route('/stats/strategy_success', methods=['GET'])
def strategy_success():
    query = """
    SELECT 
        strategy_used,
        COUNT(*) AS total_trades,
        SUM(CASE WHEN trade_outcome = 'Win' THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN trade_outcome = 'Loss' THEN 1 ELSE 0 END) AS losses
    FROM trades
    GROUP BY strategy_used
    """
    rows = query_database(query)
    strategy_stats = {
        row[0]: {
            'total_trades': row[1],
            'wins': row[2],
            'losses': row[3],
            'win_rate': round((row[2] / row[1]) * 100, 2) if row[1] > 0 else 0
        }
        for row in rows
    }
    return jsonify(strategy_stats)

@app.route('/stats/best_worst_trade', methods=['GET'])
def best_worst_trade():
    # Query for the top 5 best trades
    best_trades_query = """
    SELECT 
        filename,
        opened,
        closed,
        profit_loss
    FROM trades
    WHERE profit_loss != '#'
    ORDER BY CAST(profit_loss AS FLOAT) DESC
    LIMIT 5
    """
    best_trades = query_database(best_trades_query)

    # Query for the top 5 worst trades
    worst_trades_query = """
    SELECT 
        filename,
        opened,
        closed,
        profit_loss
    FROM trades
    WHERE profit_loss != '#'
    ORDER BY CAST(profit_loss AS FLOAT) ASC
    LIMIT 5
    """
    worst_trades = query_database(worst_trades_query)

    # Transform the results into JSON-friendly format
    best_trades_list = [
        {
            'filename': trade[0],
            'opened': trade[1],
            'closed': trade[2],
            'profit_loss': trade[3]
        }
        for trade in best_trades
    ]

    worst_trades_list = [
        {
            'filename': trade[0],
            'opened': trade[1],
            'closed': trade[2],
            'profit_loss': trade[3]
        }
        for trade in worst_trades
    ]

    return jsonify({
        'best_trades': best_trades_list,
        'worst_trades': worst_trades_list
    })

if __name__ == '__main__':
    app.run()
