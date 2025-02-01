import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Initialize Dash app with a dark theme
external_stylesheets = [dbc.themes.DARKLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, title="TradeStatsEngine")
server = app.server

# Helper function to fetch data from the backend
def fetch_data(endpoint, params=None):
    try:
        response = requests.get(f"http://127.0.0.1:5000{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return {}

# Fetch the list of accounts for the dropdown
accounts = fetch_data('/accounts')
if not accounts:
    print("No accounts fetched from backend. Please ensure the backend is running and accessible.")
    accounts = [{"id": 0, "name": "No Accounts Available"}]
account_options = [{"label": account["name"], "value": account["id"]} for account in accounts]

# Layout
app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H1("TradeStatsEngine 📈", className="my-4 text-center"),
            width=12
        )
    ),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H4("Select Account", className="mb-2"),
                dbc.Select(
                    id="account-dropdown",
                    options=account_options,
                    value=accounts[0]["id"] if accounts else None,
                    style={
                        "backgroundColor": "#333",
                        "color": "#fff",
                        "fontSize": "16px",
                        "width": "70%",  # Adjust width as needed
                    },
                )
            ]),
            width=6,
            style={"textAlign": "left"}
        ),
        dbc.Col(
            html.Div(
                dbc.Button(
                    "Import File",
                    color="primary",
                    href="http://127.0.0.1:5050/upload",
                    target="_blank"
                ),
                style={"textAlign": "right", "marginTop": "20px"}
            ),
            width=6
        )
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H4("Total P/L", className="text-center"),
                html.H1(id="total-pnl", className="text-primary text-center")
            ]),
            width=4
        ),
        dbc.Col(
            html.Div([
                html.H4("Win Rate", className="text-center"),
                html.H1(id="win-rate", className="text-info text-center")
            ]),
            width=4
        ),
        dbc.Col(
            html.Div([
                html.H4("Total Trades", className="text-center"),
                html.H1(id="total-trades", className="text-center")
            ]),
            width=4
        ),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H5("Win", className="text-center"),
                html.H3(id="total-wins", className="text-success text-center")
            ]),
            width=3
        ),
        dbc.Col(
            html.Div([
                html.H5("Loss", className="text-center"),
                html.H3(id="total-losses", className="text-danger text-center")
            ]),
            width=3
        ),
        dbc.Col(
            html.Div([
                html.H5("Break Even", className="text-center"),
                html.H3(id="total-break-even", className="text-warning text-center")
            ]),
            width=3
        ),
        dbc.Col(
            html.Div([
                html.H5("Unknowns", className="text-center"),
                html.H3(id="total-unknowns", className="text-muted text-center")
            ]),
            width=3
        ),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="equity-curve", config={"displayModeBar": True}), width=12)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="monthly-performance", config={"displayModeBar": True}), width=6),
        dbc.Col(dcc.Graph(id="daily-performance", config={"displayModeBar": True}), width=6)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(
            html.Div([
                dbc.Checkbox(
                    id="time-writing-toggle",
                    label="Order by Time Writing (Paper Account Only)",
                    value=False,
                    style={"marginTop": "10px", "fontSize": "16px", "color": "#fff"}
                )
            ], className="text-center"),
            width=6
        )
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="killzone-outcomes", config={"displayModeBar": True}), width=6),
        dbc.Col(dcc.Graph(id="profit-by-killzone", config={"displayModeBar": True}), width=6)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="reward-ratios", config={"displayModeBar": True}), width=6),
        dbc.Col(dcc.Graph(id="heatmap", config={"displayModeBar": True}), width=6)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H4("Best Trades", className="text-center"),
                html.Ul(id="best-trades-list")
            ]),
            width=6
        ),
        dbc.Col(
            html.Div([
                html.H4("Worst Trades", className="text-center"),
                html.Ul(id="worst-trades-list")
            ]),
            width=6
        )
    ]),
], fluid=True)

# Callback to update graphs and statistics when an account is selected
@app.callback(
    [
        Output("total-pnl", "children"),
        Output("win-rate", "children"),
        Output("total-trades", "children"),
        Output("total-wins", "children"),
        Output("total-losses", "children"),
        Output("total-break-even", "children"),
        Output("total-unknowns", "children"),
        Output("equity-curve", "figure"),
        Output("monthly-performance", "figure"),
        Output("daily-performance", "figure"),
        Output("killzone-outcomes", "figure"),
        Output("profit-by-killzone", "figure"),
        Output("reward-ratios", "figure"),
        Output("heatmap", "figure"),
        Output("best-trades-list", "children"),
        Output("worst-trades-list", "children"),
    ],
    [
        Input("account-dropdown", "value"),
        Input("time-writing-toggle", "value")
    ]
)
def update_dashboard(selected_account, time_writing_toggle):
    # Fetch data from your backend
    summary = fetch_data(f"/stats/summary?account_id={selected_account}") or {}
    pnl_data = fetch_data(f"/stats/pnl?account_id={selected_account}") or []
    monthly_performance = fetch_data(f"/stats/monthly?account_id={selected_account}&time_writing_toggle={str(time_writing_toggle).lower()}") or {}
    daily_performance = fetch_data(f"/stats/daily?account_id={selected_account}") or {}
    killzone_performance = fetch_data(f"/stats/killzone?account_id={selected_account}") or {}
    killzone_outcomes = fetch_data(f"/stats/killzone_outcomes?account_id={selected_account}") or {}
    reward_ratios_data = fetch_data(f"/stats/reward_ratios?account_id={selected_account}") or []
    duration_data = fetch_data(f"/stats/duration_heatmap?account_id={selected_account}") or []
    best_worst_trade = fetch_data(f"/stats/best_worst_trade?account_id={selected_account}") or {}

    # Total PNL and Win Rate
    total_pnl = sum([float(entry.get('profit_loss', 0)) for entry in pnl_data]) if pnl_data else 0
    total_trades = summary.get("total_trades", 0)
    win_rate = (summary.get("total_wins", 0) / total_trades) * 100 if total_trades else 0

    # Color mapping for outcomes
    color_mapping = {
        "Win": "#00BC8C",
        "Loss": "#E74C3C",
        "Break-even": "#F39C12",
        "Unknown": "grey"
    }
    outcome_order = ['Win', 'Break-even', 'Loss']

    # Equity Curve
    if pnl_data:
        pnl_df = pd.DataFrame(pnl_data)
        pnl_df['trade_outcome'] = pnl_df['profit_loss'].apply(
            lambda pnl: 'Win' if pnl > 0.5 else ('Break-even' if abs(pnl) < 0.5 else 'Loss')
        )
        pnl_df['color'] = pnl_df['trade_outcome'].map(color_mapping)
        pnl_df['trade_outcome'] = pd.Categorical(
            pnl_df['trade_outcome'],
            categories=outcome_order,
            ordered=True
        )
        equity_curve_fig = go.Figure()
        equity_curve_fig.add_trace(go.Scatter(
            x=pnl_df['date'],
            y=pnl_df['cumulative_pnl'],
            mode='lines',
            name='Equity Curve',
            line=dict(color='blue')
        ))
        for outcome in outcome_order:
            filtered_df = pnl_df[pnl_df['trade_outcome'] == outcome]
            if not filtered_df.empty:
                equity_curve_fig.add_trace(go.Scatter(
                    x=filtered_df['date'],
                    y=filtered_df['cumulative_pnl'],
                    mode='markers',
                    marker=dict(color=filtered_df['color'].iloc[0], size=10),
                    name=outcome
                ))
        equity_curve_fig.update_layout(
            title="Equity Curve",
            xaxis_title="Date",
            yaxis_title="Cumulative P/L (€)",
            template="plotly_dark",
            showlegend=True
        )
    else:
        equity_curve_fig = go.Figure().update_layout(
            title="Equity Curve (No Data)",
            template="plotly_dark"
        )

    # Monthly Performance
    if monthly_performance:
        monthly_df = pd.DataFrame(monthly_performance.items(), columns=["Month", "PNL"])
        monthly_df["Month"] = pd.to_datetime(monthly_df["Month"], format="%Y-%m", errors="coerce")
        monthly_df = monthly_df.sort_values("Month")
        monthly_df["Month"] = monthly_df["Month"].dt.strftime("%B %Y")
        monthly_performance_fig = px.bar(
            monthly_df,
            x="Month",
            y="PNL",
            title="Monthly Performance",
            labels={"Month": "Month", "PNL": "Net Gains (€)"},
            color="PNL",
            template="plotly_dark",
            color_continuous_scale='Cividis'
        )
        monthly_performance_fig.update_xaxes(
            tickmode="array",
            tickvals=monthly_df["Month"].unique()
        )
    else:
        monthly_performance_fig = go.Figure().update_layout(
            title="Monthly Performance (No Data)",
            template="plotly_dark"
        )

    # Daily Performance
    daily_performance_list = []
    for day, stats in daily_performance.items():
        daily_performance_list.append({"Day": day, "Outcome": "Win", "Count": stats.get("wins", 0)})
        daily_performance_list.append({"Day": day, "Outcome": "Loss", "Count": stats.get("losses", 0)})
        daily_performance_list.append({"Day": day, "Outcome": "Break-even", "Count": stats.get("break_even", 0)})
    daily_df = pd.DataFrame(daily_performance_list)
    if not daily_df.empty:
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_df['Day'] = pd.Categorical(daily_df['Day'], categories=day_order, ordered=True)
        daily_df = daily_df.sort_values('Day')
        daily_df['color'] = daily_df['Outcome'].map(color_mapping)
        daily_df['Outcome'] = pd.Categorical(
            daily_df['Outcome'],
            categories=outcome_order,
            ordered=True
        )
        daily_performance_fig = go.Figure()
        for outcome in outcome_order:
            outcome_df = daily_df[daily_df['Outcome'] == outcome]
            if not outcome_df.empty:
                daily_performance_fig.add_trace(go.Bar(
                    x=outcome_df['Day'],
                    y=outcome_df['Count'],
                    name=outcome,
                    marker=dict(color=outcome_df['color'].iloc[0])
                ))
        daily_performance_fig.update_layout(
            title="Daily Performance",
            xaxis_title="Day",
            yaxis_title="Count",
            template="plotly_dark",
            barmode="group"
        )
    else:
        daily_performance_fig = go.Figure().update_layout(
            title="Daily Performance (No Data)",
            template="plotly_dark"
        )

    # Killzone Outcomes
    killzone_list = []
    for killzone, outcomes in killzone_outcomes.items():
        killzone_list.append({"Killzone": killzone, "Outcome": "Win", "Count": outcomes["wins"]})
        killzone_list.append({"Killzone": killzone, "Outcome": "Loss", "Count": outcomes["losses"]})
        killzone_list.append({"Killzone": killzone, "Outcome": "Break-even", "Count": outcomes["break_even"]})
    killzone_outcomes_df = pd.DataFrame(killzone_list)
    if not killzone_outcomes_df.empty:
        killzone_outcomes_df['color'] = killzone_outcomes_df['Outcome'].map(color_mapping)
        killzone_outcomes_df['Outcome'] = pd.Categorical(
            killzone_outcomes_df['Outcome'],
            categories=outcome_order,
            ordered=True
        )
        killzone_outcomes_fig = go.Figure()
        for outcome in outcome_order:
            outcome_df = killzone_outcomes_df[killzone_outcomes_df['Outcome'] == outcome]
            if not outcome_df.empty:
                killzone_outcomes_fig.add_trace(go.Bar(
                    x=outcome_df['Killzone'],
                    y=outcome_df['Count'],
                    name=outcome,
                    marker=dict(color=outcome_df['color'].iloc[0])
                ))
        killzone_outcomes_fig.update_layout(
            title="Trade Outcomes by Killzone",
            xaxis_title="Killzone",
            yaxis_title="Count",
            template="plotly_dark",
            barmode="group"
        )
    else:
        killzone_outcomes_fig = go.Figure().update_layout(
            title="Trade Outcomes by Killzone (No Data)",
            template="plotly_dark"
        )

    # Killzone Performance
    killzone_list = []
    for killzone, days in killzone_performance.items():
        for day, count in days.items():
            killzone_list.append({"Killzone": killzone, "Day": day, "Count": count})
    killzone_df = pd.DataFrame(killzone_list)
    if not killzone_df.empty:
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        killzone_df['Day'] = pd.Categorical(killzone_df['Day'], categories=day_order, ordered=True)
        killzone_df = killzone_df.sort_values(['Killzone', 'Day'])
        killzone_fig = px.bar(
            killzone_df,
            x="Killzone",
            y="Count",
            color="Day",
            title="Killzone Performance by Day",
            labels={"Count": "Trade Count", "Killzone": "Killzone"},
            template="plotly_dark",
            barmode="group",
            color_discrete_sequence=['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692']
        )
    else:
        killzone_fig = go.Figure().update_layout(
            title="Killzone Performance by Day (No Data)",
            template="plotly_dark"
        )

    # Heatmap of Duration
    duration_df = pd.DataFrame(duration_data)
    if not duration_df.empty:
        bin_edges = pd.cut(duration_df['duration'], bins=10, retbins=True)[1]
        def format_range(start, end):
            return f"{int(start)}-{int(end)}"
        bin_labels = [format_range(bin_edges[i], bin_edges[i + 1]) for i in range(len(bin_edges) - 1)]
        duration_df['Duration Range'] = pd.cut(duration_df['duration'], bins=bin_edges, labels=bin_labels)
        heatmap_data = duration_df.groupby(['Duration Range', 'outcome']).size().reset_index(name='Count')
        heatmap_pivot = heatmap_data.pivot(index='outcome', columns='Duration Range', values='Count').fillna(0)
        heatmap_fig = px.imshow(
            heatmap_pivot,
            title="Heatmap of Trade Outcomes vs. Duration",
            labels={"x": "Duration Range (in minutes)", "y": "Trade Outcome", "color": "Frequency"},
            template="plotly_dark",
            color_continuous_scale='Cividis'
        )
        heatmap_fig.update_layout(
            xaxis_title="Duration Ranges (Minutes)",
            yaxis_title="Trade Outcome",
            font=dict(size=12)
        )
    else:
        heatmap_fig = go.Figure().update_layout(
            title="Heatmap of Trade Outcomes vs. Duration (No Data)",
            template="plotly_dark"
        )

    # Reward Ratios
    reward_ratios_df = pd.DataFrame(reward_ratios_data)
    if not reward_ratios_df.empty:
        reward_ratios_df['outcome'] = pd.Categorical(
            reward_ratios_df['outcome'],
            categories=outcome_order,
            ordered=True
        )
        reward_ratios_fig = px.box(
            reward_ratios_df,
            x="outcome",
            y="reward_ratio",
            color="outcome",
            title="Reward Ratios by Trade Outcome",
            template="plotly_dark",
            labels={"outcome": "Trade Outcome", "reward_ratio": "Reward Ratio"},
            color_discrete_map=color_mapping,
            points="all"
        )
        reward_ratios_fig.update_layout(
            xaxis_title="Trade Outcome",
            yaxis_title="Reward Ratio",
            showlegend=False,
            boxmode="group",
            font=dict(size=12)
        )
    else:
        reward_ratios_fig = go.Figure().update_layout(
            title="Reward Ratios by Trade Outcome (No Data)",
            template="plotly_dark"
        )

    # Best/Worst Trades
    best_trades_list = [
        html.Li(f"File: {trade.get('filename')} | Profit: €{trade.get('profit_loss')}")
        for trade in best_worst_trade.get("best_trades", [])
    ]
    worst_trades_list = [
        html.Li(f"File: {trade.get('filename')} | Loss: €{trade.get('profit_loss')}")
        for trade in best_worst_trade.get("worst_trades", [])
    ]

    return (
        f"€{total_pnl:.2f}",
        f"{win_rate:.2f}%",
        summary.get("total_trades", 0),
        summary.get("total_wins", 0),
        summary.get("total_losses", 0),
        summary.get("total_break_even", 0),
        summary.get("total_unknowns", 0),
        equity_curve_fig,
        monthly_performance_fig,
        daily_performance_fig,
        killzone_fig,
        killzone_outcomes_fig,
        reward_ratios_fig,
        heatmap_fig,
        best_trades_list,
        worst_trades_list
    )

if __name__ == "__main__":
    app.run_server(debug=False)
