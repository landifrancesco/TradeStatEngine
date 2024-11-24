import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import requests
import pandas as pd
import plotly.express as px

# Detect system theme dynamically
import json
import dash.dash_table

# Initialize Dash app with a dynamic theme
external_stylesheets = [dbc.themes.DARKLY]  # Default to dark theme
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, title="Trading Dashboard")
server = app.server

# Fetch data from Flask API
def fetch_data(endpoint):
    try:
        response = requests.get(f"http://127.0.0.1:5000{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return {}

# Fetch stats from Flask API
summary = fetch_data('/stats/summary') or {}
pnl_data = fetch_data('/stats/pnl') or []
daily_performance = fetch_data('/stats/daily') or {}
rr_distribution = fetch_data('/stats/rr') or []
monthly_performance = fetch_data('/stats/monthly') or {}

# Handle missing or empty data
total_pnl = sum([float(entry.get('profit_loss', 0)) for entry in pnl_data]) if pnl_data else 0
win_rate = summary.get('total_wins', 0) / max(summary.get('total_trades', 1), 1) * 100
risk_reward = 1.72  # Placeholder if not available

# Safely calculate best_day and most_trades_day
if daily_performance:
    best_day = max(daily_performance.items(), key=lambda x: x[1].get("Wins", 0))[0]
    most_trades_day = max(daily_performance.items(), key=lambda x: sum(x[1].values()))[0]
else:
    best_day = "None"
    most_trades_day = "None"

# Convert daily performance data into DataFrame
daily_performance_df = pd.DataFrame.from_dict(daily_performance, orient='index').reset_index()
daily_performance_df.columns = ['Day', 'Wins', 'Losses', 'Unknowns']

# Convert monthly performance data into DataFrame
monthly_performance_df = pd.DataFrame(monthly_performance.items(), columns=["Month", "PNL"])

# Ensure graphs render even if data is missing
if pnl_data:
    pnl_df = pd.DataFrame(pnl_data)
    equity_curve_fig = px.line(
        pnl_df, x='date', y='cumulative_pnl',
        title="Equity Curve",
        labels={"date": "Date", "cumulative_pnl": "Cumulative P/L (€)"},
        template="plotly_dark"
    )
else:
    equity_curve_fig = px.line(
        title="Equity Curve",
        template="plotly_dark"
    )

if not daily_performance_df.empty:
    daily_performance_fig = px.bar(
        daily_performance_df, x='Day', y=['Wins', 'Losses', 'Unknowns'],
        title="Daily Performance",
        labels={"value": "Count", "Day": "Day of the Week"},
        template="plotly_dark"
    )
else:
    daily_performance_fig = px.bar(
        title="Daily Performance",
        template="plotly_dark"
    )

if rr_distribution:
    rr_fig = px.histogram(
        rr_distribution,
        title="Risk/Reward Distribution",
        labels={"value": "Risk/Reward Ratio", "count": "Frequency"},
        nbins=20,
        template="plotly_dark"
    )
    rr_fig.update_layout(showlegend=False)  # Remove legend
else:
    rr_fig = px.histogram(
        title="Risk/Reward Distribution",
        template="plotly_dark"
    )

if not monthly_performance_df.empty:
    monthly_performance_fig = px.bar(
        monthly_performance_df, x="Month", y="PNL",
        title="Monthly Performance",
        labels={"Month": "Month", "PNL": "Net Gains (€)"},
        color="PNL",
        color_continuous_scale=["red", "green"],
        template="plotly_dark"
    )
else:
    monthly_performance_fig = px.bar(
        title="Monthly Performance",
        template="plotly_dark"
    )

# Configure toolbar for graphs (only download button enabled)
config = {"displayModeBar": True, "modeBarButtonsToRemove": ["zoom", "pan", "resetScale2d", "autoScale2d"]}

# Custom CSS for tab styling
custom_css = """
<style>
/* Active Tab */
.tab--selected {
    background-color: #4CAF50 !important;
    color: white !important;
}

/* Inactive Tabs */
.tab {
    background-color: #222 !important;
    color: #fff !important;
}

/* Tab Hover */
.tab:hover {
    background-color: #333 !important;
    color: #fff !important;
}
</style>
"""

# App layout
app.layout = html.Div([
    html.Div(dcc.Markdown(custom_css)),  # Add custom CSS
    dcc.Tabs([
        # General Stats Tab
        dcc.Tab(label="General Stats", className="tab", selected_className="tab--selected", children=[
            dbc.Row([
                dbc.Col(html.H2("Trading Dashboard", style={"textAlign": "center"}), width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(html.Div([
                    html.H3("Total PnL", className="text-center"),
                    html.H1(f"€{total_pnl:.2f}", className="text-center",
                            style={"color": "green" if total_pnl > 0 else "red"})
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Win Rate", className="text-center"),
                    html.H1(f"{win_rate:.2f}%", className="text-warning text-center")
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Risk/Reward", className="text-center"),
                    html.H1(f"{risk_reward:.2f}", className="text-primary text-center")
                ]), width=4)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dcc.Graph(figure=equity_curve_fig, config=config), width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dcc.Graph(figure=monthly_performance_fig, config=config), width=6),
                dbc.Col(dcc.Graph(figure=daily_performance_fig, config=config), width=6)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dcc.Graph(figure=rr_fig, config=config), width=6)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(html.Div([
                    html.P(f"Best Day: {best_day}", className="text-center"),
                    html.P(f"Most Trades Day: {most_trades_day}", className="text-center")
                ]), width=12)
            ])
        ]),

        # Strategy Stats Tab
        dcc.Tab(label="Strategy Stats", className="tab", selected_className="tab--selected", children=[
            dbc.Row([
                dbc.Col(html.H2("Strategies Overview", style={"textAlign": "center"}), width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(html.Div([
                    html.H3("Box Setup", className="text-center"),
                    html.P("Win Rate: 42%", className="text-center"),
                    html.P("R/R: 1.96", className="text-center"),
                    dbc.Button("View Analytics", color="info", className="d-grid")
                ], className="p-3 bg-dark shadow-sm"), width=4),
                dbc.Col(html.Div([
                    html.H3("FVG/OB", className="text-center"),
                    html.P("Win Rate: 55%", className="text-center"),
                    html.P("R/R: 2.10", className="text-center"),
                    dbc.Button("View Analytics", color="info", className="d-grid")
                ], className="p-3 bg-dark shadow-sm"), width=4)
            ])
        ])
    ])
])

if __name__ == '__main__':
    app.run_server(debug=False)
