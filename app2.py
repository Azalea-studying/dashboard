import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import numpy as np

# ---------------------- 初始化Dash应用 ----------------------
app = Dash(__name__)
server = app.server  # 暴露Flask服务

# ---------------------- 读取示例数据 ----------------------
revenue_df = pd.read_csv("revenue_df.csv")
cogs_df = pd.read_csv("cogs_df.csv")
profit_df = pd.read_csv("profit_df.csv")
expenses_df = pd.read_csv("expenses_df.csv")
budget_df = pd.read_csv("budget_df.csv")
balance_sheet_df = pd.read_csv("balance_sheet_df.csv")

# ---------------------- 应用布局（包含交互筛选器+仪表盘） ----------------------
app.layout = html.Div([
    # 标题+说明
    html.H1("Financial Analytics Dashboard", style={"textAlign": "center", "margin": "20px 0"}),
    html.P(
        "Use the filters below to customize your view of the financial data:",
        style={"textAlign": "center", "fontSize": 16, "marginBottom": "20px"}
    ),

    # 交互筛选器（用户友好核心）
    html.Div([
        # 年份范围筛选
        html.Div([
            html.Label("Select Year Range:"),
            dcc.Dropdown(
                id="year-filter",
                options=[{"label": y, "value": y} for y in revenue_df["Year"]],
                value=revenue_df["Year"].tolist(),  # 默认选所有年份
                multi=True,
                style={"width": "250px"}
            )
        ], style={"display": "inline-block", "marginRight": "30px"}),

        # 业务单元筛选
        html.Div([
            html.Label("Select Business Unit:"),
            dcc.Dropdown(
                id="bu-filter",
                options=[
                    {"label": "All Units", "value": "all"},
                    {"label": "Business 1", "value": "Business 1"},
                    {"label": "Business 2", "value": "Business 2"},
                    {"label": "Business 3", "value": "Business 3"}
                ],
                value="all",
                style={"width": "200px"}
            )
        ], style={"display": "inline-block"})
    ], style={"textAlign": "center", "marginBottom": "30px", "padding": "10px", "background": "#f5f5f5", "borderRadius": "5px"}),

    # 仪表盘图表区域
    html.Div([
        # 第一行
        html.Div([
            html.Div([dcc.Graph(id="revenue-trend")], style={"width": "50%", "display": "inline-block"}),
            html.Div([dcc.Graph(id="profit-margin")], style={"width": "50%", "display": "inline-block"})
        ], style={"marginBottom": "30px"}),

        # 第二行
        html.Div([
            html.Div([dcc.Graph(id="revenue-dist")], style={"width": "50%", "display": "inline-block"}),
            html.Div([dcc.Graph(id="expenses-trend")], style={"width": "50%", "display": "inline-block"})
        ], style={"marginBottom": "30px"}),

        # 第三行
        html.Div([
            html.Div([dcc.Graph(id="budget-vs-actual")], style={"width": "50%", "display": "inline-block"}),
            html.Div([dcc.Graph(id="balance-sheet")], style={"width": "50%", "display": "inline-block"})
        ], style={"marginBottom": "30px"}),

        # 第四行
        html.Div([
            html.Div([dcc.Graph(id="cagr-radar")], style={"width": "50%", "display": "inline-block"}),
            html.Div([dcc.Graph(id="cost-structure")], style={"width": "50%", "display": "inline-block"})
        ])
    ], style={"padding": "20px"})
])

# ---------------------- 回调函数：根据筛选器更新图表 ----------------------
@callback(
    [Output("revenue-trend", "figure"),
     Output("profit-margin", "figure"),
     Output("revenue-dist", "figure"),
     Output("expenses-trend", "figure"),
     Output("budget-vs-actual", "figure"),
     Output("balance-sheet", "figure"),
     Output("cagr-radar", "figure"),
     Output("cost-structure", "figure")],
    [Input("year-filter", "value"),
     Input("bu-filter", "value")]
)
def update_dashboard(selected_years, selected_bu):
    # 筛选年份
    filtered_rev = revenue_df[revenue_df["Year"].isin(selected_years)]
    filtered_profit = profit_df[profit_df["Year"].isin(selected_years)]
    filtered_exp = expenses_df[expenses_df["Year"].isin(selected_years)]
    filtered_cogs = cogs_df[cogs_df["Year"].isin(selected_years)]

    # 1. 收入趋势图（按业务单元筛选）
    if selected_bu != "all":
        rev_fig = px.line(
            filtered_rev, x="Year", y=selected_bu,
            title=f"{selected_bu} Revenue Trend",
            labels={"value": "Revenue ($)"},
            hover_data={"value": ":,.0f"},
            color_discrete_sequence=["#1f77b4"]
        )
    else:
        rev_fig = px.area(
            filtered_rev, x="Year", y=["Business 1", "Business 2", "Business 3"],
            title="All Business Units Revenue Trend",
            labels={"value": "Revenue ($)", "variable": "Business Unit"},
            hover_data={"value": ":,.0f"},
            color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]
        )
    rev_fig.update_layout(hovermode="x unified", template="plotly_white", height=400)

    # 2. 利润率图
    profit_fig = go.Figure()
    profit_fig.add_trace(go.Bar(
        x=filtered_profit["Year"], y=filtered_profit["Profit $"], name="Profit ($)",
        hovertemplate="Year: %{x}<br>Profit: $%{y:,.0f}",
        marker_color="#2ca02c"
    ))
    profit_fig.add_trace(go.Scatter(
        x=filtered_profit["Year"], y=filtered_profit["Profit %"], name="Profit (%)",
        mode="lines+markers", line=dict(color="#ff7f0e", width=3),
        yaxis="y2", hovertemplate="Year: %{x}<br>Profit %: %{y}%"
    ))
    profit_fig.update_layout(
        title="Profit Margin Analysis",
        yaxis=dict(title="Profit ($)", tickformat="$,.0f"),
        yaxis2=dict(title="Profit (%)", overlaying="y", side="right"),
        template="plotly_white", hovermode="x unified", height=400
    )

    # 3. 收入分布饼图（最新年份）
    latest_year = filtered_rev["Year"].iloc[-1] if not filtered_rev.empty else revenue_df["Year"].iloc[-1]
    rev_latest = revenue_df[revenue_df["Year"] == latest_year]
    if selected_bu != "all":
        rev_dist_fig = px.pie(
            names=[selected_bu], values=[rev_latest[selected_bu].iloc[0]],
            title=f"{selected_bu} Revenue (Year: {latest_year})",
            hole=0.3,
            hover_data={"values": ":,.0f"},
            color_discrete_sequence=["#1f77b4"]
        )
    else:
        rev_dist_fig = px.pie(
            names=["Business 1", "Business 2", "Business 3"],
            values=[rev_latest["Business 1"].iloc[0], rev_latest["Business 2"].iloc[0], rev_latest["Business 3"].iloc[0]],
            title=f"Revenue Distribution (Year: {latest_year})",
            hole=0.3,
            hover_data={"values": ":,.0f"},
            color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]
        )
    rev_dist_fig.update_traces(textinfo="percent+label")
    rev_dist_fig.update_layout(template="plotly_white", height=400)

    # 4. 费用趋势图
    exp_fig = px.area(
        filtered_exp, x="Year", y=["Salaries", "Rent", "D&A", "Interest"],
        title="Expenses Trend Over Time",
        labels={"value": "Expense ($)", "variable": "Expense Type"},
        hover_data={"value": ":,.0f"},
        color_discrete_sequence=["#d62728", "#9467bd", "#8c564b", "#e377c2"]
    )
    exp_fig.update_layout(hovermode="x unified", template="plotly_white", height=400)

    # 5. 预算vs实际
    budget_fig = go.Figure()
    budget_vals = [
        budget_df.loc[budget_df["Category"]=="Revenue", "Value"].iloc[0],
        budget_df.loc[budget_df["Category"]=="COGS", "Value"].iloc[0],
        budget_df.loc[budget_df["Category"]=="Expenses", "Value"].iloc[0],
        budget_df.loc[budget_df["Category"]=="Profit ($)", "Value"].iloc[0]
    ]
    actual_vals = [
        revenue_df["Consolidated"].iloc[-1],
        cogs_df["COGS"].iloc[-1],
        expenses_df["Total"].iloc[-1],
        profit_df["Profit $"].iloc[-1]
    ]
    budget_fig.add_trace(go.Bar(x=["Revenue", "COGS", "Expenses", "Profit"], y=budget_vals, name="Budget", marker_color="#9467bd"))
    budget_fig.add_trace(go.Bar(x=["Revenue", "COGS", "Expenses", "Profit"], y=actual_vals, name="Actual", marker_color="#1f77b4"))
    budget_fig.update_layout(
        title="Budget vs Actual (Latest Year)",
        barmode="group",
        yaxis=dict(title="Amount ($)", tickformat="$,.0f"),
        template="plotly_white", hovermode="x unified", height=400
    )

    # 6. 资产负债表环形图
    bs_fig = px.pie(
        balance_sheet_df, values="Value", names="Category",
        title="Balance Sheet Structure (Latest Year)",
        hole=0.4,
        hover_data={"Value": ":,.0f"},
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]
    )
    bs_fig.update_traces(textinfo="label+percent")
    bs_fig.update_layout(template="plotly_white", height=400)

    # 7. CAGR雷达图
    rev = revenue_df[["Business 1", "Business 2", "Business 3"]]
    cagr = (rev.iloc[-1] / rev.iloc[0]) ** (1/4) - 1
    if selected_bu != "all":
        radar_fig = px.line_polar(
            r=[cagr[selected_bu]*100], theta=[selected_bu],
            title=f"{selected_bu} 5-Year CAGR",
            line_close=True,
            color_discrete_sequence=["#2ca02c"]
        )
    else:
        radar_fig = px.line_polar(
            r=[cagr["Business 1"]*100, cagr["Business 2"]*100, cagr["Business 3"]*100],
            theta=["Business 1", "Business 2", "Business 3"],
            title="5-Year CAGR by Business Unit",
            line_close=True,
            color_discrete_sequence=["#2ca02c"]
        )
    radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, title="CAGR (%)")),
        template="plotly_white", height=400
    )

    # 8. 成本结构线图
    cost_pct = pd.DataFrame({
        "Year": filtered_rev["Year"],
        "COGS %": filtered_cogs["COGS"] / filtered_rev["Consolidated"] * 100,
        "Salaries %": filtered_exp["Salaries"] / filtered_rev["Consolidated"] * 100,
        "Rent %": filtered_exp["Rent"] / filtered_rev["Consolidated"] * 100,
    })
    cost_fig = px.line(
        cost_pct, x="Year", y=["COGS %", "Salaries %", "Rent %"],
        title="Cost Structure as % of Revenue",
        labels={"value": "% of Revenue", "variable": "Cost Type"},
        hover_data={"value": ":,.1f"},
        markers=True
    )
    cost_fig.update_layout(hovermode="x unified", template="plotly_white", height=400)

    return rev_fig, profit_fig, rev_dist_fig, exp_fig, budget_fig, bs_fig, radar_fig, cost_fig

# ---------------------- 运行入口 ----------------------
if __name__ == "__main__":
    app.run(debug=False)
