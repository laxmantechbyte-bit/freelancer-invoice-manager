# Freelancer Invoice Manager

A beginner-friendly Python web application for freelancers and small businesses to manage clients, create invoices, track payment status, download PDF invoices, and export invoice records to CSV.

## Features

- Add and maintain client records
- Create invoices with quantity, unit price, tax, issue date, and due date
- Automatically calculate subtotal, tax, and total
- Track paid and unpaid invoices
- Dashboard metrics for billed, paid, outstanding, and overdue amounts
- Download individual invoices as PDF
- Export filtered invoice records to CSV
- SQLite database; no separate database server required

## Tech stack

- Python
- Streamlit
- SQLite
- ReportLab

## Requirements

- Python 3.9 or newer
- pip

## Run locally

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Start the app
streamlit run app.py
```

Streamlit will print a local URL, usually http://localhost:8501.

## How to use

1. Open **Clients** and add a client.
2. Open **Create invoice**, choose the client, enter the service, quantity, price, and tax.
3. Open **Invoices** to update payment status, download a PDF, or export records to CSV.
4. View totals and recent invoices on **Dashboard**.

## Data and privacy

The app stores its database in `invoice_manager.db` in the project folder. This is a local demonstration application. It does not include user accounts, cloud synchronization, automated email delivery, online payments, or production-grade access controls. Do not enter real customer personal or financial information into a public demo deployment.

To reset demo data, stop the app and delete `invoice_manager.db`. The database will be recreated on the next run.

## Portfolio description

**Freelancer Invoice Manager – Python Web App**

Built a Python-based invoice management application for freelancers and small businesses. The app supports client records, invoice creation, automatic tax and total calculations, payment tracking, PDF invoice downloads, CSV exports, and a dashboard with revenue and outstanding-payment summaries. Developed using Python, Streamlit, SQLite, and ReportLab.

## Suggested GitHub repository description

A Python + Streamlit invoice manager for freelancers with client management, PDF invoices, payment tracking, dashboard metrics, and CSV export.

## Suggested improvements

- Add authentication and user roles
- Add configurable business profile and invoice numbering
- Add automated email delivery
- Add recurring invoices and multi-currency support
- Add automated tests and deployment configuration
