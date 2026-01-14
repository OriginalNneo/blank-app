import pandas as pd
import io
import xlsxwriter
from datetime import date
from typing import List, Dict, Any
from pydantic import BaseModel

class BudgetItem(BaseModel):
    description: str
    per_unit: float
    quantity: int

class BudgetRequest(BaseModel):
    event_name: str
    event_date: str
    participants: int
    volunteers: int
    income_items: List[Dict[str, Any]]
    expense_items: List[Dict[str, Any]]
    prepared_by: str
    designation: str
    vetted_by: str

class BudgetService:
    @staticmethod
    def calculate_budget_totals(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate totals for budget items"""
        df["$ per unit"] = pd.to_numeric(df["$ per unit"], errors='coerce').fillna(0)
        df["Qty"] = pd.to_numeric(df["Qty"], errors='coerce').fillna(0)
        df["$ (Total)"] = df["$ per unit"] * df["Qty"]
        return df

    @staticmethod
    def generate_budget_excel(request: BudgetRequest) -> bytes:
        """Generate budget Excel file"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Budget")

        # Convert items to DataFrames
        income_df = pd.DataFrame(request.income_items)
        expense_df = pd.DataFrame(request.expense_items)

        # Calculate totals
        if not income_df.empty:
            income_df = BudgetService.calculate_budget_totals(income_df)
        if not expense_df.empty:
            expense_df = BudgetService.calculate_budget_totals(expense_df)

        # Styles
        fmt_title = workbook.add_format({'font_name': 'Calibri', 'font_size': 14, 'bold': True, 'align': 'center'})
        fmt_bold = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True})
        fmt_bold_center = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'align': 'center'})
        fmt_header = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'border': 1, 'align': 'center', 'bg_color': '#D9D9D9'})
        fmt_text = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1})
        fmt_currency = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1, 'num_format': '$#,##0.00'})
        fmt_curr_bold = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold':True, 'num_format': '$#,##0.00'})

        # Columns
        sheet.set_column('A:A', 30); sheet.set_column('E:E', 30)
        sheet.set_column('B:B', 12); sheet.set_column('F:F', 12)
        sheet.set_column('C:C', 8);  sheet.set_column('G:G', 8)
        sheet.set_column('D:D', 12); sheet.set_column('H:H', 12)

        # Header
        sheet.merge_range('A1:H1', "Teck Ghee Youth Network", fmt_title)
        # Parse date string to format it
        from datetime import datetime
        try:
            parsed_date = datetime.fromisoformat(request.event_date.replace('T', ' ').split('.')[0])
            formatted_date = parsed_date.strftime('%d-%b-%y')
        except:
            formatted_date = request.event_date  # fallback to original string
        sheet.merge_range('A2:H2', formatted_date, fmt_bold_center)
        sheet.merge_range('A3:H3', request.event_name, fmt_bold_center)
        sheet.merge_range('A4:H4', "Projected Statement of Accounts", fmt_bold_center)
        sheet.merge_range('A5:H5', "", fmt_bold_center)
        sheet.merge_range('A6:H6', f"No. of Expected Participants: {request.participants} | Volunteers: {request.volunteers}", fmt_bold_center)

        # Tables
        sheet.write(8, 0, "INCOME", fmt_bold)
        sheet.write(8, 4, "EXPENDITURE", fmt_bold)

        headers = ["Description", "$ per unit", "Qty", "$"]
        for i, h in enumerate(headers):
            sheet.write(9, i, h, fmt_header)
            sheet.write(9, 4 + i, h, fmt_header)

        # Data
        rows = max(len(income_df), len(expense_df), 17)
        for i in range(rows):
            r = 10 + i
            # Income
            if i < len(income_df):
                row = income_df.iloc[i]
                sheet.write(r, 0, row['Description'], fmt_text)
                sheet.write(r, 1, row['$ per unit'], fmt_currency)
                sheet.write(r, 2, row['Qty'], fmt_text)
                sheet.write(r, 3, row['$ (Total)'], fmt_currency)
            else:
                for c in range(4): sheet.write(r, c, "", fmt_text)
            # Expenditure
            if i < len(expense_df):
                row = expense_df.iloc[i]
                sheet.write(r, 4, row['Description'], fmt_text)
                sheet.write(r, 5, row['$ per unit'], fmt_currency)
                sheet.write(r, 6, row['Qty'], fmt_text)
                sheet.write(r, 7, row['$ (Total)'], fmt_currency)
            else:
                for c in range(4, 8): sheet.write(r, c, "", fmt_text)

        # Totals
        r_tot = 10 + rows
        if not income_df.empty:
            sheet.write(r_tot, 0, "Total Income:", fmt_bold)
            sheet.write(r_tot, 3, income_df["$ (Total)"].sum(), fmt_curr_bold)
        if not expense_df.empty:
            sheet.write(r_tot, 4, "Total Expenditure:", fmt_bold)
            sheet.write(r_tot, 7, expense_df["$ (Total)"].sum(), fmt_curr_bold)

        # Net calculation
        income_total = income_df["$ (Total)"].sum() if not income_df.empty else 0
        expense_total = expense_df["$ (Total)"].sum() if not expense_df.empty else 0
        net = income_total - expense_total

        sheet.write(r_tot+2, 4, "Deficit/Surplus:", fmt_bold)
        sheet.write(r_tot+2, 7, net, fmt_curr_bold)

        # Signatures
        r_sig = r_tot + 5
        # Prepared By
        sheet.write(r_sig, 0, "_"*25); sheet.write(r_sig+1, 0, "Prepared By:")
        sheet.write(r_sig+2, 0, request.prepared_by); sheet.write(r_sig+3, 0, request.designation)
        sheet.write(r_sig+4, 0, "Teck Ghee Youth Network")
        # Vetted By
        sheet.write(r_sig, 4, "_"*25); sheet.write(r_sig+1, 4, "Vetted By:")
        sheet.write(r_sig+2, 4, request.vetted_by); sheet.write(r_sig+3, 4, "Member")
        sheet.write(r_sig+4, 4, "Teck Ghee Youth Network")

        # Approved By
        r_app = r_sig + 6
        sheet.write(r_app, 4, "_"*25); sheet.write(r_app+1, 4, "Approved By:")
        sheet.write(r_app+2, 4, "[Name]"); sheet.write(r_app+3, 4, "Chairman/Treasurer")
        sheet.write(r_app+4, 4, "Teck Ghee Youth Network")

        workbook.close()
        return output.getvalue()

    @staticmethod
    def parse_budget_excel(file_bytes: bytes) -> Dict[str, Any]:
        """Parse an existing budget Excel file generated by this system into a BudgetRequest-like dict."""
        from io import BytesIO

        result: Dict[str, Any] = {
            "event_name": "",
            "event_date": "",
            "participants": 0,
            "volunteers": 0,
            "prepared_by": "",
            "designation": "",
            "vetted_by": "",
            "income_items": [],
            "expense_items": [],
        }

        try:
            df = pd.read_excel(BytesIO(file_bytes), sheet_name="Budget", header=None)
        except Exception:
            # Fallback: try first sheet name
            df = pd.read_excel(BytesIO(file_bytes), header=None)

        # Event name: line with non-empty text between title and "Projected Statement of Accounts"
        for _, row in df.iterrows():
            val = row.iloc[0]
            if isinstance(val, str) and val.strip() and "Teck Ghee Youth Network" not in val and "Projected Statement of Accounts" not in val and "No. of Expected Participants" not in val:
                result["event_name"] = val.strip()
                break

        # Event date: look for row that contains "No. of Expected Participants" and also use the earlier date row if available
        for _, row in df.iterrows():
            val = row.iloc[0]
            if isinstance(val, str) and "No. of Expected Participants" in val:
                # Try to extract participants and volunteers
                text = val
                import re

                m = re.search(r"Participants:\s*(\d+)", text)
                if m:
                    result["participants"] = int(m.group(1))
                m = re.search(r"Volunteers:\s*(\d+)", text)
                if m:
                    result["volunteers"] = int(m.group(1))
                break

        # Prepared By / Designation / Vetted By
        mask_prepared = df == "Prepared By:"
        coords_prepared = list(zip(*mask_prepared.to_numpy().nonzero()))
        if coords_prepared:
            r, c = coords_prepared[0]
            if r + 2 < len(df):
                result["prepared_by"] = str(df.iat[r + 2, c] or "").strip()
                result["designation"] = str(df.iat[r + 3, c] or "").strip()

        mask_vetted = df == "Vetted By:"
        coords_vetted = list(zip(*mask_vetted.to_numpy().nonzero()))
        if coords_vetted:
            r, c = coords_vetted[0]
            if r + 2 < len(df.columns):
                result["vetted_by"] = str(df.iat[r + 2, c] or "").strip()

        # Find header row for income/expense tables
        header_row_idx = None
        for idx, row in df.iterrows():
            if (
                str(row.iloc[0]).strip() == "Description"
                and str(row.iloc[1]).strip() == "$ per unit"
            ):
                header_row_idx = idx
                break

        income_items: List[Dict[str, Any]] = []
        expense_items: List[Dict[str, Any]] = []

        if header_row_idx is not None:
            # Income in cols 0-3, Expenditure in cols 4-7
            i = header_row_idx + 1
            while i < len(df):
                row = df.iloc[i]
                # Stop at Total row
                if isinstance(row.iloc[0], str) and row.iloc[0].strip().startswith("Total Income"):
                    break

                desc = row.iloc[0]
                if not (pd.isna(desc) and pd.isna(row.iloc[1]) and pd.isna(row.iloc[2]) and pd.isna(row.iloc[3])):
                    if isinstance(desc, str) and desc.strip():
                        income_items.append(
                            {
                                "Description": str(desc).strip(),
                                "$ per unit": float(row.iloc[1] or 0),
                                "Qty": int(row.iloc[2] or 0),
                                "$ (Total)": float(row.iloc[3] or 0),
                            }
                        )

                exp_desc = row.iloc[4] if len(row) > 4 else None
                if len(row) > 7 and not (pd.isna(exp_desc) and pd.isna(row.iloc[5]) and pd.isna(row.iloc[6]) and pd.isna(row.iloc[7])):
                    if isinstance(exp_desc, str) and exp_desc.strip():
                        expense_items.append(
                            {
                                "Description": str(exp_desc).strip(),
                                "$ per unit": float(row.iloc[5] or 0),
                                "Qty": int(row.iloc[6] or 0),
                                "$ (Total)": float(row.iloc[7] or 0),
                            }
                        )

                i += 1

        result["income_items"] = income_items
        result["expense_items"] = expense_items

        return result