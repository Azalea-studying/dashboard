import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html
import numpy as np

# ---------------------- 初始化Dash+Flask应用 ----------------------
app = Dash(__name__)
server = app.server  # 暴露Flask服务，供PythonAnywhere部署

# ---------------------- 读取数据 ----------------------
revenue_df = pd.read_csv("revenue_df.csv")
cogs_df = pd.read_csv("cogs_df.csv")
profit_df = pd.read_csv("profit_df.csv")
expenses_df = pd.read_csv("expenses_df.csv")
budget_df = pd.read_csv("budget_df.csv")
balance_sheet_df = pd.read_csv("balance_sheet_df.csv")

# ---------------------- 定义交互式图表函数 ----------------------
def business_unit_revenue_fig():
    """1. 业务单元收入（堆叠面积图）"""
    fig = px.area(
        revenue_df, x="Year", y=["Business 1", "Business 2", "Business 3"],
        title="Business Unit Revenue",
        labels={"value": "Revenue ($)", "variable": "Business Unit"},
        hover_data={"value": ":,.0f"},
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]
    )
    fig.update_layout(hovermode="x unified", template="plotly_white", height=400)
    return fig

def profit_margin_fig():
    """2. 利润率（双轴图：柱状图+线图）"""
    fig = go.Figure()
    # 利润金额（柱状图）
    fig.add_trace(go.Bar(
        x=profit_df["Year"], y=profit_df["Profit $"], name="Profit ($)",
        hovertemplate="Year: %{x}<br>Profit: $%{y:,.0f}",
        marker_color="#2ca02c"
    ))
    # 利润率（线图，右侧y轴）
    fig.add_trace(go.Scatter(
        x=profit_df["Year"], y=profit_df["Profit %"], name="Profit (%)",
        mode="lines+markers", line=dict(color="#ff7f0e", width=3),
        yaxis="y2", hovertemplate="Year: %{x}<br>Profit %: %{y}%"
    ))
    # 配置双轴和样式（正确语法）
    fig.update_layout(
        title="Profit Margin",
        yaxis=dict(title="Profit ($)", tickformat="$,.0f"),
        yaxis2=dict(title="Profit (%)", overlaying="y", side="right"),
        template="plotly_white", hovermode="x unified", height=400
    )
    return fig

def cumulative_revenue_fig():
    """3. 累计收入（Year 0）"""
    temp_df = pd.DataFrame({
        "Business": ["Business 1", "Business 2", "Business 3", "Consolidated"],
        "Revenue": [
            revenue_df["Business 1"].iloc[-1],
            revenue_df["Business 2"].iloc[-1],
            revenue_df["Business 3"].iloc[-1],
            revenue_df["Consolidated"].iloc[-1]
        ]
    })
    fig = px.bar(
        temp_df, x="Business", y="Revenue",
        title="Cumulative Revenue (Year 0)",
        labels={"Revenue": "Revenue ($)"},
        color="Business", 
        color_discrete_sequence=["#bbbbbb", "#888888", "#555555", "#000066"],
        hover_data={"Revenue": ":,.0f"}
    )
    fig.update_layout(template="plotly_white", height=400, showlegend=False)
    return fig

def expenses_trend_fig():
    """4. 费用趋势（堆叠面积图）"""
    fig = px.area(
        expenses_df, x="Year",
        y=["Salaries", "Rent", "D&A", "Interest"],
        title="Expenses Trend",
        labels={"value": "Expense ($)", "variable": "Expense Type"},
        hover_data={"value": ":,.0f"},
        color_discrete_sequence=["#d62728", "#9467bd", "#8c564b", "#e377c2"]
    )
    fig.update_layout(hovermode="x unified", template="plotly_white", height=400)
    return fig

def budget_vs_actual_fig():
    """5. 预算vs实际（Year 0）- 修复labels参数错误"""
    labels = ["Revenue", "COGS", "Expenses", "Profit"]
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
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=budget_vals, name="Budget", marker_color="#9467bd"))
    fig.add_trace(go.Bar(x=labels, y=actual_vals, name="Actual", marker_color="#1f77b4"))
    # 正确配置：用yaxis.title替代labels={"y": ...}
    fig.update_layout(
        title="Budget vs Actual (Year 0)",
        barmode="group",
        yaxis=dict(title="Amount ($)", tickformat="$,.0f"),  # 修复核心
        template="plotly_white",
        hovermode="x unified",
        height=400
    )
    return fig

def balance_sheet_fig():
    """6. 资产负债表摘要 - 修复hover_data语法"""
    # 创建临时DataFrame（避免数组传参问题）
    temp_bs_df = pd.DataFrame({
        "Asset Type": ["Current Assets", "Non-current Assets"],
        "Value": balance_sheet_df.iloc[0:2]["Value"].values
    })
    fig = px.bar(
        temp_bs_df, x="Asset Type", y="Value",
        title="Balance Sheet Summary (Year 0)",
        labels={"Value": "Amount ($)"},
        color_discrete_sequence=["#1f77b4", "#ff7f0e"],
        hover_data={"Value": ":,.0f"}
    )
    fig.update_layout(template="plotly_white", height=400)
    return fig

def cagr_fig():
    """7. 业务单元CAGR"""
    rev = revenue_df[["Business 1", "Business 2", "Business 3"]]
    cagr = (rev.iloc[-1] / rev.iloc[0]) ** (1/4) - 1  # 4年CAGR
    cagr_df = pd.DataFrame({"Business Unit": rev.columns, "CAGR (%)": cagr*100})
    fig = px.bar(
        cagr_df, x="Business Unit", y="CAGR (%)",
        title="5-Year CAGR by Business Unit",
        color_discrete_sequence=["#2ca02c"],
        hover_data={"CAGR (%)": ":,.2f"}
    )
    fig.update_layout(template="plotly_white", height=400)
    return fig

def cost_structure_pct_fig():
    """8. 成本占收入比例"""
    cost_pct = pd.DataFrame({
        "Year": ["Year -4", "Year -3", "Year -2", "Year -1", "Year 0"],
        "COGS %": cogs_df["COGS"] / revenue_df["Consolidated"] * 100,
        "Salaries %": expenses_df["Salaries"] / revenue_df["Consolidated"] * 100,
        "Rent %": expenses_df["Rent"] / revenue_df["Consolidated"] * 100,
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

# ---------------------- 应用布局（网页结构） ----------------------
app.layout = html.Div([
    # 标题
    html.H1("Financial Dashboard", style={"textAlign": "center", "margin": "20px 0"}),
    
    # 第一行：2个图表（分栏）
    html.Div([
        html.Div([dcc.Graph(figure=business_unit_revenue_fig())], style={"width": "50%", "display": "inline-block"}),
        html.Div([dcc.Graph(figure=profit_margin_fig())], style={"width": "50%", "display": "inline-block"})
    ], style={"marginBottom": "30px"}),
    
    # 第二行：2个图表
    html.Div([
        html.Div([dcc.Graph(figure=cumulative_revenue_fig())], style={"width": "50%", "display": "inline-block"}),
        html.Div([dcc.Graph(figure=expenses_trend_fig())], style={"width": "50%", "display": "inline-block"})
    ], style={"marginBottom": "30px"}),
    
    # 第三行：2个图表
    html.Div([
        html.Div([dcc.Graph(figure=budget_vs_actual_fig())], style={"width": "50%", "display": "inline-block"}),
        html.Div([dcc.Graph(figure=balance_sheet_fig())], style={"width": "50%", "display": "inline-block"})
    ], style={"marginBottom": "30px"}),
    
    # 第四行：2个图表
    html.Div([
        html.Div([dcc.Graph(figure=cagr_fig())], style={"width": "50%", "display": "inline-block"}),
        html.Div([dcc.Graph(figure=cost_structure_pct_fig())], style={"width": "50%", "display": "inline-block"})
    ])
], style={"padding": "20px"})

# ---------------------- 本地运行入口（修复Dash语法） ----------------------
if __name__ == "__main__":
    app.run(debug=False)  # 关键修改：run_server → run
