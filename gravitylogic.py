# gravitylogic.py

import os
import csv
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    filename="receipt_system.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Global files
receipt_number_file = "receipt_number.txt"
receipt_history_file = "receipt_history.csv"

# Default customization settings
customization = {
    "header_text": "GRAVITY VIT FRESH RECEIPT",
    "address": "P.O. BOX 1732-00900 KIAMBU",
    "phone": "TEL: 0721935039",
    "email": "Email: jammoh2010@gmail.com",
    "logo_path": "",  # optional
    "footer_text": "*Goods once sold are not Returnable*",
    "font": "Arial",
    "header_font_size": 16,
    "body_font_size": 12,
    "footer_font_size": 12
}

def read_csv_file(file_path, default_headers=None):
    try:
        if not os.path.exists(file_path):
            logging.warning(f"{file_path} not found. Creating empty DataFrame.")
            return pd.DataFrame(columns=default_headers) if default_headers else pd.DataFrame()
        return pd.read_csv(file_path)
    except Exception as e:
        logging.exception(f"Failed to read {file_path}: {e}")
        return pd.DataFrame(columns=default_headers)

def load_items():
    try:
        with open('items.csv', 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            items = {}
            for row in reader:
                try:
                    items[row[0]] = float(row[1])
                except (IndexError, ValueError):
                    continue
            return items
    except FileNotFoundError:
        logging.error("items.csv not found.")
        return {}
    except Exception as e:
        logging.exception(f"Error loading items: {e}")
        return {}

def get_next_receipt_number():
    try:
        if not os.path.exists(receipt_number_file):
            with open(receipt_number_file, 'w') as f:
                f.write("1")
                return 1
        with open(receipt_number_file, 'r+') as f:
            try:
                current = int(f.read().strip())
            except ValueError:
                current = 0
            new_number = current + 1
            f.seek(0)
            f.truncate()
            f.write(str(new_number))
            return new_number
    except Exception as e:
        logging.exception(f"Failed to update receipt number: {e}")
        return 0

def save_receipt_to_history(receipt_number, selected_items, grand_total, company):
    try:
        df = read_csv_file(receipt_history_file, ['Receipt Number', 'Date', 'Company', 'Grand Total'])
        new_entry = pd.DataFrame([[receipt_number,
                                   datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                   company,
                                   grand_total]],
                                 columns=df.columns)
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(receipt_history_file, index=False)
        logging.info(f"Saved receipt #{receipt_number} to history.")
    except Exception as e:
        logging.exception(f"Error saving to history: {e}")

def generate_receipt_pdf(selected_items, company):
    if company == "Select Company" or not selected_items:
        logging.error("Missing company or items for receipt generation.")
        return None
    try:
        receipt_number = get_next_receipt_number()
        pdf = FPDF()
        pdf.add_page()

        if customization["logo_path"] and os.path.exists(customization["logo_path"]):
            try:
                pdf.image(customization["logo_path"], 10, 8, 33)
            except Exception as e:
                logging.warning(f"Could not load logo image: {e}")

        # Header
        pdf.set_font(customization["font"], 'B', customization["header_font_size"])
        pdf.cell(200, 10, customization["header_text"], ln=True, align='C')
        pdf.set_font(customization["font"], '', customization["body_font_size"])
        pdf.cell(200, 10, customization["address"], ln=True, align='C')
        pdf.cell(200, 10, customization["phone"], ln=True, align='C')
        pdf.cell(200, 10, customization["email"], ln=True, align='C')
        pdf.ln(10)

        pdf.cell(200, 10, f"Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(200, 10, f"Company: {company}", ln=True)
        pdf.ln(10)

        # Item table
        pdf.set_font(customization["font"], 'B', customization["body_font_size"])
        pdf.cell(40, 10, "Quantity", 1)
        pdf.cell(80, 10, "Item", 1)
        pdf.cell(40, 10, "Price", 1)
        pdf.cell(40, 10, "Total", 1)
        pdf.ln(10)

        grand_total = 0
        pdf.set_font(customization["font"], '', customization["body_font_size"])
        for item, qty, price, total in selected_items:
            pdf.cell(40, 10, str(qty), 1)
            pdf.cell(80, 10, item, 1)
            pdf.cell(40, 10, f"{price:.2f}", 1)
            pdf.cell(40, 10, f"{total:.2f}", 1)
            pdf.ln(10)
            grand_total += total

        pdf.ln(5)
        pdf.set_font(customization["font"], 'B', customization["body_font_size"])
        pdf.cell(200, 10, f"Grand Total: {grand_total:.2f}", ln=True, align='R')

        pdf.ln(5)
        pdf.set_font(customization["font"], 'BI', customization["footer_font_size"])
        pdf.cell(200, 10, customization["footer_text"], ln=True, align='C')

        filename = f"receipt_{receipt_number}.pdf"
        pdf.output(filename)

        save_receipt_to_history(receipt_number, selected_items, grand_total, company)

        logging.info(f"Generated receipt PDF: {filename}")
        return filename
    except Exception as e:
        logging.exception(f"Failed to generate receipt PDF: {e}")
        return None

def generate_monthly_report(year: int, month: int, company: str) -> str:
    try:
        df = read_csv_file(receipt_history_file, ['Receipt Number', 'Date', 'Company', 'Grand Total'])
        if df.empty:
            print("[DEBUG] receipt_history.csv is empty.")
            return None

        print(f"\n[DEBUG] Filtering for: {year}-{month:02d}, Company: {company}")
        print("[DEBUG] Raw Company Values in File:", df['Company'].unique())
        print("[DEBUG] Raw Date Values in File:", df['Date'].tolist())

        # Parse 'Date' from "DD/MM/YYYY HH:MM" to datetime object
        df['ParsedDate'] = pd.to_datetime(df['Date'], format="%d/%m/%Y %H:%M", errors='coerce')

        # Drop rows where date parsing failed
        df = df.dropna(subset=['ParsedDate'])

        # Normalize company names to lowercase (case-insensitive matching)
        df['Company'] = df['Company'].str.strip().str.lower()
        company = company.strip().lower()

        # Filter by year, month, and company
        df = df[
            (df['ParsedDate'].dt.year == year) &
            (df['ParsedDate'].dt.month == month) &
            (df['Company'] == company)
        ].copy()

        if df.empty:
            print(f"[INFO] No data found for {year}-{month:02d} and {company}")
            return None

        df['Grand Total'] = pd.to_numeric(df['Grand Total'], errors='coerce')
        df['DateOnly'] = df['ParsedDate'].dt.strftime('%Y-%m-%d')

        daily_totals = df.groupby('DateOnly')['Grand Total'].sum().reset_index()
        total_sales = daily_totals['Grand Total'].sum()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Monthly Report - {company.title()}", ln=True, align="C")
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"{year}-{month:02d}", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(50, 10, "Date", 1)
        pdf.cell(80, 10, "Daily Total (KSH)", 1)
        pdf.ln()

        pdf.set_font("Arial", '', 12)
        for _, row in daily_totals.iterrows():
            pdf.cell(50, 10, row['DateOnly'], 1)
            pdf.cell(80, 10, f"{row['Grand Total']:.2f}", 1)
            pdf.ln()

        pdf.ln()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Grand Total: KSH {total_sales:.2f}", ln=True, align='R')

        filename = f"monthly_report_{year}_{month:02d}_{company.replace(' ', '_')}.pdf"
        pdf.output(filename)
        print(f"[DEBUG] Monthly report PDF saved as {filename}")
        return filename

    except Exception as e:
        logging.exception("Monthly report generation failed")
        return None
