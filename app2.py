import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback  # 保持与你之前版本一致的导入

# ---------------------- 初始化应用（与你原始版本保持一致，确保WSGI兼容） ----------------------
app = Dash(__name__)
server = app.server  # 维持WSGI调用的兼容性

# ---------------------- 读取数据（路径与你原始dashboard一致，确保能找到CSV） ----------------------
# 假设你的CSV文件与app.py在同一目录，与你之前的版本路径相同
revenue_df = pd.read_csv("revenue_df.csv")
cogs_df = pd.read_csv("cogs_df.csv")
profit_df = pd.read_csv("profit_df.csv")
expenses_df = pd.read_csv("expenses_df.csv")
budget_df = pd.read_csv("budget_df.csv")
balance_sheet_df = pd.read_csv("balance_sheet_df.csv")

# ---------------------- 应用布局（简化但保持与你原始dashboard的结构兼容） ----------------------
app.layout = html.Div([
    html.H1("Financial Analytics Dashboard", style={"textAlign": "center", "margin": "20px 0"}),
    
    # 筛选器（保留简单交互，不引入复杂功能）
    html.Div([
        html.Div([
            html.Label("Select Year:"),
            dcc.Dropdown(
                id="year-filter",
                options=[{"label": str(y), "value": y} for y in revenue_df["Year"].unique()],
                value=revenue_df["Year"].max(),  # 默认最新年份
                style={"width": "200px"}
            )
        ], style={"display": "inline-block", "marginRight": "30px", "marginLeft": "40px"}),
        
        html.Div([
            html.Label("Business Unit:"),
            dcc.Dropdown(
                id="bu-filter",
                options=[{"label": bu, "value": bu} for bu in ["Business 1", "Business 2", "Business 3", "All"]],
                value="All",
                style={"width": "200px"}
            )
        ], style={"display": "inline-block"})
    ], style={"margin": "20px 0"}),
    
    # 图表区域（与你原始dashboard的布局逻辑一致）
    html.Div([
        # 第一行
        html.Div([
            html.Div([dcc.Graph(id="revenue-trend")], style={"width": "50%", "display": "inline-block"}),
            html.Div([dcc.Graph(id="profit-margin")], style={"width": "50%", "display": "inline-block"})
        ]),
        
        # 第二行
        html.Div([
            html.Div([dcc.Graph(id="revenue-dist")], style={"width": "50%", "display": "inline-block"}),
            html.Div([dcc.Graph(id="expenses-chart")], style={"width": "50%", "display": "inline-block"})
        ]),
        
        # 第三行
        html.Div([
            html.Div([dcc.Graph(id="budget-vs-actual")], style={"width": "50%", "display": "inline-block"}),
            html.Div([dcc.Graph(id="cagr-radar")], style={"width": "50%", "display": "inline-block"})
        ])
    ])
])

# ---------------------- 回调函数（修复核心错误，保持返回格式与原始版本兼容） ----------------------
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
    # 1. 收入趋势图（修复数据筛选逻辑）
    if selected_bu != "All":
        rev_fig = px.line(
            revenue_df, x="Year", y=selected_bu,
            title=f"{selected_bu} Revenue Trend",
            labels={selected_bu: "Revenue ($)"},
            template="plotly_white"
        )
    else:
        rev_fig = px.line(
            revenue_df, x="Year", y=["Business 1", "Business 2", "Business 3"],
            title="All Units Revenue Trend",
            labels={"value": "Revenue ($)", "variable": "Unit"},
            template="plotly_white"
        )
    rev_fig.update_yaxes(tickprefix="$", tickformat=",")  # 保持与你原始图表的格式一致

    # 2. 利润率图（修复索引方式，用iloc避免警告）
    profit_data = profit_df[profit_df["Year"] == selected_year].iloc[0]  # 关键修复：用iloc[0]替代[0]
    profit_fig = go.Figure()
    profit_fig.add_trace(go.Bar(
        x=[selected_year], y=[profit_data["Profit $"]],
        name="Profit ($)", marker_color="green"
    ))
    profit_fig.update_layout(
        title=f"Profit Margin ({selected_year})",
        yaxis=dict(tickprefix="$", tickformat=","),
        template="plotly_white"
    )

    # 3. 收入分布饼图（修复数据提取逻辑）
    rev_dist_data = revenue_df[revenue_df["Year"] == selected_year].iloc[0]  # 修复索引
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

    # 4. 费用分析图（保持与原始版本的图表类型一致）
    exp_data = expenses_df[expenses_df["Year"] == selected_year].iloc[0]  # 修复索引
    exp_fig = px.bar(
        x=["Salaries", "Rent", "D&A", "Interest"],
        y=[exp_data["Salaries"], exp_data["Rent"], exp_data["D&A"], exp_data["Interest"]],
        title=f"Expenses Breakdown ({selected_year})",
        labels={"y": "Amount ($)", "x": "Expense Type"},
        template="plotly_white"
    )
    exp_fig.update_yaxes(tickprefix="$", tickformat=",")

    # 5. 预算vs实际（修复数据匹配逻辑）
    budget_data = budget_df[budget_df["Year"] == selected_year].iloc[0]  # 修复索引
    actual_data = {
        "Revenue": revenue_df[revenue_df["Year"] == selected_year]["Consolidated"].iloc[0],
        "COGS": cogs_df[cogs_df["Year"] == selected_year]["COGS"].iloc[0],
        "Expenses": expenses_df[expenses_df["Year"] == selected_year]["Total"].iloc[0]
    }
    budget_fig = go.Figure()
    budget_fig.add_trace(go.Bar(x=["Revenue", "COGS", "Expenses"], y=[budget_data["Revenue"], budget_data["COGS"], budget_data["Expenses"]], name="Budget"))
    budget_fig.add_trace(go.Bar(x=["Revenue", "COGS", "Expenses"], y=[actual_data["Revenue"], actual_data["COGS"], actual_data["Expenses"]], name="Actual"))
    budget_fig.update_layout(barmode="group", template="plotly_white", title=f"Budget vs Actual ({selected_year})")
    budget_fig.update_yaxes(tickprefix="$", tickformat=",")

    # 6. CAGR雷达图（彻底修复核心错误：不依赖数据框列名，直接传值）
    start_year = revenue_df["Year"].min()
    end_year = revenue_df["Year"].max()
    years = end_year - start_year
    cagr_list = []
    labels = []
    for bu in ["Business 1", "Business 2", "Business 3"]:
        if selected_bu == "All" or bu == selected_bu:
            start_val = revenue_df[revenue_df["Year"] == start_year][bu].iloc[0]  # 修复索引
            end_val = revenue_df[revenue_df["Year"] == end_year][bu].iloc[0]
            cagr = ((end_val / start_val) ** (1/years) - 1) * 100  # 计算为百分比
            cagr_list.append(cagr)
            labels.append(bu)
    # 生成雷达图（直接用列表传参，避免列名错误）
    radar_fig = px.line_polar(
        r=cagr_list, theta=labels, line_close=True,
        title=f"CAGR ({start_year}-{end_year})",
        template="plotly_white"
    )
    radar_fig.update_polars(radialaxis_title="CAGR (%)")

    # 确保返回值格式与原始版本一致（6个图表对象的列表）
    return rev_fig, profit_fig, dist_fig, exp_fig, budget_fig, radar_fig

# ---------------------- 运行入口（与你原始版本一致，确保WSGI能正确调用） ----------------------
if __name__ == "__main__":
    app.run_server(debug=False)  # 关闭debug，与生产环境一致
