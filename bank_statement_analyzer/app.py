import os
import re
import pandas as pd
from PyPDF2 import PdfReader
from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import tabula
from pdfminer.high_level import extract_text
from charts import create_chart_data, create_bar_chart, create_line_chart, create_pie_chart
import json
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Unified data extraction function
def extract_money_data(pdf_path):
    try:
        # First extraction pattern
        with open(pdf_path, 'rb') as file:
            # Extract tables using tabula
            tables = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True, pandas_options={'header': None})
            
            if tables:
                # Combine all tables into a single DataFrame
                df_combined = pd.concat(tables, ignore_index=True)                
                # Save the combined data to a CSV file
                os.makedirs("uploads", exist_ok=True)
                csv_path = os.path.join("uploads", "bank_table_data.csv")
                df_combined.to_csv(csv_path, index=False)
                print(f"\nSaved table data to {csv_path}")
            else:
                raise ValueError("No tables found in the PDF.")
            reader = PdfReader(file)
            content = "".join([page.extract_text() for page in reader.pages])

        # Test.py pattern
        pattern1 = r'Opening Balance\s+Total Debit\s+Total Credit\s+Closing Balance\s+(\d+\.\d+)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)\s+(\d+\.\d+)'
        match1 = re.search(pattern1, content, re.IGNORECASE)
        symbol = ""
        if match1:
            symbol = "₹"
            return pd.DataFrame([{
                'Opening Balance': float(match1.group(1).replace(',', '')),
                'Total Debit': float(match1.group(2).replace(',', '')),
                'Total Credit': float(match1.group(3).replace(',', '')),
                'Closing Balance': float(match1.group(4).replace(',', '')),
            }]), symbol

        
        # Test2.py pattern
        pattern2 = {
            'Money In': r"Money In\s+£([\d,.]+)",
            'Money Out': r"Money Out\s+£([\d,.]+)",
            'Balance Start': r"Balance on 01 September 2019\s+£([\d,.]+)",
            'Balance End': r"Balance on 30 November 2019\s+£([\d,.]+)"
        }
        values = {key: re.search(pattern, content) for key, pattern in pattern2.items()}
        if all(values.values()):
            symbol = r'[₹$£€¥]'
            # Use re.findall to find all currency symbols in the content
            symbols = re.search(symbol, content, re.UNICODE).group(0)
            return pd.DataFrame([{
                'Opening Balance': float(values['Balance Start'].group(1).replace(',', '')),
                'Total Debit': float(values['Money Out'].group(1).replace(',', '')),
                'Total Credit': float(values['Money In'].group(1).replace(',', '')),
                'Closing Balance': float(values['Balance End'].group(1).replace(',', '')),
            }]), symbols

        # Test4.py pattern
        pattern3 = r"Opening balance\s+-\s+Total debits\s+\+\s+Total credits\s+=\s+Closing balance\s+\$([\d,]+\.\d+)\s+CR.*\$([\d,]+\.\d+)\s+\$([\d,]+\.\d+)\s+\$([\d,]+\.\d+)\s+CR"
        match3 = re.search(pattern3, content, re.DOTALL)
        if match3:
            symbol = r'[₹$£€¥]'
            # Use re.findall to find all currency symbols in the content
            symbols = re.search(symbol, content, re.UNICODE).group(0)
            return pd.DataFrame([{
                'Opening Balance': float(match3.group(1).replace(',', '')),
                'Total Debit': float(match3.group(2).replace(',', '')),
                'Total Credit': float(match3.group(3).replace(',', '')),
                'Closing Balance': float(match3.group(4).replace(',', '')),
            }]), symbols

    except Exception as e:
        print(f"Error extracting data: {str(e)}")
    raise ValueError("Unable to extract data using any method.")

# ML-based analysis
def analyze_with_ml(csv_path, transation_path):
    """Analyze bank statement data from CSV"""
    try:
        df = pd.read_csv(csv_path)
        # Dynamically determine the number of rows to skip for `df_transation`
        # Read the first few rows to inspect the structure
        preview = pd.read_csv(transation_path, nrows=5)
        if "Opening Balance" in preview.iloc[0, 0]:
            skip_rows = 3
        else:
            skip_rows = 0

        df_transation = pd.read_csv(transation_path,  skiprows=skip_rows)
        if '0' not in df_transation.columns:
            # Rename columns to remove 'Unnamed:' and fill missing headers with meaningful names
            df_transation.columns = [col if not col.startswith('Unnamed') else f"Extra_{i}" for i, col in enumerate(df_transation.columns)]
            
            # Drop unnecessary columns if needed (e.g., extra columns)
            df_transation = df_transation.dropna(how="all", axis=1)  # Drop completely empty columns
            df_transation = df_transation.dropna(how="all", axis=0)  # Drop completely empty rows
            # Map meaningful column names
            df_transation.rename(
                columns={
                    "Extra_0": "Transaction_Date",
                    "Extra_1": "Value_Date",
                    "Extra_2": "Description",
                    "Extra_3": "Cheque_No",
                    "Extra_4": "Debit",
                    "Extra_5": "Credit",
                    "Extra_7": "Balance"
                },
                inplace=True
            )
            # Parse dates 
            df_transation['Transaction_Date'] = pd.to_datetime(df_transation['Transaction_Date'], errors='coerce') 
            df_transation['Value_Date'] = pd.to_datetime(df_transation['Value_Date'], errors='coerce')
            df_transation = df_transation[df_transation['Transaction_Date'].notna()]
        elif "Type" in df_transation.iloc[:, 2].values:
            #pdf2
            # Map meaningful column names for the second PDF format 
            df_transation.rename( columns={ df_transation.columns[0]: "Transaction_Date", df_transation.columns[1]: "Description", df_transation.columns[2]: "Type", df_transation.columns[3]: "Credit", df_transation.columns[4]: "Debit", df_transation.columns[5]: "Balance" }, inplace=True )
            # Parse dates 
            df_transation['Transaction_Date'] = pd.to_datetime(df_transation['Transaction_Date'], errors='coerce') 
            # df_transation['Value_Date'] = pd.to_datetime(df_transation['Value_Date'], errors='coerce')
            df_transation = df_transation[df_transation['Transaction_Date'].notna()]
        else:
            # Drop the last column if it contains only NaN values 
            if df_transation.shape[1] > 6: 
                df_transation.drop(df_transation.columns[-1], axis=1, inplace=True) 
            # Map meaningful column names for the second PDF format 
            # print(df_transation.head())
            # print("balance column here",df_transation.columns[4])
            df_transation.rename(columns={ df_transation.columns[0]: "Transaction_Date", df_transation.columns[0]: "Description", df_transation.columns[2]: "Type", df_transation.columns[3]: "Credit", df_transation.columns[1]: "Debit", df_transation.columns[4]: "Balance" }, inplace=True) 
            df_transation["Transaction_Date"] = "14 Oct 2017"
            # df_transation['Balance'] = df_transation["Balance"].apply(lambda x: x if pd.notna(x) else "")
            df_transation['Transaction_Date'] = pd.to_datetime(df_transation['Transaction_Date'], errors='coerce') 
            df_transation = df_transation[df_transation['Transaction_Date'].notna()]
        
        # Filter out rows with NaT values in 'Transaction_Date' 
        df_transation = df_transation[df_transation['Transaction_Date'].notna()]
        # df_transation = df_transation[df_transation['Balance'].notna()]
        # Clean numeric columns (remove commas and convert to float)
        numeric_columns = ["Debit", "Credit", "Balance"]
        for col in numeric_columns:
            if col in df_transation.columns:
                df_transation[col] = pd.to_numeric(
                    df_transation[col]
                    .astype(str)  # Ensure the column values are strings
                    .str.replace(",", "", regex=True)  # Remove commas
                    .str.replace(r"[^\d.-]", "", regex=True)  # Remove non-numeric characters
                    .str.strip(),  # Strip leading/trailing whitespaces
                    errors="coerce"  # Coerce invalid parsing to NaN
                )
                # df_transation[col] = pd.to_numeric(
                #     df_transation[col].str.replace(",", "").str.strip(), errors="coerce"
                #     # df_transation[col].astype(str).str.replace(r"[^\d.-]", ""), errors="coerce"
                # )
        
        # Filter rows with valid transactions
        df_transation = df_transation[df_transation["Description"].notna()]

        # Create monthly summaries and calculate the trend of balances
        df_transation['Month'] = df_transation['Transaction_Date'].dt.to_period('M')
        
        monthly_balances = df_transation.groupby('Month')['Balance'].last().reset_index()  # Get balance at the end of each month
        
        monthly_balances['Balance Change'] = monthly_balances['Balance'].diff()  # Calculate the change in balance month-to-month
        monthly_balances['Balance Change (%)'] = (monthly_balances['Balance Change'] / monthly_balances['Balance'].shift(1)) * 100  # Percentage change in balance
        
        # Calculate the trend of balance (increasing or decreasing)
        monthly_balances['Balance Trend'] = np.where(monthly_balances['Balance Change'] > 0, 'Increasing', 
                                                     np.where(monthly_balances['Balance Change'] < 0, 'Decreasing', 'No Change'))
        # Identify recurring EMIs based on debit amounts occurring on the same date each month
        df_transation['Is_EMI'] = df_transation.groupby(['Debit'])['Transaction_Date'].transform('nunique') > 1
        emi_transactions = df_transation[df_transation['Is_EMI'] == True]
        
        # Add logic to detect EMI payments
        existing_emi_count = emi_transactions.shape[0]
        is_existing_emi = 'Yes' if existing_emi_count > 0 else 'No'

        # Create transaction records
        transaction_records = df_transation.to_dict(orient="records")

        # Create summary for each transaction record 
        transaction_summaries = [] 
        monthly_credit = 0
        monthly_debit = 0
        for record in transaction_records: 
            # if record['Balance'] == 0:
            #     record['Balance'] = "Not available"  # Set to a descriptive string
            # else:
            #     record['Balance'] = float(record['Balance'])  # Convert to float if not zeroif balance is not available
            transaction_summary = { 'Date': record['Transaction_Date'], 'Description': record['Description'], 'Debit': record['Debit'], 'Credit': record['Credit'], 'Balance': record['Balance'], 'Category': 'Transaction' } 
            transaction_summaries.append(transaction_summary)
            monthly_credit += record['Credit'] if not pd.isna(record['Credit']) else 0
            monthly_debit += record['Debit'] if not pd.isna(record['Debit']) else 0
        # Create transaction record
        overall_transaction = {
            'Date': pd.Timestamp.now(),
            'Description': 'Bank Statement Summary',
            'Debit': float(str(df['Total Debit'].iloc[0]).replace(',', '')),
            'Credit': float(str(df['Total Credit'].iloc[0]).replace(',', '')),
            'Balance': float(str(df['Closing Balance'].iloc[0]).replace(',', '')),
            'Category': 'Summary'
        }
        # Calculate eligibility
        eligibility = {
            'Average Monthly Income': monthly_credit/ 12,
            'Average Monthly Expenses': monthly_debit / 12,
            'Net Cash Flow': monthly_credit - monthly_debit,
            'Regular Payment Commitments': monthly_debit * 0.3,
            'Risk Factors': {
                'Frequent Low Balance': 'Low' if monthly_credit > monthly_debit else 'High',
                'Existing Loan EMIs': 'Medium' if is_existing_emi == 'Yes' else 'Low',
                'Irregular Income Pattern': 'Low' if monthly_credit > monthly_debit * 1.5 else 'Medium',
                'Balance Trend': 'Good' if monthly_balances['Balance Trend'].iloc[-1] == 'Increasing' else 'Risky'
            }
        }
        
        # Calculate eligibility score
        score = 100
        for risk in eligibility['Risk Factors'].values():
            if risk == 'High':
                score -= 40
            elif risk == 'Medium':
                score -= 15
            elif risk == 'Low':
                score -= 10
            elif risk == 'Good':
                score += 20
            elif risk == 'Risky':
                score -= 30
        
        eligibility['Eligibility Score'] = max(0, score)
        eligibility['Recommendation'] = "Eligible for loan" if score > 50 else "Not eligible for loan"
        
        return transaction_summaries, eligibility, overall_transaction
    except Exception as e:
        print(f"Error analyzing bank statement: {str(e)}")
        return None, None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return redirect(url_for('index'))
    
    try:
        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(pdf_path)
        # Extract and analyze data
        df, symbol = extract_money_data(pdf_path)
        if not df.empty:
            csv_path = os.path.join(UPLOAD_FOLDER, 'bank_statements.csv')
            transation_path = os.path.join(UPLOAD_FOLDER, 'bank_table_data.csv')
            df.to_csv(csv_path, index=False)
            transactions, eligibility, overall_transaction = analyze_with_ml(csv_path, transation_path)
            #create a function here and take transactions, eligibility, overall_transaction to the charts.py and return the chart data
            chart_data = create_chart_data(transactions, eligibility, overall_transaction)
            bar_graph = create_bar_chart(chart_data['financial_metrics'])
            line_graph = create_line_chart(chart_data['balance_trend'])
            pie_chart = create_pie_chart(transactions)
            # print(pie_chart)
            return render_template('analysis_report.html', eligibility=eligibility, transactions=transactions, overall_transaction=overall_transaction, symbol=symbol, chart_data=chart_data, bar_graph=bar_graph, line_graph=line_graph, pie_chart=pie_chart)
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect(url_for('index'))
    

if __name__ == '__main__':
    app.run(debug=True, port=5000)
