import pandas as pd
import io
import xlsxwriter
from datetime import date
from typing import List, Dict, Any
from pydantic import BaseModel

class SOAItem(BaseModel):
    description: str
    actual_amount: float
    budgeted_amount: float

class SOARequest(BaseModel):
    event_name: str
    event_date: str
    venue: str
    activity_code: str
    income_items: List[Dict[str, Any]]
    expense_items: List[Dict[str, Any]]
    prepared_by: str
    designation_prepared: str
    certified_by: str
    designation_certified: str

class SOAService:
    @staticmethod
    def calculate_soa_totals(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate variance for SOA items"""
        df["Actual ($)"] = pd.to_numeric(df["Actual ($)"], errors='coerce').fillna(0)
        df["Budgeted ($)"] = pd.to_numeric(df["Budgeted ($)"], errors='coerce').fillna(0)
        df["Variance ($)"] = df["Actual ($)"] - df["Budgeted ($)"]
        return df

    @staticmethod
    def generate_soa_excel(request: SOARequest) -> bytes:
        """Generate SOA Excel file"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Sheet1")

        # Convert items to DataFrames
        income_df = pd.DataFrame(request.income_items)
        expense_df = pd.DataFrame(request.expense_items)

        # Calculate totals
        if not income_df.empty:
            income_df = SOAService.calculate_soa_totals(income_df)
        if not expense_df.empty:
            expense_df = SOAService.calculate_soa_totals(expense_df)

        # Styles
        fmt_header_left = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True, 'align': 'right'})
        fmt_header_val = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'align': 'left'})
        fmt_table_header = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True, 'align': 'center', 'top': 1, 'bottom': 1})
        fmt_desc = workbook.add_format({'font_name': 'Arial', 'font_size': 10})
        fmt_num = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'num_format': '#,##0.00'})
        fmt_total_label = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True, 'align': 'right'})
        fmt_total_val = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True, 'num_format': '#,##0.00', 'top': 1, 'bottom': 1})

        # Columns
        sheet.set_column('A:A', 2)
        sheet.set_column('B:B', 40) # Description
        sheet.set_column('C:D', 2)  # Spacers
        sheet.set_column('E:G', 15) # Numbers

        # Top Block
        sheet.write(0, 1, "Ang Mo Kio Community Centre", workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 12}))

        sheet.write(3, 1, "Name of Organising Committee:", fmt_header_left)
        sheet.write(3, 3, "Teck Ghee West Youth Network", fmt_header_val)

        sheet.write(4, 1, "Name of Activity:", fmt_header_left)
        sheet.write(4, 3, request.event_name, fmt_header_val)

        sheet.write(5, 1, "Date / Time / Venue:", fmt_header_left)
        # Parse date string to format it
        from datetime import datetime
        try:
            parsed_date = datetime.fromisoformat(request.event_date.replace('T', ' ').split('.')[0])
            formatted_date = parsed_date.strftime('%d-%b-%y')
        except:
            formatted_date = request.event_date  # fallback to original string
        sheet.write(5, 3, f"{formatted_date} / {request.venue}", fmt_header_val)
        sheet.write(5, 5, "Activity Code:", fmt_header_left)
        sheet.write(5, 6, request.activity_code, fmt_header_val)

        # Table Headers
        r = 9
        sheet.write(r, 1, "INCOME", fmt_table_header)
        sheet.write(r, 4, "ACTUAL", fmt_table_header)
        sheet.write(r, 5, "BUDGETTED", fmt_table_header)
        sheet.write(r, 6, "VARIANCE", fmt_table_header)

        # INCOME Rows
        r += 1
        if not income_df.empty:
            for _, row in income_df.iterrows():
                sheet.write(r, 1, row['Description'], fmt_desc)
                sheet.write(r, 4, row['Actual ($)'], fmt_num)
                sheet.write(r, 5, row['Budgeted ($)'], fmt_num)
                sheet.write(r, 6, row['Variance ($)'], fmt_num)
                r += 1

        # Total Income
        sheet.write(r, 3, "TOTAL INCOME", fmt_total_label)
        income_actual = income_df['Actual ($)'].sum() if not income_df.empty else 0
        income_budgeted = income_df['Budgeted ($)'].sum() if not income_df.empty else 0
        income_variance = income_df['Variance ($)'].sum() if not income_df.empty else 0
        sheet.write(r, 4, income_actual, fmt_total_val)
        sheet.write(r, 5, income_budgeted, fmt_total_val)
        sheet.write(r, 6, income_variance, fmt_total_val)

        r += 2 # Spacer

        # EXPENDITURE Header
        sheet.write(r, 1, "EXPENSES", fmt_table_header)
        r += 1
        if not expense_df.empty:
            for _, row in expense_df.iterrows():
                sheet.write(r, 1, row['Description'], fmt_desc)
                sheet.write(r, 4, row['Actual ($)'], fmt_num)
                sheet.write(r, 5, row['Budgeted ($)'], fmt_num)
                sheet.write(r, 6, row['Variance ($)'], fmt_num)
                r += 1

        # Total Expenditure
        sheet.write(r, 3, "TOTAL EXPENDITURE", fmt_total_label)
        expense_actual = expense_df['Actual ($)'].sum() if not expense_df.empty else 0
        expense_budgeted = expense_df['Budgeted ($)'].sum() if not expense_df.empty else 0
        expense_variance = expense_df['Variance ($)'].sum() if not expense_df.empty else 0
        sheet.write(r, 4, expense_actual, fmt_total_val)
        sheet.write(r, 5, expense_budgeted, fmt_total_val)
        sheet.write(r, 6, expense_variance, fmt_total_val)

        r += 2
        # Surplus/Deficit
        net_act = income_actual - expense_actual
        net_bud = income_budgeted - expense_budgeted
        net_var = income_variance - expense_variance

        sheet.write(r, 3, "SURPLUS / (DEFICIT)", fmt_total_label)
        sheet.write(r, 4, net_act, fmt_total_val)
        sheet.write(r, 5, net_bud, fmt_total_val)
        sheet.write(r, 6, net_var, fmt_total_val)

        # Signatures
        r += 4
        sheet.write(r, 1, "Prepared by :")
        sheet.write(r, 3, "Certified By:")
        sheet.write(r, 5, "Approved By:") # Template has it, so we leave it blank

        r += 4 # Space for signing
        sheet.write(r, 1, request.prepared_by if request.prepared_by else "[Name]", fmt_desc)
        sheet.write(r, 3, request.certified_by if request.certified_by else "[Name]", fmt_desc)
        sheet.write(r, 5, "[Name]", fmt_desc) # Blank for approver

        r += 1
        sheet.write(r, 1, request.designation_prepared, fmt_desc)
        sheet.write(r, 3, request.designation_certified, fmt_desc)
        sheet.write(r, 5, "[Designation]", fmt_desc)

        r += 1
        sheet.write(r, 1, "Ang Mo Kio CC", fmt_desc)
        sheet.write(r, 3, "Teck Ghee West Youth Network", fmt_desc)
        sheet.write(r, 5, "Teck Ghee West Youth Network", fmt_desc)

        workbook.close()
        return output.getvalue()