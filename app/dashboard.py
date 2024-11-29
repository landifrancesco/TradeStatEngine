import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Initialize Dash app
external_stylesheets = [dbc.themes.DARKLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, title="TradeStatsEngine")
server = app.server


def fetch_data(endpoint):
    try:
        response = requests.get(f"http://127.0.0.1:5000{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return {}


summary = fetch_data('/stats/summary') or {}
pnl_data = fetch_data('/stats/pnl') or []
daily_performance = fetch_data('/stats/daily') or {}
monthly_performance = fetch_data('/stats/monthly') or {}
killzone_performance = fetch_data('/stats/killzone') or {}
killzone_outcomes = fetch_data('/stats/killzone_outcomes') or {}
average_trade_duration = fetch_data('/stats/average_trade_duration') or {}
strategy_success = fetch_data('/stats/strategy_success') or {}
best_worst_trade = fetch_data('/stats/best_worst_trade') or {}
# Fetch reward ratios data
reward_ratios_data = fetch_data('/stats/reward_ratios') or []


# Fetch data for heatmap
duration_data = fetch_data('/stats/duration_heatmap') or []

# Custom color palette
custom_palette = ["#00BC8C", "#E74C3C", "#F39C12"]  # Green, Red, Yellow

# Create a DataFrame
duration_df = pd.DataFrame(duration_data)

if not duration_df.empty:
    num_bins = 10
    bin_edges = pd.cut(duration_df['duration'], bins=num_bins, retbins=True, labels=False)[1]

    def format_minutes_to_hhmm(minutes):
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"

    bin_labels = [
        f"{format_minutes_to_hhmm(bin_edges[i])}-{format_minutes_to_hhmm(bin_edges[i+1])}"
        for i in range(len(bin_edges) - 1)
    ]

    duration_df['Duration Range'] = pd.cut(duration_df['duration'], bins=bin_edges, labels=bin_labels)

    heatmap_data = duration_df.groupby(['Duration Range', 'outcome']).size().reset_index(name='Count')
    heatmap_pivot = heatmap_data.pivot(index='outcome', columns='Duration Range', values='Count').fillna(0)

    heatmap_fig = px.imshow(
        heatmap_pivot,
        title="Heatmap of Trade Outcomes vs. Duration",
        labels={"x": "Duration Ranges (hh:mm)", "y": "Trade Outcome", "color": "Frequency"},
        template="plotly_dark",
        color_continuous_scale='Cividis'
    )

    heatmap_fig.update_layout(
        xaxis_title="Duration Ranges (hh:mm)",
        yaxis_title="Trade Outcome"
    )
else:
    heatmap_fig = go.Figure().update_layout(
        title="Heatmap of Trade Outcomes vs. Duration (No Data)",
        template="plotly_dark"
    )

reward_ratios_df = pd.DataFrame(reward_ratios_data)

if not reward_ratios_df.empty:
    outcome_order = ["Win", "Loss", "Break Even"]
    reward_ratios_df['outcome'] = pd.Categorical(
        reward_ratios_df['outcome'], categories=outcome_order, ordered=True
    )

    reward_ratios_fig = px.violin(
        reward_ratios_df,
        x="reward_ratio",
        y="outcome",
        color="outcome",
        title="Violin Plot of Reward Ratios by Trade Outcome",
        labels={"reward_ratio": "Reward Ratio", "outcome": "Trade Outcome"},
        template="plotly_dark",
        box=True,
        points=False,
        category_orders={"outcome": outcome_order},
        color_discrete_sequence=custom_palette
    )
else:
    reward_ratios_fig = go.Figure().update_layout(
        title="Violin Plot of Reward Ratios by Trade Outcome (No Data)",
        template="plotly_dark"
    )

killzone_list = []
for killzone, outcomes in killzone_outcomes.items():
    killzone_list.append({"Killzone": killzone, "Outcome": "Wins", "Count": outcomes["wins"]})
    killzone_list.append({"Killzone": killzone, "Outcome": "Losses", "Count": outcomes["losses"]})
    killzone_list.append({"Killzone": killzone, "Outcome": "Break-even", "Count": outcomes["break_even"]})

killzone_outcomes_df = pd.DataFrame(killzone_list)

total_pnl = sum([float(entry.get('profit_loss', 0)) for entry in pnl_data]) if pnl_data else 0

total_trades = summary.get('total_trades', 0)
total_wins = summary.get('total_wins', 0)
win_rate = (total_wins / total_trades) * 100 if total_trades > 0 else 0

total_losses = summary.get('total_losses', 0)
total_break_even = summary.get('total_break_even', 0)
total_unknowns = summary.get('total_unknowns', 0)

pnl_df = pd.DataFrame(pnl_data) if pnl_data else pd.DataFrame()
if not pnl_df.empty:
    pnl_df['trade_outcome'] = pnl_df['profit_loss'].apply(
        lambda pnl: 'Win' if pnl > 0.5 else ('Break-even' if abs(pnl) < 0.5 else 'Loss')
    )
    pnl_df['color'] = pnl_df['trade_outcome'].map({'Win': 'green', 'Loss': 'red', 'Break-even': 'yellow', 'Unknown': 'grey'})

    equity_curve_fig = go.Figure()
    equity_curve_fig.add_trace(go.Scatter(x=pnl_df['date'], y=pnl_df['cumulative_pnl'], mode='lines', name='Equity Curve', line=dict(color='blue')))
    for outcome, color in {'Win': custom_palette[0], 'Loss': custom_palette[1], 'Break-even': custom_palette[2], 'Unknown': 'grey'}.items():
        filtered_df = pnl_df[pnl_df['trade_outcome'] == outcome]
        equity_curve_fig.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['cumulative_pnl'], mode='markers', marker=dict(color=color, size=10), name=outcome))
    equity_curve_fig.update_layout(showlegend=False, title="Equity Curve", xaxis_title="Date", yaxis_title="Cumulative P/L (€)", template="plotly_dark")

if monthly_performance:
    monthly_performance_df = pd.DataFrame(monthly_performance.items(), columns=["Month", "PNL"])
else:
    monthly_performance_df = pd.DataFrame()

if not monthly_performance_df.empty:
    month_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    monthly_performance_df["Month"] = pd.Categorical(monthly_performance_df["Month"], categories=month_order, ordered=True)
    monthly_performance_df = monthly_performance_df.sort_values("Month")
    monthly_performance_fig = px.bar(
        monthly_performance_df,
        x="Month",
        y="PNL",
        title="Monthly Performance",
        labels={"Month": "Month", "PNL": "Net Gains (€)"},
        color="PNL",
        template="plotly_dark",
        color_continuous_scale='Cividis'
    )
    monthly_performance_fig.update_layout()

daily_performance_list = []
for day, outcomes in daily_performance.items():
    daily_performance_list.append({"Day": day, "Wins": outcomes.get("wins", 0), "Losses": outcomes.get("losses", 0), "Break-even": outcomes.get("break_even", 0)})

daily_performance_df = pd.DataFrame(daily_performance_list)
if not daily_performance_df.empty:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily_performance_df['Day'] = pd.Categorical(daily_performance_df['Day'], categories=day_order, ordered=True)
    daily_performance_df = daily_performance_df.sort_values('Day')
    daily_performance_df = daily_performance_df.melt(id_vars='Day', value_vars=['Wins', 'Losses', 'Break-even'], var_name='Outcome', value_name='Count')
    daily_performance_fig = px.bar(
        daily_performance_df,
        x='Day',
        y='Count',
        color='Outcome',
        title="Daily Performance",
        labels={"Count": "Count", "Day": "Day of the Week"},
        template="plotly_dark",
        color_discrete_sequence=custom_palette
    )
    daily_performance_fig.update_layout(showlegend=False)

killzone_list = []
for killzone, days in killzone_performance.items():
    for day, count in days.items():
        killzone_list.append({"Killzone": killzone, "Day": day, "Count": count})

killzone_df = pd.DataFrame(killzone_list)
killzone_df['Day'] = pd.Categorical(killzone_df['Day'], categories=day_order, ordered=True)
killzone_df = killzone_df.sort_values(['Killzone', 'Day'])

profit_by_killzone_fig = px.bar(
    killzone_df,
    x="Killzone",
    y="Count",
    color="Day",
    title="Trade Count by Killzone and Day",
    labels={"Count": "Trade Count", "Killzone": "Killzone"},
    template="plotly_dark",
    barmode="group",
)

killzone_outcomes_fig = px.bar(
    killzone_outcomes_df,
    x="Killzone",
    y="Count",
    color="Outcome",
    title="Trade Outcomes by Killzone (Wins, Losses, Break-even)",
    labels={"Count": "Trade Count", "Killzone": "Killzone"},
    template="plotly_dark",
    barmode="group",
    color_discrete_sequence=custom_palette
)
killzone_outcomes_fig.update_layout(showlegend=False)

app.layout = dbc.Container([
    html.H1("TradeStatsEngine 📈", className="text-center my-4"),
    dbc.Row([
        dbc.Col(html.Div([html.H4("Total P/L", className="text-center"), html.H1(f"€{total_pnl:.2f}", className="text-center", style={"color": "green" if total_pnl >= 0 else "red"})]), width=4),
        dbc.Col(html.Div([html.H4("Win Rate", className="text-center"), html.H1(f"{win_rate:.2f}%", className="text-warning text-center")]), width=4),
        dbc.Col(html.Div([html.H4("Total Trades", className="text-center"), html.H1(f"{summary.get('total_trades', 0)}", className="text-primary text-center")]), width=4)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(html.Div([html.H5("Wins", className="text-center"), html.H3(f"{total_wins}", className="text-success text-center")]), width=3),
        dbc.Col(html.Div([html.H5("Losses", className="text-center"), html.H3(f"{total_losses}", className="text-danger text-center")]), width=3),
        dbc.Col(html.Div([html.H5("Break Even", className="text-center"), html.H3(f"{total_break_even}", className="text-info text-center")]), width=3),
        dbc.Col(html.Div([html.H5("Unknowns", className="text-center"), html.H3(f"{total_unknowns}", className="text-muted text-center")]), width=3)
    ], className="mb-4"),
    dbc.Row([dbc.Col(dcc.Graph(figure=equity_curve_fig, config={"displayModeBar": True}), width=12)], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=monthly_performance_fig, config={"displayModeBar": True}), width=6),
        dbc.Col(dcc.Graph(figure=daily_performance_fig, config={"displayModeBar": True}), width=6)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=killzone_outcomes_fig, config={"displayModeBar": True}), width=6),
        dbc.Col(dcc.Graph(figure=profit_by_killzone_fig, config={"displayModeBar": True}), width=6)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=reward_ratios_fig, config={"displayModeBar": True}), width=12),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=heatmap_fig, config={"displayModeBar": True}), width=12)

    ], className="mb-4"),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H4("Best Trades", className="text-center"),
                html.Ul([
                    html.Li(
                        f"File: {trade.get('filename', 'N/A')} | Profit: €{trade.get('profit_loss', 'N/A')}")
                    for trade in best_worst_trade.get('best_trades', [])
                ])
            ]), width=6
        ),
        dbc.Col(
            html.Div([
                html.H4("Worst Trades", className="text-center"),
                html.Ul([
                    html.Li(
                        f"File: {trade.get('filename', 'N/A')} | Loss: €{trade.get('profit_loss', 'N/A')}")
                    for trade in best_worst_trade.get('worst_trades', [])
                ])
            ]), width=6
        )
    ])
], fluid=True)

if __name__ == '__main__':
    app.run_server(debug=False)
