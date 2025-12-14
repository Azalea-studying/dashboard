import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback

# 初始化应用
app = Dash(__name__)
server = app.server

# ---------------------- 读取数据（增加容错处理） ----------------------
# 确保CSV文件与app.py在同一目录，且列名正确（根据你的原始数据调整）
try:
    revenue_df = pd.read_csv("revenue_df.csv")
    cogs_df = pd.read_csv("cogs_df.csv")
    profit_df = pd.read_csv("profit_df.csv")
    expenses_df = pd.read_csv("expenses_df.csv")
    budget_df = pd.read_csv("budget_df.csv")
    # 打印列名，帮助确认数据结构（部署时可删除）
    print("Revenue columns:", revenue_df.columns.tolist())
except Exception as e:
    print("数据读取错误：", e)
    # 若读取失败，创建示例数据避免崩溃（仅用于测试）
    revenue_df = pd.DataFrame({
        "Year": [2020, 2021, 2022, 2023, 2024],
        "Business 1": [100, 200, 300, 400, 500],
        "Business 2": [150, 250, 350, 450, 550],
        "Business 3": [200, 300, 400, 500, 600],
        "Consolidated": [450, 750, 1050, 1350, 1650]
    })
    cogs_df = pd.DataFrame({"Year": [2020,2021,2022,2023,2024], "COGS": [200, 300, 400, 500, 600]})
    profit_df = pd.DataFrame({"Year": [2020,2021,2022,2023,2024], "Profit $": [250, 450, 650, 850, 1050], "Profit %": [55, 60, 62, 64, 65]})
    expenses_df = pd.DataFrame({"Year": [2020,2021,2022,2023,2024], "Salaries": [100,120,140,160,180], "Rent": [50,60,70,80,90], "D&A": [30,40,50,60,70], "Interest": [20,30,40,50,60], "Total": [200,250,300,350,400]})
    budget_df = pd.DataFrame({"Year": [2020,2021,2022,2023,2024], "Revenue": [400,700,1000,1300,1600], "COGS": [180,280,380,480,580], "Expenses": [180,230,280,330,380]})

# ---------------------- 应用布局 ----------------------
app.layout = html.Div([
    html.H1("Financial Analytics Dashboard", style={"textAlign": "center"}),
    
    # 筛选器
    html.Div([
        html.Div([
            html.Label("Select Year:"),
            dcc.Dropdown(
                id="year-filter",
                options=[{"label": str(y), "value": y} for y in revenue_df["Year"].unique()],
                value=revenue_df["Year"].max(),
                style={"width": "200px"}
            )
        ], style={"display": "inline-block", "margin": "0 20px"}),
        
        html.Div([
            html.Label("Business Unit:"),
            dcc.Dropdown(
                id="bu-filter",
                options=[{"label": bu, "value": bu} for bu in ["Business 1", "Business 2", "Business 3", "All"]],
                value="All",
                style={"width": "200px"}
            )
        ], style={"display": "inline-block"})
    ], style={"textAlign": "center", "margin": "20px 0"}),
    
    # 图表区域
    html.Div([
        html.Div([dcc.Graph(id="revenue-trend")], style={"width": "50%", "display": "inline-block"}),
        html.Div([dcc.Graph(id="profit-margin")], style={"width": "50%", "display": "inline-block"}),
        html.Div([dcc.Graph(id="revenue-dist")], style={"width": "50%", "display": "inline-block"}),
        html.Div([dcc.Graph(id="expenses-chart")], style={"width": "50%", "display": "inline-block"}),
        html.Div([dcc.Graph(id="budget-vs-actual")], style={"width": "50%", "display": "inline-block"}),
        html.Div([dcc.Graph(id="cagr-radar")], style={"width": "50%", "display": "inline-block"})
    ])
])

# ---------------------- 回调函数（增加数据校验） ----------------------
@callback(
    [Output("revenue-trend", "figure"),
     Output("profit-margin", "figure"),
     Output("revenue-dist", "figure"),
     Output("expenses-chart", "figure"),
     Output("budget-vs-actual", "figure"),
     Output("cagr-radar", "figure")],
    [Input("year-filter", "value"),
     Input("bu-filter", "value")]
)
def update_charts(selected_year, selected_bu):
    # 校验选中年份是否存在
    if selected_year not in revenue_df["Year"].values:
        empty_fig = go.Figure().update_layout(title="无数据：年份不存在")
        return [empty_fig]*6  # 所有图表返回空提示
    
    # 1. 收入趋势图
    if selected_bu != "All":
        # 校验业务单元列是否存在
        if selected_bu not in revenue_df.columns:
            rev_fig = go.Figure().update_layout(title=f"无数据：{selected_bu}不存在")
        else:
            rev_fig = px.line(
                revenue_df, x="Year", y=selected_bu,
                title=f"{selected_bu} Revenue Trend",
                labels={selected_bu: "Revenue ($)"},
                template="plotly_white"
            )
            rev_fig.update_yaxes(tickprefix="$", tickformat=",")
    else:
        rev_fig = px.line(
            revenue_df, x="Year", y=["Business 1", "Business 2", "Business 3"],
            title="All Units Revenue Trend",
            labels={"value": "Revenue ($)", "variable": "Unit"},
            template="plotly_white"
        )
        rev_fig.update_yaxes(tickprefix="$", tickformat=",")
    
    # 2. 利润率图
    profit_data = profit_df[profit_df["Year"] == selected_year].iloc[0]
    profit_fig = go.Figure(go.Bar(
        x=[selected_year], y=[profit_data["Profit $"]],
        name="Profit ($)", marker_color="green"
    ))
    profit_fig.update_layout(
        title=f"Profit ({selected_year}): ${profit_data['Profit $']:,}",
        yaxis=dict(tickprefix="$", tickformat=","),
        template="plotly_white"
    )
    
    # 3. 收入分布饼图
    rev_dist_data = revenue_df[revenue_df["Year"] == selected_year].iloc[0]
    if selected_bu == "All":
        dist_labels = ["Business 1", "Business 2", "Business 3"]
        dist_values = [rev_dist_data["Business 1"], rev_dist_data["Business 2"], rev_dist_data["Business 3"]]
    else:
        dist_labels = [selected_bu]
        dist_values = [rev_dist_data[selected_bu]]
    dist_fig = px.pie(
        values=dist_values, names=dist_labels,
        title=f"Revenue Distribution ({selected_year})",
        hole=0.3, template="plotly_white"
    )
    
    # 4. 费用分析图
    exp_data = expenses_df[expenses_df["Year"] == selected_year].iloc[0]
    exp_fig = px.bar(
        x=["Salaries", "Rent", "D&A", "Interest"],
        y=[exp_data["Salaries"], exp_data["Rent"], exp_data["D&A"], exp_data["Interest"]],
        title=f"Expenses ({selected_year})",
        labels={"y": "Amount ($)", "x": "Type"},
        template="plotly_white"
    )
    exp_fig.update_yaxes(tickprefix="$", tickformat=",")
    
    # 5. 预算vs实际
    budget_data = budget_df[budget_df["Year"] == selected_year].iloc[0]
    actual_data = {
        "Revenue": revenue_df[revenue_df["Year"] == selected_year]["Consolidated"].iloc[0],
        "COGS": cogs_df[cogs_df["Year"] == selected_year]["COGS"].iloc[0],
        "Expenses": expenses_df[expenses_df["Year"] == selected_year]["Total"].iloc[0]
    }
    budget_fig = go.Figure()
    budget_fig.add_trace(go.Bar(x=["Revenue", "COGS", "Expenses"], y=[budget_data["Revenue"], budget_data["COGS"], budget_data["Expenses"]], name="Budget"))
    budget_fig.add_trace(go.Bar(x=["Revenue", "COGS", "Expenses"], y=[actual_data["Revenue"], actual_data["COGS"], actual_data["Expenses"]], name="Actual"))
    budget_fig.update_layout(barmode="group", title=f"Budget vs Actual ({selected_year})", template="plotly_white")
    budget_fig.update_yaxes(tickprefix="$", tickformat=",")
    
    # 6. CAGR雷达图
    start_year = revenue_df["Year"].min()
    end_year = revenue_df["Year"].max()
    years = end_year - start_year
    cagr_list = []
    labels = []
    for bu in ["Business 1", "Business 2", "Business 3"]:
        if (selected_bu == "All" or bu == selected_bu) and bu in revenue_df.columns:
            start_val = revenue_df[revenue_df["Year"] == start_year][bu].iloc[0]
            end_val = revenue_df[revenue_df["Year"] == end_year][bu].iloc[0]
            if start_val > 0:  # 避免除以0
                cagr = ((end_val / start_val) ** (1/years) - 1) * 100
                cagr_list.append(round(cagr, 2))
                labels.append(bu)
    radar_fig = px.line_polar(
        r=cagr_list, theta=labels, line_close=True,
        title=f"CAGR ({start_year}-{end_year}) (%)",
        template="plotly_white"
    )
    radar_fig.update_polars(radialaxis_title="CAGR (%)")
    
    return rev_fig, profit_fig, dist_fig, exp_fig, budget_fig, radar_fig

# ---------------------- 运行入口（根据环境选择） ----------------------
if __name__ == "__main__":
    # Colab测试用：app.run(debug=False)
    # PythonAnywhere部署用：app.run_server(debug=False)
    app.run_server(debug=False)
