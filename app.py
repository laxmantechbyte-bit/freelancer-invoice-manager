import csv
import io
import sqlite3
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "invoice_manager.db"
CURRENCY = "INR"

st.set_page_config(page_title="Freelancer Invoice Manager", page_icon="🧾", layout="wide")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                company TEXT,
                address TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL UNIQUE,
                client_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                tax_rate REAL NOT NULL DEFAULT 0,
                subtotal REAL NOT NULL,
                tax_amount REAL NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Unpaid',
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            );
        """)


def money(value):
    return f"₹{float(value):,.2f}"


def fetch_clients():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM clients ORDER BY name COLLATE NOCASE").fetchall()


def fetch_invoices(status=None):
    sql = """SELECT i.*, c.name AS client_name, c.email AS client_email,
                    c.address AS client_address, c.company AS client_company
             FROM invoices i JOIN clients c ON c.id=i.client_id"""
    params = []
    if status and status != "All":
        sql += " WHERE i.status=?"
        params.append(status)
    sql += " ORDER BY i.issue_date DESC, i.id DESC"
    with get_connection() as conn:
        return conn.execute(sql, params).fetchall()


def make_invoice_pdf(invoice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallGrey", parent=styles["Normal"], textColor=colors.HexColor("#64748b"), fontSize=9))
    story = [
        Paragraph("INVOICE", styles["Title"]),
        Paragraph("Freelancer Invoice Manager", styles["SmallGrey"]),
        Spacer(1, 10*mm),
        Paragraph(f"<b>Invoice:</b> {invoice['invoice_number']}", styles["Normal"]),
        Paragraph(f"<b>Issue date:</b> {invoice['issue_date']} &nbsp;&nbsp; <b>Due date:</b> {invoice['due_date']}", styles["Normal"]),
        Spacer(1, 6*mm),
        Paragraph("<b>Bill to</b>", styles["Heading2"]),
        Paragraph(invoice["client_name"], styles["Normal"]),
    ]
    if invoice["client_company"]:
        story.append(Paragraph(invoice["client_company"], styles["Normal"]))
    if invoice["client_email"]:
        story.append(Paragraph(invoice["client_email"], styles["Normal"]))
    if invoice["client_address"]:
        story.append(Paragraph(invoice["client_address"].replace("\n", "<br/>"), styles["Normal"]))
    story += [Spacer(1, 8*mm)]
    data = [
        ["Description", "Qty", "Unit price", "Amount"],
        [invoice["description"], f"{invoice['quantity']:g}", money(invoice["unit_price"]), money(invoice["subtotal"])],
        ["", "", "Subtotal", money(invoice["subtotal"])],
        ["", "", f"Tax ({invoice['tax_rate']:g}%)", money(invoice["tax_amount"])],
        ["", "", "TOTAL", money(invoice["total"])],
    ]
    table = Table(data, colWidths=[85*mm, 18*mm, 32*mm, 35*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cbd5e1")),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e0e7ff")),
        ("FONTNAME", (2,-1), (-1,-1), "Helvetica-Bold"),
        ("PADDING", (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story += [table, Spacer(1, 8*mm)]
    if invoice["notes"]:
        story.append(Paragraph("<b>Notes</b>", styles["Heading3"]))
        story.append(Paragraph(invoice["notes"], styles["Normal"]))
    story += [Spacer(1, 12*mm), Paragraph("Thank you for your business.", styles["SmallGrey"])]
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def add_client(name, email, phone, company, address):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO clients(name,email,phone,company,address) VALUES(?,?,?,?,?)",
            (name.strip(), email.strip(), phone.strip(), company.strip(), address.strip())
        )


def add_invoice(client_id, issue, due, description, quantity, unit_price, tax_rate, notes):
    subtotal = round(quantity * unit_price, 2)
    tax_amount = round(subtotal * tax_rate / 100, 2)
    total = round(subtotal + tax_amount, 2)
    invoice_number = f"INV-{date.today():%Y%m%d}-{int(date.today().strftime('%j')):03d}-{int(__import__('time').time()) % 10000:04d}"
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO invoices(invoice_number,client_id,issue_date,due_date,description,
                quantity,unit_price,tax_rate,subtotal,tax_amount,total,status,notes)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,'Unpaid',?)
        """, (invoice_number, client_id, issue.isoformat(), due.isoformat(), description.strip(),
              quantity, unit_price, tax_rate, subtotal, tax_amount, total, notes.strip()))


def update_status(invoice_id, status):
    with get_connection() as conn:
        conn.execute("UPDATE invoices SET status=? WHERE id=?", (status, invoice_id))


init_db()

st.title("🧾 Freelancer Invoice Manager")
st.caption("A simple workspace to manage clients, create invoices and track payments.")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Clients", "Create invoice", "Invoices"])
st.sidebar.divider()
st.sidebar.caption("Local demo app • Data is stored in invoice_manager.db on this computer.")

invoices = fetch_invoices()
clients = fetch_clients()

if page == "Dashboard":
    st.subheader("Business overview")
    total_billed = sum(row["total"] for row in invoices)
    paid = sum(row["total"] for row in invoices if row["status"] == "Paid")
    outstanding = sum(row["total"] for row in invoices if row["status"] != "Paid")
    overdue = sum(row["total"] for row in invoices if row["status"] != "Paid" and date.fromisoformat(row["due_date"]) < date.today())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total billed", money(total_billed))
    c2.metric("Paid", money(paid))
    c3.metric("Outstanding", money(outstanding))
    c4.metric("Overdue", money(overdue))
    st.subheader("Recent invoices")
    if invoices:
        st.dataframe([{"Invoice": x["invoice_number"], "Client": x["client_name"],
                       "Issue date": x["issue_date"], "Due date": x["due_date"],
                       "Total": money(x["total"]), "Status": x["status"]} for x in invoices[:8]],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No invoices yet. Add a client, then create your first invoice.")
    st.subheader("Getting started")
    st.markdown("1. Add a client in **Clients**.  \n2. Create an invoice in **Create invoice**.  \n3. Track payment status in **Invoices**.")

elif page == "Clients":
    st.subheader("Client management")
    with st.expander("＋ Add a new client", expanded=not bool(clients)):
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("Client name *")
            company = st.text_input("Company")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            address = st.text_area("Billing address")
            submitted = st.form_submit_button("Save client", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Client name is required.")
                else:
                    add_client(name, email, phone, company, address)
                    st.success("Client saved.")
                    st.rerun()
    clients = fetch_clients()
    if clients:
        st.dataframe([{"Name": c["name"], "Company": c["company"], "Email": c["email"],
                       "Phone": c["phone"], "Address": c["address"]} for c in clients],
                     use_container_width=True, hide_index=True)
    else:
        st.info("Your client list is empty.")

elif page == "Create invoice":
    st.subheader("Create a new invoice")
    if not clients:
        st.warning("Add at least one client before creating an invoice. Open the Clients page first.")
    else:
        client_options = {f"{c['name']} — {c['company'] or 'Individual'}": c["id"] for c in clients}
        with st.form("invoice_form"):
            selected_client = st.selectbox("Bill to", list(client_options.keys()))
            col1, col2 = st.columns(2)
            issue = col1.date_input("Issue date", value=date.today())
            due = col2.date_input("Due date", value=date.today() + timedelta(days=14), min_value=date.today())
            description = st.text_input("Service / item description", placeholder="e.g. Website design")
            col3, col4, col5 = st.columns(3)
            quantity = col3.number_input("Quantity", min_value=0.01, value=1.0, step=1.0)
            unit_price = col4.number_input("Unit price (₹)", min_value=0.0, value=5000.0, step=100.0)
            tax_rate = col5.number_input("Tax rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
            notes = st.text_area("Notes / payment instructions")
            subtotal = quantity * unit_price
            tax = subtotal * tax_rate / 100
            st.info(f"Subtotal: **{money(subtotal)}**  |  Tax: **{money(tax)}**  |  Total: **{money(subtotal + tax)}**")
            submitted = st.form_submit_button("Create invoice", type="primary")
            if submitted:
                if not description.strip():
                    st.error("Please enter a service or item description.")
                elif due < issue:
                    st.error("Due date cannot be earlier than issue date.")
                else:
                    add_invoice(client_options[selected_client], issue, due, description,
                                float(quantity), float(unit_price), float(tax_rate), notes)
                    st.success("Invoice created successfully.")
                    st.rerun()


elif page == "Invoices":
    st.subheader("Invoice register")

    filter_status = st.selectbox(
        "Filter by status",
        ["All", "Unpaid", "Paid", "Overdue"]
    )

    rows = fetch_invoices()

    if filter_status == "Overdue":
        rows = [
            r for r in rows
            if r["status"] != "Paid"
            and date.fromisoformat(r["due_date"]) < date.today()
        ]

    elif filter_status != "All":
        rows = [
            r for r in rows
            if r["status"] == filter_status
        ]

    if rows:
        st.dataframe(
            [
                {
                    "Invoice": r["invoice_number"],
                    "Client": r["client_name"],
                    "Issue date": r["issue_date"],
                    "Due date": r["due_date"],
                    "Total": money(r["total"]),
                    "Status": r["status"]
                }
                for r in rows
            ],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        chosen_number = st.selectbox(
            "Select invoice",
            [r["invoice_number"] for r in rows]
        )

        chosen = next(
            r for r in rows
            if r["invoice_number"] == chosen_number
        )

        left, right = st.columns([1, 2])

        with left:
            new_status = st.selectbox(
                "Payment status",
                ["Unpaid", "Paid"],
                index=0 if chosen["status"] == "Unpaid" else 1
            )

            if st.button("Update status"):
                update_status(chosen["id"], new_status)
                st.success("Payment status updated.")
                st.rerun()

        with right:
            pdf_bytes = make_invoice_pdf(chosen)

            st.download_button(
                "⬇ Download invoice PDF",
                data=pdf_bytes,
                file_name=f"{chosen['invoice_number']}.pdf",
                mime="application/pdf",
                type="primary"
            )

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)

        writer.writerow([
            "Invoice", "Client", "Issue date", "Due date",
            "Description", "Quantity", "Unit price",
            "Tax rate", "Subtotal", "Tax", "Total", "Status"
        ])

        for r in rows:
            writer.writerow([
                r["invoice_number"],
                r["client_name"],
                r["issue_date"],
                r["due_date"],
                r["description"],
                r["quantity"],
                r["unit_price"],
                r["tax_rate"],
                r["subtotal"],
                r["tax_amount"],
                r["total"],
                r["status"]
            ])

        st.download_button(
            "⬇ Export visible invoices as CSV",
            data=csv_buffer.getvalue(),
            file_name="invoices.csv",
            mime="text/csv"
        )

    else:
        st.info("No invoices match this filter.")
