from datetime import datetime
from flask import Flask, jsonify, request
import sqlite3
import os
import sys

# Redirect stdout and stderr to null (no output)
# sys.stdout = open(os.devnull, 'w')
# sys.stderr = open(os.devnull, 'w')


app = Flask(__name__)

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_NAME = os.path.join(DATA_DIR, "trades.db")


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

@app.route('/stats/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint.
    """
    return jsonify({"status": "OK"})

@app.route('/accounts', methods=['GET'])
def get_accounts():
    """
    Endpoint to retrieve all account IDs and names.
    """
    query = "SELECT id, name FROM accounts"
    rows = query_database(query)
    accounts = [{"id": row[0], "name": row[1]} for row in rows]
    return jsonify(accounts)


@app.route('/stats/summary', methods=['GET'])
def summary_stats():
    """
    Endpoint to provide summary statistics including break-even trades, filtered by account_id.
    """
    account_id = request.args.get('account_id',1)
    query = """
    SELECT 
        COUNT(*) AS total_trades,
        SUM(CASE WHEN trade_outcome = 'Win' THEN 1 ELSE 0 END) AS total_wins,
        SUM(CASE WHEN trade_outcome = 'Loss' THEN 1 ELSE 0 END) AS total_losses,
        SUM(CASE WHEN trade_outcome = 'Break-even' THEN 1 ELSE 0 END) AS total_break_even,
        SUM(CASE WHEN trade_outcome = 'Unknown' THEN 1 ELSE 0 END) AS total_unknowns
    FROM trades WHERE account_id = ?
    """
    stats = query_database(query, params=(account_id,))[0]
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
    Endpoint to provide profit and loss stats over time, filtered by account_id.
    """
    account_id = request.args.get('account_id',1)
    query = """
    SELECT opened, profit_loss FROM trades 
    WHERE profit_loss != '#' AND account_id = ?
    ORDER BY datetime(substr(opened, 7, 4) || '-' || substr(opened, 4, 2) || '-' || substr(opened, 1, 2))
    """
    rows = query_database(query, params=(account_id,))
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

@app.route('/stats/duration_heatmap', methods=['GET'])
def duration_heatmap():
    """
    Endpoint to provide trade outcomes and durations for heatmap generation.
    """
    account_id = request.args.get('account_id',1)
    query = """
    SELECT
        trade_outcome,
        trade_duration_minutes
    FROM trades
    WHERE trade_duration_minutes IS NOT NULL AND trade_outcome IN ('Win', 'Loss', 'Break-Even') AND account_id = ?
    """
    rows = query_database(query, params=(account_id,))
    duration_data = [{"outcome": row[0], "duration": row[1]} for row in rows]
    return jsonify(duration_data)


@app.route('/stats/monthly', methods=['GET'])
def monthly_performance():
    account_id = request.args.get('account_id')
    time_writing_mode = request.args.get('time_writing_toggle', 'false').lower() == 'true'

    query = """
        SELECT time_writing, opened, profit_loss
        FROM trades
        WHERE account_id = ?
    """
    rows = query_database(query, (account_id,))

    monthly_data = {}

    for time_writing, opened, profit_loss in rows:
        try:
            if time_writing_mode and time_writing:
                time_obj = datetime.strptime(time_writing.strip(), "%H:%M %d/%m/%Y")
                month_key = time_obj.strftime("%Y-%m")
            elif opened:
                time_obj = datetime.strptime(opened.strip(), "%d/%m/%Y %H:%M")
                month_key = time_obj.strftime("%Y-%m")
            else:
                continue

            profit_loss_value = float(profit_loss) if profit_loss else 0.0
            monthly_data[month_key] = monthly_data.get(month_key, 0.0) + profit_loss_value

        except ValueError as e:
            continue

    return jsonify(monthly_data)



@app.route('/stats/daily', methods=['GET'])
def daily_performance():
    """
    Endpoint to provide daily performance stats, filtered by account_id.
    """
    account_id = request.args.get('account_id',1)
    query = """
    SELECT 
        open_day,
        trade_outcome
    FROM trades
    WHERE account_id = ?
    """
    rows = query_database(query, params=(account_id,))
    performance = {
        "Monday": {"wins": 0, "losses": 0, "break_even": 0},
        "Tuesday": {"wins": 0, "losses": 0, "break_even": 0},
        "Wednesday": {"wins": 0, "losses": 0, "break_even": 0},
        "Thursday": {"wins": 0, "losses": 0, "break_even": 0},
        "Friday": {"wins": 0, "losses": 0, "break_even": 0},
        "Saturday": {"wins": 0, "losses": 0, "break_even": 0},
        "Sunday": {"wins": 0, "losses": 0, "break_even": 0},
    }
    for row in rows:
        day, trade_outcome = row
        if day in performance:
            if trade_outcome == "Win":
                performance[day]["wins"] += 1
            elif trade_outcome == "Loss":
                performance[day]["losses"] += 1
            elif trade_outcome == "Break-even":
                performance[day]["break_even"] += 1
    return jsonify(performance)

@app.route('/stats/killzone', methods=['GET'])
def performance_killzone():
    """
    Endpoint to provide killzone data grouped by day, filtered by account_id.
    """
    account_id = request.args.get('account_id',1)

    query = """
    SELECT
        killzone,
        open_day,
        COUNT(*) AS trade_count
    FROM trades
    WHERE profit_loss != '#' AND killzone IS NOT NULL AND open_day IS NOT NULL AND account_id = ?
    GROUP BY killzone, open_day
    ORDER BY killzone, open_day
    """
    rows = query_database(query, params=(account_id,))

    performance = {}
    for row in rows:
        killzone, day, count = row
        if killzone not in performance:
            performance[killzone] = {}
        performance[killzone][day] = count

    return jsonify(performance)


@app.route('/stats/killzone_outcomes', methods=['GET'])
def performance_killzone_outcomes():
    """
    Endpoint to provide trade outcomes grouped by killzone, filtered by account_id.
    """
    account_id = request.args.get('account_id',1)
    query = """
    SELECT 
        killzone,
        trade_outcome,
        COUNT(*) AS trade_count
    FROM trades
    WHERE profit_loss != '#' AND killzone IS NOT NULL AND account_id = ?
    GROUP BY killzone, trade_outcome
    ORDER BY killzone, trade_outcome
    """
    rows = query_database(query, params=(account_id,))
    performance = {}
    for row in rows:
        killzone, outcome, count = row
        if killzone not in performance:
            performance[killzone] = {"wins": 0, "losses": 0, "break_even": 0}
        if outcome == "Win":
            performance[killzone]["wins"] += count
        elif outcome == "Loss":
            performance[killzone]["losses"] += count
        elif outcome == "Break-even":
            performance[killzone]["break_even"] += count
    return jsonify(performance)

@app.route('/stats/best_worst_trade', methods=['GET'])
def best_worst_trade():
    """
    Endpoint to fetch the top 5 best and worst trades, filtered by account_id.
    """
    account_id = request.args.get('account_id',1)
    best_query = """
    SELECT filename, opened, closed, profit_loss
    FROM trades
    WHERE profit_loss != '#' AND account_id = ?
    ORDER BY CAST(profit_loss AS FLOAT) DESC
    LIMIT 5
    """
    worst_query = """
    SELECT filename, opened, closed, profit_loss
    FROM trades
    WHERE profit_loss != '#' AND account_id = ?
    ORDER BY CAST(profit_loss AS FLOAT) ASC
    LIMIT 5
    """
    best_trades = query_database(best_query, params=(account_id,))
    worst_trades = query_database(worst_query, params=(account_id,))
    best_trades_list = [{'filename': row[0], 'opened': row[1], 'closed': row[2], 'profit_loss': row[3]} for row in best_trades]
    worst_trades_list = [{'filename': row[0], 'opened': row[1], 'closed': row[2], 'profit_loss': row[3]} for row in worst_trades]
    return jsonify({
        'best_trades': best_trades_list,
        'worst_trades': worst_trades_list
    })

@app.route('/stats/reward_ratios', methods=['GET'])
def reward_ratios():
    """
    Endpoint to provide reward ratios grouped by trade outcome, filtered by account_id.
    """
    account_id = request.args.get('account_id',1)
    query = """
    SELECT 
        trade_outcome,
        CAST(risk_reward AS FLOAT) AS reward_ratio
    FROM trades
    WHERE risk_reward != '' AND risk_reward IS NOT NULL AND account_id = ?
    """
    rows = query_database(query, params=(account_id,))
    reward_ratios = [{"outcome": row[0], "reward_ratio": row[1]} for row in rows]
    return jsonify(reward_ratios)

@app.route('/stats/average_trade_duration', methods=['GET'])
def average_trade_duration():
    """
    Endpoint to provide average trade duration by outcome, filtered by account_id.
    """
    account_id = request.args.get('account_id',1)
    query = """
    SELECT 
        trade_outcome,
        AVG(trade_duration_minutes) AS avg_duration
    FROM trades
    WHERE trade_duration_minutes IS NOT NULL AND account_id = ?
    GROUP BY trade_outcome
    """
    rows = query_database(query, params=(account_id,))
    avg_duration = {row[0]: row[1] for row in rows}
    return jsonify(avg_duration)

@app.route('/stats/strategy_success', methods=['GET'])
def strategy_success():
    """
    Endpoint to provide success rate for each strategy, filtered by account_id.
    """
    account_id = request.args.get('account_id',1)
    query = """
    SELECT 
        strategy_used,
        COUNT(*) AS total_trades,
        SUM(CASE WHEN trade_outcome = 'Win' THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN trade_outcome = 'Loss' THEN 1 ELSE 0 END) AS losses
    FROM trades
    WHERE account_id = ?
    GROUP BY strategy_used
    """
    rows = query_database(query, params=(account_id,))
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
