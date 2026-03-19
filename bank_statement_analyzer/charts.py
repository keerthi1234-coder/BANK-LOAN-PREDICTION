import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from collections import Counter
import pandas as pd
import re

def create_chart_data(transactions, eligibility, overall_transaction):
    # print("transactions",transactions)
    """
    Process transaction data to create chart-friendly data structures
    """
    # Process balance trend data
    balance_data = {
        'labels': [],
        'values': []
    }

    for transaction in transactions:
        # Convert numpy.datetime64 to Python datetime and then format the date
        if isinstance(transaction['Balance'], (int, float)):
            date_obj = transaction['Date']
            if isinstance(date_obj, np.datetime64):
                # Convert numpy.datetime64 to a Python datetime object
                date_obj = pd.to_datetime(date_obj).to_pydatetime()
            balance_data['labels'].append(date_obj.strftime("%d-%b"))
            balance_data['values'].append(float(transaction['Balance']))

    # Process financial metrics data
    financial_metrics = {
        'labels': ['Total Credits', 'Total Debits', 'Avg Monthly Income', 'Avg Monthly Expenses'],
        'values': [
            float(overall_transaction['Credit']),
            float(overall_transaction['Debit']),
            float(eligibility['Average Monthly Income']),
            float(eligibility['Average Monthly Expenses'])
        ],
        'colors': [
            'rgba(75, 192, 192, 0.7)',   # Teal
            'rgba(255, 99, 132, 0.7)',   # Pink
            'rgba(54, 162, 235, 0.7)',   # Blue
            'rgba(255, 159, 64, 0.7)'    # Orange
        ]
    }

    return {
        'balance_trend': balance_data,
        'financial_metrics': financial_metrics
    }

# Function to create bar chart for financial metrics
def create_bar_chart(financial_metrics):
    bar_chart = go.Figure()
    bar_chart.add_trace(go.Bar(
        x=financial_metrics['labels'],
        y=financial_metrics['values'],
        marker_color=financial_metrics['colors'],
    ))

    bar_chart.update_layout(
        title='Financial Metrics',
        xaxis_title='Metrics',
        yaxis_title='Values',
        template='plotly_white'
    )
    return bar_chart.to_dict()

# Function to create line chart for balance trends
def create_line_chart(balance_data):
    line_chart = go.Figure()
    line_chart.add_trace(go.Scatter(
        x=balance_data['labels'],
        y=balance_data['values'],
        mode='lines+markers',
        name='Balance Trend',
        line=dict(color='royalblue', width=2)
    ))

    line_chart.update_layout(
        title='Balance Trends',
        xaxis_title='Date',
        yaxis_title='Balance',
        template='plotly_white'
    )
    return line_chart.to_dict()

# Extract keywords from descriptions
def extract_keywords(description):
    keywords = re.findall(r'\b\w+\b', description.upper())
    return keywords

def create_pie_chart(transactions):
    transactions = transactions[:10]
    # Create a DataFrame
    df = pd.DataFrame(transactions)
    # Aggregate keywords
    keyword_counter = Counter()
    for description in df['Description']:
        keywords = extract_keywords(description)
        keyword_counter.update(keywords)
    # Filter out common words (optional)
    common_words = {'CD', 'SW', 'DEB', 'DD', 'TFR', 'CPT', 'DC'}
    filtered_keywords = {k: v for k, v in keyword_counter.items() if k not in common_words and v > 1}

    # Prepare data for pie chart
    labels = list(filtered_keywords.keys())
    values = list(filtered_keywords.values())
    # Create pie chart
    pie_chart = go.Figure()
    pie_chart.add_trace(go.Pie(labels=labels, values=values, textinfo='label+percent', hole=.3))

    pie_chart.update_layout(
        title='Transaction Categories',
        template='plotly_white'
    )

    return pie_chart.to_dict()

# Example Data
transactions = [
    {'Date': np.datetime64('2025-01-01'), 'Balance': 1200.50},
    {'Date': np.datetime64('2025-01-02'), 'Balance': 1500.00},
    {'Date': np.datetime64('2025-01-03'), 'Balance': 1100.75},
]
eligibility = {'Average Monthly Income': 5000, 'Average Monthly Expenses': 3000}
overall_transaction = {'Credit': 20000, 'Debit': 15000}

# Generate chart data
chart_data = create_chart_data(transactions, eligibility, overall_transaction)

# Create charts
bar_chart = create_bar_chart(chart_data['financial_metrics'])
line_chart = create_line_chart(chart_data['balance_trend'])

# Save charts to HTML
# bar_chart_html = bar_chart.to_html(full_html=False, include_plotlyjs='cdn')
# line_chart_html = line_chart.to_html(full_html=False, include_plotlyjs='cdn')

# Combine HTML for rendering
# html_template = f"""
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Bank Statement Analysis</title>
#     <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
# </head>
# <body>
#     <h1>Bank Statement Analysis</h1>
#     <div id="bar-chart">
#         {bar_chart_html}
#     </div>
#     <div id="line-chart">
#         {line_chart_html}
#     </div>
# </body>
# </html>
# """

# Save the HTML to a file
# with open("bank_statement_analysis.html", "w") as file:
#     file.write(html_template)

print("Charts successfully created and saved to 'bank_statement_analysis.html'.")
