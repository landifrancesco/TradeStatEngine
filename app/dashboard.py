import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Initialize Dash app
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
account_options = [{"label": account["name"], "value": account["id"]} for account in accounts]

# Layout with Dropdown for Account Selection
app.layout = dbc.Container([
    html.H1("TradeStatsEngine 📈", className="text-center my-4"),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H4("Select Account", className="text-center"),
                dbc.Select(
                    id="account-dropdown",
                    options=[{"label": acc["name"], "value": acc["id"]} for acc in accounts],
                    value=accounts[0]["id"],  # Default value (first account)
                    className="mb-4",
                    style={
                        "backgroundColor": "#333",  # Matches the dark theme
                        "color": "#fff",  # White text for better contrast
                        "fontSize": "16px",  # Larger font size
                        "width": "50%",  # Wider dropdown
                        "margin": "0 auto",  # Center the dropdown
                    },
                )

            ]),
            width=4,
            className="offset-4",
        ),
    ], className="mb-4"
    ),
    dbc.Row([
        dbc.Col(
            html.Div([html.H4("Total P/L", className="text-center"), html.H1(id="total-pnl", className="text-primary text-center")]),
            width=4),
        dbc.Col(
            html.Div([html.H4("Win Rate", className="text-center"), html.H1(id="win-rate", className="text-info text-center")]),
            width=4),
        dbc.Col(html.Div(
            [html.H4("Total Trades", className="text-center"), html.H1(id="total-trades", className="text-center")]),
                width=4),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(html.Div([html.H5("Wins", className="text-center"), html.H3(id="total-wins", className="text-success text-center")]),
                width=3),
        dbc.Col(
            html.Div([html.H5("Losses", className="text-center"), html.H3(id="total-losses", className="text-danger text-center")]),
            width=3),
        dbc.Col(html.Div(
            [html.H5("Break Even", className="text-center"), html.H3(id="total-break-even", className="text-warning text-center")]),
                width=3),
        dbc.Col(html.Div(
            [html.H5("Unknowns", className="text-center"), html.H3(id="total-unknowns", className="text-muted text-center")]),
                width=3),
    ], className="mb-4"),
    dbc.Row([dbc.Col(dcc.Graph(id="equity-curve", config={"displayModeBar": True}), width=12)], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="monthly-performance", config={"displayModeBar": True}), width=6),
        dbc.Col(dcc.Graph(id="daily-performance", config={"displayModeBar": True}), width=6)
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
            ]), width=6
        ),
        dbc.Col(
            html.Div([
                html.H4("Worst Trades", className="text-center"),
                html.Ul(id="worst-trades-list")
            ]), width=6
        )
    ])
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
    [Input("account-dropdown", "value")]
)
def update_dashboard(selected_account):
    # Fetch data for the selected account
    summary = fetch_data(f"/stats/summary?account_id={selected_account}") or {}
    pnl_data = fetch_data(f"/stats/pnl?account_id={selected_account}") or []
    daily_performance = fetch_data(f"/stats/daily?account_id={selected_account}") or {}
    monthly_performance = fetch_data(f"/stats/monthly?account_id={selected_account}") or {}
    killzone_performance = fetch_data(f"/stats/killzone?account_id={selected_account}") or {}
    killzone_outcomes = fetch_data(f"/stats/killzone_outcomes?account_id={selected_account}") or {}
    reward_ratios_data = fetch_data(f"/stats/reward_ratios?account_id={selected_account}") or []
    duration_data = fetch_data(f"/stats/duration_heatmap?account_id={selected_account}") or []
    best_worst_trade = fetch_data(f"/stats/best_worst_trade?account_id={selected_account}") or {}

    # Total PNL and Win Rate
    total_pnl = sum([float(entry.get('profit_loss', 0)) for entry in pnl_data]) if pnl_data else 0
    total_trades = summary.get("total_trades", 0)
    win_rate = (summary.get("total_wins", 0) / total_trades) * 100 if total_trades else 0


    # Equity Curve
    pnl_df = pd.DataFrame(pnl_data) if pnl_data else pd.DataFrame()
    if not pnl_df.empty:
        pnl_df['trade_outcome'] = pnl_df['profit_loss'].apply(
            lambda pnl: 'Win' if pnl > 0.5 else ('Break-even' if abs(pnl) < 0.5 else 'Loss')
        )
        pnl_df['color'] = pnl_df['trade_outcome'].map({'Win': 'green', 'Loss': 'red', 'Break-even': 'yellow', 'Unknown': 'grey'})
        equity_curve_fig = go.Figure()
        equity_curve_fig.add_trace(go.Scatter(
            x=pnl_df['date'],
            y=pnl_df['cumulative_pnl'],
            mode='lines',
            name='Equity Curve',
            line=dict(color='blue')
        ))
        for outcome, color in {'Win': 'green', 'Loss': 'red', 'Break-even': 'yellow', 'Unknown': 'grey'}.items():
            filtered_df = pnl_df[pnl_df['trade_outcome'] == outcome]
            equity_curve_fig.add_trace(go.Scatter(
                x=filtered_df['date'],
                y=filtered_df['cumulative_pnl'],
                mode='markers',
                marker=dict(color=color, size=10),
                name=outcome
            ))
        equity_curve_fig.update_layout(
            showlegend=True,
            title="Equity Curve",
            xaxis_title="Date",
            yaxis_title="Cumulative P/L (€)",
            template="plotly_dark"
        )
    else:
        equity_curve_fig = go.Figure().update_layout(
            title="Equity Curve (No Data)",
            template="plotly_dark"
        )

    # Monthly Performance
    if monthly_performance:
        monthly_performance_df = pd.DataFrame(monthly_performance.items(), columns=["Month", "PNL"])
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
    else:
        monthly_performance_fig = go.Figure().update_layout(
            title="Monthly Performance (No Data)",
            template="plotly_dark"
        )

    # Daily Performance
    daily_performance_list = []
    for day, stats in daily_performance.items():
        daily_performance_list.append({"Day": day, "Outcome": "Wins", "Count": stats.get("wins", 0)})
        daily_performance_list.append({"Day": day, "Outcome": "Losses", "Count": stats.get("losses", 0)})
        daily_performance_list.append({"Day": day, "Outcome": "Break-even", "Count": stats.get("break_even", 0)})
    daily_df = pd.DataFrame(daily_performance_list)
    if not daily_df.empty:
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_df['Day'] = pd.Categorical(daily_df['Day'], categories=day_order, ordered=True)
        daily_df = daily_df.sort_values('Day')
        daily_performance_fig = px.bar(
            daily_df,
            x="Day",
            y="Count",
            color="Outcome",
            title="Daily Performance",
            template="plotly_dark",
            color_discrete_sequence=['#E74C3C', '#F39C12', '#00BC8C'],  # Custom palette
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
        killzone_list.append({"Killzone": killzone, "Outcome": "Wins", "Count": outcomes["wins"]})
        killzone_list.append({"Killzone": killzone, "Outcome": "Losses", "Count": outcomes["losses"]})
        killzone_list.append({"Killzone": killzone, "Outcome": "Break-even", "Count": outcomes["break_even"]})
    killzone_outcomes_df = pd.DataFrame(killzone_list)
    if not killzone_outcomes_df.empty:
        killzone_outcomes_fig = px.bar(
            killzone_outcomes_df,
            x="Killzone",
            y="Count",
            color="Outcome",
            title="Trade Outcomes by Killzone",
            template="plotly_dark",
            barmode="group",
            color_discrete_sequence=['#00BC8C', '#E74C3C', '#F39C12']
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

    # Heatmap
    duration_df = pd.DataFrame(duration_data)
    if not duration_df.empty:
        # Define the bins and labels based on duration
        bin_edges = pd.cut(duration_df['duration'], bins=10, retbins=True)[1]

        # Function to format the bin labels as ranges
        def format_range(start, end):
            return f"{int(start)}-{int(end)}"

        # Create labels for the bins using the bin edges
        bin_labels = [
            format_range(bin_edges[i], bin_edges[i + 1])
            for i in range(len(bin_edges) - 1)
        ]

        # Assign the new labels to the 'Duration Range' column
        duration_df['Duration Range'] = pd.cut(
            duration_df['duration'],
            bins=bin_edges,
            labels=bin_labels
        )

        # Optional: Include a legend in the visualization
        heatmap_data = duration_df.groupby(['Duration Range', 'outcome']).size().reset_index(name='Count')
        heatmap_pivot = heatmap_data.pivot(index='outcome', columns='Duration Range', values='Count').fillna(0)

        heatmap_fig = px.imshow(
            heatmap_pivot,
            title="Heatmap of Trade Outcomes vs. Duration",
            labels={
                "x": "Duration Range (in minutes)",
                "y": "Trade Outcome",
                "color": "Frequency"
            },
            template="plotly_dark",
            color_continuous_scale='Cividis'
        )

        # Add range descriptions to the title or as a legend
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
        reward_ratios_fig = px.box(
            reward_ratios_df,
            x="outcome",
            y="reward_ratio",
            color="outcome",
            title="Reward Ratios by Trade Outcome",
            template="plotly_dark",
            labels={
                "outcome": "Trade Outcome",
                "reward_ratio": "Reward Ratio"
            },
            color_discrete_sequence=['#E74C3C', '#F39C12', '#00BC8C'],  # Custom palette for colors
            points="all"  # Show all data points for better clarity
        )

        # Update layout for better visuals
        reward_ratios_fig.update_layout(
            xaxis_title="Trade Outcome",
            yaxis_title="Reward Ratio",
            showlegend=False,  # Hide the legend since color already represents the outcome
            boxmode="group",  # Group boxes if categories increase
            font=dict(size=12)  # Adjust font size for better readability
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

