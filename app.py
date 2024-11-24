from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

DB_NAME = 'trade_logs.db'

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
    Endpoint to provide summary statistics.
    """
    # Total trades, wins, losses, unknowns
    query = """
    SELECT 
        COUNT(*) AS total_trades,
        SUM(CASE WHEN trade_outcome = 'Win' THEN 1 ELSE 0 END) AS total_wins,
        SUM(CASE WHEN trade_outcome = 'Loss' THEN 1 ELSE 0 END) AS total_losses,
        SUM(CASE WHEN trade_outcome = 'Unknown' THEN 1 ELSE 0 END) AS total_unknowns
    FROM trades
    """
    stats = query_database(query)[0]
    return jsonify({
        'total_trades': stats[0],
        'total_wins': stats[1],
        'total_losses': stats[2],
        'total_unknowns': stats[3]
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

@app.route('/stats/rr_by_outcome', methods=['GET'])
def rr_by_outcome():
    """
    Endpoint to provide risk/reward ratio distribution by outcome (Win/Loss).
    """
    query = "SELECT risk_reward, trade_outcome FROM trades WHERE risk_reward != ''"
    rows = query_database(query)

    rr_data = {'Win': [], 'Loss': []}
    for row in rows:
        try:
            rr_value = float(row[0].split('->')[0].strip())  # Handles multi-value RRs
            if row[1] == 'Win':
                rr_data['Win'].append(rr_value)
            elif row[1] == 'Loss':
                rr_data['Loss'].append(rr_value)
        except ValueError:
            continue

    return jsonify(rr_data)


@app.route('/stats/daily', methods=['GET'])
def daily_performance():
    """
    Endpoint to provide performance grouped by day of the week.
    """
    query = """
    SELECT 
        open_day,
        SUM(CASE WHEN trade_outcome = 'Win' THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN trade_outcome = 'Loss' THEN 1 ELSE 0 END) AS losses,
        SUM(CASE WHEN trade_outcome = 'Unknown' THEN 1 ELSE 0 END) AS unknowns
    FROM trades
    GROUP BY open_day
    """
    rows = query_database(query)
    daily_performance = {row[0]: {'wins': row[1], 'losses': row[2], 'unknowns': row[3]} for row in rows}

    return jsonify(daily_performance)

if __name__ == '__main__':
    app.run()
