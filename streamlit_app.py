import streamlit as st
import pandas as pd
import io
import xlsxwriter
from datetime import date

# --- Page Configuration ---
st.set_page_config(page_title="TGYN Finance App", layout="wide")

# --- Helper Functions ---
def calculate_budget_totals(df):
    """Calculates totals for the Budget Planner (Unit * Qty)"""
    df["$ per unit"] = pd.to_numeric(df["$ per unit"], errors='coerce').fillna(0)
    df["Qty"] = pd.to_numeric(df["Qty"], errors='coerce').fillna(0)
    df["$ (Total)"] = df["$ per unit"] * df["Qty"]
    return df

def calculate_soa_totals(df):
    """Calculates Variance for SOA (Actual - Budgeted)"""
    df["Actual ($)"] = pd.to_numeric(df["Actual ($)"], errors='coerce').fillna(0)
    df["Budgeted ($)"] = pd.to_numeric(df["Budgeted ($)"], errors='coerce').fillna(0)
    df["Variance ($)"] = df["Actual ($)"] - df["Budgeted ($)"]
    return df

# --- EXCEL GENERATOR: BUDGET (Side-by-Side) ---
def generate_budget_excel(event_name, event_date, participants, volunteers, inc_df, exp_df, prep_by, des_prep, vet_by):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    sheet = workbook.add_worksheet("Budget")

    # Styles
    fmt_title = workbook.add_format({'font_name': 'Calibri', 'font_size': 14, 'bold': True})
    fmt_bold = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True})
    fmt_header = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'border': 1, 'align': 'center', 'bg_color': '#D9D9D9'})
    fmt_text = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1})
    fmt_currency = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1, 'num_format': '$#,##0.00'})
    fmt_curr_bold = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold':True, 'num_format': '$#,##0.00'})
    
    # Columns (A-H)
    sheet.set_column('A:A', 30); sheet.set_column('E:E', 30)
    sheet.set_column('B:B', 12); sheet.set_column('F:F', 12)
    sheet.set_column('C:C', 8);  sheet.set_column('G:G', 8)
    sheet.set_column('D:D', 12); sheet.set_column('H:H', 12)

    # Header
    sheet.write(0, 0, "Teck Ghee Youth Network", fmt_title)
    sheet.write(1, 0, f"{event_date.strftime('%d-%b-%y')}")
    sheet.write(2, 0, event_name)
    sheet.write(3, 0, "Projected Statement of Accounts")
    sheet.write(5, 2, f"No. of Expected Participants: {participants} | Volunteers: {volunteers}", fmt_bold)

    # Tables
    sheet.write(8, 0, "INCOME", fmt_bold)
    sheet.write(8, 4, "EXPENDITURE", fmt_bold)

    headers = ["Description", "$ per unit", "Qty", "$"]
    for i, h in enumerate(headers):
        sheet.write(9, i, h, fmt_header)
        sheet.write(9, 4 + i, h, fmt_header)

    # Data
    rows = max(len(inc_df), len(exp_df), 17)
    for i in range(rows):
        r = 10 + i
        # Income
        if i < len(inc_df):
            row = inc_df.iloc[i]
            sheet.write(r, 0, row['Description'], fmt_text)
            sheet.write(r, 1, row['$ per unit'], fmt_currency)
            sheet.write(r, 2, row['Qty'], fmt_text)
            sheet.write(r, 3, row['$ (Total)'], fmt_currency)
        else:
            for c in range(4): sheet.write(r, c, "", fmt_text)
        # Expenditure
        if i < len(exp_df):
            row = exp_df.iloc[i]
            sheet.write(r, 4, row['Description'], fmt_text)
            sheet.write(r, 5, row['$ per unit'], fmt_currency)
            sheet.write(r, 6, row['Qty'], fmt_text)
            sheet.write(r, 7, row['$ (Total)'], fmt_currency)
        else:
            for c in range(4, 8): sheet.write(r, c, "", fmt_text)

    # Totals
    r_tot = 10 + rows
    sheet.write(r_tot, 0, "Total Income:", fmt_bold)
    sheet.write(r_tot, 3, inc_df["$ (Total)"].sum(), fmt_curr_bold)
    sheet.write(r_tot, 4, "Total Expenditure:", fmt_bold)
    sheet.write(r_tot, 7, exp_df["$ (Total)"].sum(), fmt_curr_bold)
    
    net = inc_df["$ (Total)"].sum() - exp_df["$ (Total)"].sum()
    sheet.write(r_tot+2, 4, "Surplus/Deficit:", fmt_bold)
    sheet.write(r_tot+2, 7, net, fmt_curr_bold)

    # Signatures
    r_sig = r_tot + 5
    # Prepared By
    sheet.write(r_sig, 0, "_"*25); sheet.write(r_sig+1, 0, "Prepared By:")
    sheet.write(r_sig+2, 0, prep_by); sheet.write(r_sig+3, 0, des_prep)
    sheet.write(r_sig+4, 0, "Teck Ghee Youth Network")
    # Vetted By
    sheet.write(r_sig, 4, "_"*25); sheet.write(r_sig+1, 4, "Vetted By:")
    sheet.write(r_sig+2, 4, vet_by); sheet.write(r_sig+3, 4, "Member")
    sheet.write(r_sig+4, 4, "Teck Ghee Youth Network")

    workbook.close()
    return output

# --- EXCEL GENERATOR: SOA (Vertical, Ang Mo Kio CC Template) ---
def generate_soa_excel(event_name, event_date, venue, act_code, inc_df, exp_df, prep_by, des_prep, cert_by, des_cert):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    sheet = workbook.add_worksheet("Sheet1")

    # Styles
    fmt_header_left = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True, 'align': 'right'})
    fmt_header_val = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'align': 'left'})
    fmt_table_header = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True, 'align': 'center', 'top': 1, 'bottom': 1})
    fmt_desc = workbook.add_format({'font_name': 'Arial', 'font_size': 10})
    fmt_num = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'num_format': '#,##0.00'})
    fmt_total_label = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True, 'align': 'right'})
    fmt_total_val = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True, 'num_format': '#,##0.00', 'top': 1, 'bottom': 1})

    # Columns: A(Hidden/Margin), B(Desc), C(Gap), D(Gap), E(Actual), F(Budget), G(Variance)
    sheet.set_column('A:A', 2)
    sheet.set_column('B:B', 40) # Description
    sheet.set_column('C:D', 2)  # Spacers
    sheet.set_column('E:G', 15) # Numbers

    # Top Block
    sheet.write(0, 1, "Ang Mo Kio Community Centre", workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 12}))
    
    sheet.write(3, 1, "Name of Organising Committee:", fmt_header_left)
    sheet.write(3, 3, "Teck Ghee West Youth Network", fmt_header_val)
    
    sheet.write(4, 1, "Name of Activity:", fmt_header_left)
    sheet.write(4, 3, event_name, fmt_header_val)
    
    sheet.write(5, 1, "Date / Time / Venue:", fmt_header_left)
    sheet.write(5, 3, f"{event_date.strftime('%d-%b-%y')} / {venue}", fmt_header_val)
    sheet.write(5, 5, "Activity Code:", fmt_header_left)
    sheet.write(5, 6, act_code, fmt_header_val)

    # Table Headers
    r = 9
    sheet.write(r, 1, "INCOME", fmt_table_header)
    sheet.write(r, 4, "ACTUAL", fmt_table_header)
    sheet.write(r, 5, "BUDGETTED", fmt_table_header)
    sheet.write(r, 6, "VARIANCE", fmt_table_header)

    # INCOME Rows
    r += 1
    for _, row in inc_df.iterrows():
        sheet.write(r, 1, row['Description'], fmt_desc)
        sheet.write(r, 4, row['Actual ($)'], fmt_num)
        sheet.write(r, 5, row['Budgeted ($)'], fmt_num)
        sheet.write(r, 6, row['Variance ($)'], fmt_num)
        r += 1
    
    # Total Income
    sheet.write(r, 3, "TOTAL INCOME", fmt_total_label)
    sheet.write(r, 4, inc_df['Actual ($)'].sum(), fmt_total_val)
    sheet.write(r, 5, inc_df['Budgeted ($)'].sum(), fmt_total_val)
    sheet.write(r, 6, inc_df['Variance ($)'].sum(), fmt_total_val)
    
    r += 2 # Spacer

    # EXPENDITURE Header
    sheet.write(r, 1, "EXPENDITURE", fmt_table_header)
    r += 1
    for _, row in exp_df.iterrows():
        sheet.write(r, 1, row['Description'], fmt_desc)
        sheet.write(r, 4, row['Actual ($)'], fmt_num)
        sheet.write(r, 5, row['Budgeted ($)'], fmt_num)
        sheet.write(r, 6, row['Variance ($)'], fmt_num)
        r += 1

    # Total Exp
    sheet.write(r, 3, "TOTAL EXPENDITURE", fmt_total_label)
    sheet.write(r, 4, exp_df['Actual ($)'].sum(), fmt_total_val)
    sheet.write(r, 5, exp_df['Budgeted ($)'].sum(), fmt_total_val)
    sheet.write(r, 6, exp_df['Variance ($)'].sum(), fmt_total_val)

    r += 2
    # Surplus/Deficit
    net_act = inc_df['Actual ($)'].sum() - exp_df['Actual ($)'].sum()
    net_bud = inc_df['Budgeted ($)'].sum() - exp_df['Budgeted ($)'].sum()
    net_var = inc_df['Variance ($)'].sum() - exp_df['Variance ($)'].sum()

    sheet.write(r, 3, "SURPLUS / (DEFICIT)", fmt_total_label)
    sheet.write(r, 4, net_act, fmt_total_val)
    sheet.write(r, 5, net_bud, fmt_total_val)
    sheet.write(r, 6, net_var, fmt_total_val)

    # Signatures (Prepared, Certified, Approved)
    r += 4
    sheet.write(r, 1, "Prepared by :")
    sheet.write(r, 3, "Certified By:")
    sheet.write(r, 5, "Approved By:") # Template has it, so we leave it blank

    r += 4 # Space for signing
    sheet.write(r, 1, prep_by if prep_by else "[Name]", fmt_desc)
    sheet.write(r, 3, cert_by if cert_by else "[Name]", fmt_desc)
    sheet.write(r, 5, "[Name]", fmt_desc) # Blank for approver

    r += 1
    sheet.write(r, 1, des_prep, fmt_desc)
    sheet.write(r, 3, des_cert, fmt_desc)
    sheet.write(r, 5, "[Designation]", fmt_desc)

    r += 1
    sheet.write(r, 1, "Ang Mo Kio CC", fmt_desc)
    sheet.write(r, 3, "Teck Ghee West Youth Network", fmt_desc)
    sheet.write(r, 5, "Teck Ghee West Youth Network", fmt_desc)

    workbook.close()
    return output

# --- APP NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Budget Planner", "Statement of Accounts (SOA)"])

if page == "Budget Planner":
    st.title("💰 Event Budget Planner")
    st.info("Layout: Side-by-Side (Income | Expenditure)")
    
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            e_name = st.text_input("Event Name")
            e_date = st.date_input("Date")
            prep = st.text_input("Prepared By")
            des_p = st.text_input("Designation", value="Member")
        with c2:
            pax = st.number_input("Participants", min_value=0)
            vol = st.number_input("Volunteers", min_value=0)
            vet = st.text_input("Vetted By")

    col_inc, col_exp = st.columns(2)
    with col_inc:
        st.subheader("Income")
        df_i = pd.DataFrame([{"Description": "Fees", "$ per unit": 0.0, "Qty": 0}])
        ed_i = calculate_budget_totals(st.data_editor(df_i, num_rows="dynamic", use_container_width=True))
    with col_exp:
        st.subheader("Expenditure")
        df_e = pd.DataFrame([{"Description": "Food", "$ per unit": 0.0, "Qty": 0}])
        ed_e = calculate_budget_totals(st.data_editor(df_e, num_rows="dynamic", use_container_width=True))

    if st.button("Generate Budget"):
        f = generate_budget_excel(e_name, e_date, pax, vol, ed_i, ed_e, prep, des_p, vet)
        st.download_button("Download Budget.xlsx", f.getvalue(), f"{e_name}_Budget.xlsx")

elif page == "Statement of Accounts (SOA)":
    st.title("📄 Statement of Accounts (SOA)")
    st.info("Layout: Vertical (Ang Mo Kio CC Template) | Actual vs Budgeted")
    
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            e_name = st.text_input("Event Name")
            e_date = st.date_input("Date")
            venue = st.text_input("Venue", value="Teck Ghee CC")
            act_code = st.text_input("Activity Code", placeholder="A1234567")
        with c2:
            prep = st.text_input("Prepared By")
            des_p = st.text_input("Designation (Prep)", value="Member")
            cert = st.text_input("Certified By")
            des_c = st.text_input("Designation (Cert)", value="Chairman/Treasurer")

    st.subheader("Income Data")
    df_i = pd.DataFrame([
        {"Description": "Participant Fees", "Actual ($)": 0.0, "Budgeted ($)": 0.0},
        {"Description": "Misc Income", "Actual ($)": 0.0, "Budgeted ($)": 0.0}
    ])
    ed_i = calculate_soa_totals(st.data_editor(df_i, num_rows="dynamic", use_container_width=True))
    
    st.subheader("Expenditure Data")
    df_e = pd.DataFrame([
        {"Description": "Food & Bev", "Actual ($)": 0.0, "Budgeted ($)": 0.0},
        {"Description": "Logistics", "Actual ($)": 0.0, "Budgeted ($)": 0.0},
        {"Description": "Transport", "Actual ($)": 0.0, "Budgeted ($)": 0.0}
    ])
    ed_e = calculate_soa_totals(st.data_editor(df_e, num_rows="dynamic", use_container_width=True))

    # Live Totals for verification
    tot_inc = ed_i["Actual ($)"].sum()
    tot_exp = ed_e["Actual ($)"].sum()
    st.write(f"**Net Surplus/Deficit (Actual):** ${tot_inc - tot_exp:,.2f}")

    if st.button("Generate SOA"):
        f = generate_soa_excel(e_name, e_date, venue, act_code, ed_i, ed_e, prep, des_p, cert, des_c)
        st.download_button("Download SOA.xlsx", f.getvalue(), f"{e_name}_SOA.xlsx")