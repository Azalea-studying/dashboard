import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback, no_update
import numpy as np
import base64
import io

# ---------------------- 初始化Dash应用 ----------------------
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # 暴露Flask服务

# ---------------------- 读取示例数据 ----------------------
# （保持原数据读取逻辑，用于默认展示）
revenue_df = pd.read_csv("revenue_df.csv")
cogs_df = pd.read_csv("cogs_df.csv")
profit_df = pd.read_csv("profit_df.csv")
expenses_df = pd.read_csv("expenses_df.csv")
budget_df = pd.read_csv("budget_df.csv")
balance_sheet_df = pd.read_csv("balance_sheet_df.csv")

# ---------------------- 通用图表函数（支持动态数据输入） ----------------------
def business_unit_revenue_fig(data):
    """1. 业务单元收入（堆叠面积图）"""
    fig = px.area(
        data, x="Year", y=["Business 1", "Business 2", "Business 3"],
        title="Business Unit Revenue Trend",
        labels={"value": "Revenue ($)", "variable": "Business Unit"},
        hover_data={"value": ":,.0f"},
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]
    )
    fig.update_layout(hovermode="x unified", template="plotly_white", height=400)
    return fig

def profit_margin_fig(data):
    """2. 利润率（双y轴图：柱状图+线图）"""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data["Year"], y=data["Profit $"], name="Profit ($)",
        hovertemplate="Year: %{x}<br>Profit: $%{y:,.0f}",
        marker_color="#2ca02c"
    ))
    fig.add_trace(go.Scatter(
        x=data["Year"], y=data["Profit %"], name="Profit (%)",
        mode="lines+markers", line=dict(color="#ff7f0e", width=3),
        yaxis="y2", hovertemplate="Year: %{x}<br>Profit %: %{y}%"
    ))
    fig.update_layout(
        title="Profit Margin Analysis",
        yaxis=dict(title="Profit ($)", tickformat="$,.0f"),
        yaxis2=dict(title="Profit (%)", overlaying="y", side="right"),
        template="plotly_white", hovermode="x unified", height=400
    )
    return fig

def cumulative_revenue_fig(data):
    """3. 累计收入（饼图替换柱状图）"""
    temp_df = pd.DataFrame({
        "Business": ["Business 1", "Business 2", "Business 3", "Consolidated"],
        "Revenue": [
            data["Business 1"].iloc[-1],
            data["Business 2"].iloc[-1],
            data["Business 3"].iloc[-1],
            data["Consolidated"].iloc[-1]
        ]
    })
    # 饼图：更适合展示占比关系
    fig = px.pie(
        temp_df, values="Revenue", names="Business",
        title="Cumulative Revenue Distribution (Latest Year)",
        hole=0.3,  # 环形图效果
        hover_data={"Revenue": ":,.0f"},
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c", "#000066"]
    )
    fig.update_traces(textinfo="percent+label")  # 显示百分比和标签
    fig.update_layout(template="plotly_white", height=400)
    return fig

def expenses_trend_fig(data):
    """4. 费用趋势（堆叠面积图）"""
    fig = px.area(
        data, x="Year", y=["Salaries", "Rent", "D&A", "Interest"],
        title="Expenses Trend Over Time",
        labels={"value": "Expense ($)", "variable": "Expense Type"},
        hover_data={"value": ":,.0f"},
        color_discrete_sequence=["#d62728", "#9467bd", "#8c564b", "#e377c2"]
    )
    fig.update_layout(hovermode="x unified", template="plotly_white", height=400)
    return fig

def budget_vs_actual_fig(budget_data, actual_rev, actual_cogs, actual_exp, actual_profit):
    """5. 预算vs实际（保留分组柱状图，适合对比）"""
    labels = ["Revenue", "COGS", "Expenses", "Profit"]
    budget_vals = [
        budget_data.loc[budget_data["Category"]=="Revenue", "Value"].iloc[0],
        budget_data.loc[budget_data["Category"]=="COGS", "Value"].iloc[0],
        budget_data.loc[budget_data["Category"]=="Expenses", "Value"].iloc[0],
        budget_data.loc[budget_data["Category"]=="Profit ($)", "Value"].iloc[0]
    ]
    actual_vals = [
        actual_rev, actual_cogs, actual_exp, actual_profit
    ]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=budget_vals, name="Budget", marker_color="#9467bd"))
    fig.add_trace(go.Bar(x=labels, y=actual_vals, name="Actual", marker_color="#1f77b4"))
    fig.update_layout(
        title="Budget vs Actual Comparison",
        barmode="group",
        yaxis=dict(title="Amount ($)", tickformat="$,.0f"),
        template="plotly_white",
        hovermode="x unified",
        height=400
    )
    return fig

def balance_sheet_fig(data):
    """6. 资产负债表（环形图替换柱状图）"""
    # 扩展数据：包含资产、负债和权益
    temp_df = pd.DataFrame({
        "Category": data["Category"],
        "Value": data["Value"]
    })
    # 环形图：适合展示整体结构
    fig = px.pie(
        temp_df, values="Value", names="Category",
        title="Balance Sheet Structure (Latest Year)",
        hole=0.4,
        hover_data={"Value": ":,.0f"},
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]
    )
    fig.update_traces(textinfo="label+percent")
    fig.update_layout(template="plotly_white", height=400)
    return fig

def cagr_fig(data):
    """7. 业务单元CAGR（雷达图替换柱状图）"""
    rev = data[["Business 1", "Business 2", "Business 3"]]
    cagr = (rev.iloc[-1] / rev.iloc[0]) ** (1/4) - 1  # 4年CAGR
    # 雷达图数据格式
    radar_data = pd.DataFrame({
        "Metric": ["CAGR (%)"],
        "Business 1": [cagr[0]*100],
        "Business 2": [cagr[1]*100],
        "Business 3": [cagr[2]*100]
    })
    fig = px.line_polar(
        radar_data, r="CAGR (%)", theta=["Business 1", "Business 2", "Business 3"],
        line_close=True, title="5-Year CAGR by Business Unit",
        color_discrete_sequence=["#2ca02c"]
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, title="CAGR (%)")),
        template="plotly_white", height=400
    )
    return fig

def cost_structure_pct_fig(rev_data, cogs_data, exp_data):
    """8. 成本占收入比例（线图保留，适合趋势）"""
    cost_pct = pd.DataFrame({
        "Year": rev_data["Year"],
        "COGS %": cogs_data["COGS"] / rev_data["Consolidated"] * 100,
        "Salaries %": exp_data["Salaries"] / rev_data["Consolidated"] * 100,
        "Rent %": exp_data["Rent"] / rev_data["Consolidated"] * 100,
    })
    fig = px.line(
        cost_pct, x="Year", y=["COGS %", "Salaries %", "Rent %"],
        title="Cost Structure as % of Revenue",
        labels={"value": "% of Revenue", "variable": "Cost Type"},
        hover_data={"value": ":,.1f"},
        markers=True
    )
    fig.update_layout(hovermode="x unified", template="plotly_white", height=400)
    return fig

# ---------------------- 应用布局 ----------------------
app.layout = html.Div([
    # 标题和说明
    html.Div([
        html.H1("Financial Analytics Dashboard", style={"textAlign": "center", "margin": "20px 0"}),
        html.P(
            "Upload your company's financial data (CSV files) to generate customized analytics. "
            "Use the tabs below to switch between sample data and your uploaded data.",
            style={"textAlign": "center", "fontSize": 16, "marginBottom": "30px", "maxWidth": "800px", "margin": "0 auto"}
        )
    ]),

    # 文件上传区域
    html.Div([
        html.H3("Upload Your Financial Data", style={"textAlign": "center", "margin": "20px 0"}),
        dcc.Upload(
            id="upload-data",
            children=html.Div([
                "Drag and drop or click to select CSV files. Required files: ",
                html.Strong("revenue, cogs, profit, expenses, budget, balance_sheet")
            ]),
            style={
                "width": "80%",
                "height": "100px",
                "lineHeight": "100px",
                "borderWidth": "2px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "0 auto 30px auto",
                "padding": "10px"
            },
            multiple=True  # 允许同时上传多个文件
        ),
        html.P(
            "Data format guide: Each CSV should have columns matching the sample data. "
            "Year columns must include 'Year -4' to 'Year 0'.",
            style={"textAlign": "center", "fontSize": 14, "color": "#666", "marginBottom": "30px"}
        ),
        html.Div(id="upload-status", style={"textAlign": "center", "marginBottom": "20px"})
    ]),

    # 标签页：切换示例数据和用户数据
    dcc.Tabs(id="data-tabs", value="sample-tab", children=[
        dcc.Tab(label="Sample Data Dashboard", value="sample-tab"),
        dcc.Tab(label="Your Uploaded Data", value="user-tab")
    ]),

    # 图表内容区域
    html.Div(id="dashboard-content", style={"padding": "20px"})
])

# ---------------------- 回调函数：处理文件上传 ----------------------
@callback(
    Output("upload-status", "children"),
    Output("dashboard-content", "children"),
    Input("upload-data", "contents"),
    Input("data-tabs", "value"),
    State("upload-data", "filename"),
    prevent_initial_call=True
)
def update_dashboard(contents, active_tab, filenames):
    # 1. 示例数据标签页
    if active_tab == "sample-tab":
        return (
            "Viewing sample data. Upload your files and switch to 'Your Uploaded Data' tab to use your data.",
            html.Div([
                # 第一行
                html.Div([
                    html.Div([dcc.Graph(figure=business_unit_revenue_fig(revenue_df))], style={"width": "50%", "display": "inline-block"}),
                    html.Div([dcc.Graph(figure=profit_margin_fig(profit_df))], style={"width": "50%", "display": "inline-block"})
                ], style={"marginBottom": "30px"}),
                # 第二行
                html.Div([
                    html.Div([dcc.Graph(figure=cumulative_revenue_fig(revenue_df))], style={"width": "50%", "display": "inline-block"}),
                    html.Div([dcc.Graph(figure=expenses_trend_fig(expenses_df))], style={"width": "50%", "display": "inline-block"})
                ], style={"marginBottom": "30px"}),
                # 第三行
                html.Div([
                    html.Div([dcc.Graph(
                        figure=budget_vs_actual_fig(
                            budget_df,
                            revenue_df["Consolidated"].iloc[-1],
                            cogs_df["COGS"].iloc[-1],
                            expenses_df["Total"].iloc[-1],
                            profit_df["Profit $"].iloc[-1]
                        ))], style={"width": "50%", "display": "inline-block"}),
                    html.Div([dcc.Graph(figure=balance_sheet_fig(balance_sheet_df))], style={"width": "50%", "display": "inline-block"})
                ], style={"marginBottom": "30px"}),
                # 第四行
                html.Div([
                    html.Div([dcc.Graph(figure=cagr_fig(revenue_df))], style={"width": "50%", "display": "inline-block"}),
                    html.Div([dcc.Graph(
                        figure=cost_structure_pct_fig(revenue_df, cogs_df, expenses_df))], 
                        style={"width": "50%", "display": "inline-block"})
                ])
            ])
        )
    
    #
