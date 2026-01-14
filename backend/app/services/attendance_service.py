import gspread
from google.oauth2.service_account import Credentials
import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
import io
from app.utils.config import get_members_sheets_url, get_attendance_sheets_url, get_google_service_account_file


class AttendanceService:
    def __init__(self):
        self.gc = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize Google Sheets connection"""
        try:
            creds_file_path = get_google_service_account_file()
            
            if not os.path.exists(creds_file_path):
                raise FileNotFoundError(f"Google service account JSON file not found at {creds_file_path}")

            # Load credentials from JSON file
            with open(creds_file_path, 'r') as f:
                creds_dict = json.load(f)

            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )

            self.gc = gspread.authorize(creds)
            print("Google Sheets connection initialized successfully")
        except Exception as e:
            print(f"Error initializing Google Sheets connection: {e}")
            raise

    def get_members(self) -> List[Dict[str, str]]:
        """Get list of members from members Google Sheet"""
        try:
            members_url = get_members_sheets_url()
            if not members_url:
                raise ValueError("Members Google Sheets URL not configured")
            
            spreadsheet = self.gc.open_by_url(members_url)
            
            # Try to get the first worksheet (or a specific one if needed)
            worksheet = spreadsheet.sheet1
            
            # Get all records (assuming first row is headers)
            records = worksheet.get_all_records()
            
            # Extract member names and how to address them
            members = []
            for record in records:
                # Assuming columns are: Name, How to Address (or similar)
                name = record.get('Name', '') or record.get('name', '') or list(record.values())[0] if record else ''
                address = record.get('How to Address', '') or record.get('how_to_address', '') or record.get('Address', '') or name
                
                if name:
                    members.append({
                        "name": name,
                        "address": address or name
                    })
            
            # If no records found, try getting all values from column A (names)
            if not members:
                all_values = worksheet.get_all_values()
                if len(all_values) > 1:  # Skip header row
                    for row in all_values[1:]:
                        if row and row[0]:  # If first column has a value
                            members.append({
                                "name": row[0],
                                "address": row[0]
                            })
            
            return members
        except Exception as e:
            print(f"Error getting members: {e}")
            # Return empty list or raise based on your preference
            return []

    def get_attendance_for_date(self, date: str) -> Dict[str, str]:
        """Get attendance data for a specific date from attendance Google Sheet"""
        try:
            attendance_url = get_attendance_sheets_url()
            if not attendance_url:
                raise ValueError("Attendance Google Sheets URL not configured")
            
            spreadsheet = self.gc.open_by_url(attendance_url)
            worksheet = spreadsheet.sheet1
            
            # Get all values
            all_values = worksheet.get_all_values()
            
            if not all_values:
                return {}
            
            # Find date column
            header_row = all_values[0] if all_values else []
            date_col_index = None
            
            # Format date to match expected format (YYYY-MM-DD)
            formatted_date = date
            
            # Check if date exists in header
            for idx, header in enumerate(header_row):
                if idx == 0 or idx == 1:  # Skip column A and column B (B has names)
                    continue
                header_clean = header.strip() if header else ''
                if header_clean == formatted_date or header_clean == date:
                    date_col_index = idx
                    break
            
            if date_col_index is None:
                print(f"Date {date} not found in attendance sheet")
                return {}
            
            # Get attendance data
            # Names are in column B (index 1), not column A
            attendance_dict = {}
            for row_idx in range(1, len(all_values)):  # Start from row 2 (index 1)
                if row_idx < len(all_values) and all_values[row_idx]:
                    name = all_values[row_idx][1] if len(all_values[row_idx]) > 1 and all_values[row_idx][1] else ''
                    if name and name.strip():
                        name_clean = name.strip()
                        # Get attendance status from the date column
                        if date_col_index < len(all_values[row_idx]):
                            status = all_values[row_idx][date_col_index].strip() if all_values[row_idx][date_col_index] else 'Not Present'
                            attendance_dict[name_clean] = status
                        else:
                            attendance_dict[name_clean] = 'Not Present'
            
            return attendance_dict
        except Exception as e:
            print(f"Error getting attendance for date {date}: {e}")
            import traceback
            print(traceback.format_exc())
            return {}

    def get_most_recent_attendance(self) -> Tuple[Dict[str, str], str]:
        """Get attendance data for the most recent date from attendance Google Sheet
        Returns tuple of (attendance_dict, date_used)"""
        try:
            attendance_url = get_attendance_sheets_url()
            if not attendance_url:
                raise ValueError("Attendance Google Sheets URL not configured")
            
            spreadsheet = self.gc.open_by_url(attendance_url)
            worksheet = spreadsheet.sheet1
            
            # Get all values
            all_values = worksheet.get_all_values()
            
            if not all_values:
                return {}, ""
            
            # Find the most recent date column
            header_row = all_values[0] if all_values else []
            date_col_index = None
            most_recent_date = None
            most_recent_date_str = ""
            
            # Parse all date columns and find the most recent one
            from datetime import datetime
            
            date_columns = []  # List of (index, date_string, datetime_obj)
            
            for idx, header in enumerate(header_row):
                if idx == 0 or idx == 1:  # Skip column A and column B (B has names)
                    continue
                header_clean = header.strip() if header else ''
                if not header_clean:
                    continue
                
                # Try to parse as date in various formats
                date_obj = None
                for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%B %d, %Y", "%d-%b-%Y", "%d-%b-%y"]:
                    try:
                        date_obj = datetime.strptime(header_clean, date_format)
                        date_columns.append((idx, header_clean, date_obj))
                        break
                    except ValueError:
                        continue
            
            if not date_columns:
                print("No valid date columns found in attendance sheet")
                return {}, ""
            
            # Sort by date (most recent first)
            date_columns.sort(key=lambda x: x[2], reverse=True)
            date_col_index, most_recent_date_str, most_recent_date = date_columns[0]
            
            print(f"Using most recent date: {most_recent_date_str} (column index: {date_col_index})")
            
            # Get attendance data from the most recent date column
            # Names are in column B (index 1), not column A
            attendance_dict = {}
            for row_idx in range(1, len(all_values)):  # Start from row 2 (index 1)
                if row_idx < len(all_values) and all_values[row_idx]:
                    name = all_values[row_idx][1] if len(all_values[row_idx]) > 1 and all_values[row_idx][1] else ''
                    if name and name.strip():
                        name_clean = name.strip()
                        # Get attendance status from the date column
                        if date_col_index < len(all_values[row_idx]):
                            status = all_values[row_idx][date_col_index].strip() if all_values[row_idx][date_col_index] else 'Not Present'
                            attendance_dict[name_clean] = status
                        else:
                            attendance_dict[name_clean] = 'Not Present'
            
            return attendance_dict, most_recent_date_str
        except Exception as e:
            print(f"Error getting most recent attendance: {e}")
            import traceback
            print(traceback.format_exc())
            return {}, ""

    def submit_attendance(self, date: str, attendance: Dict[str, str]) -> bool:
        """Submit attendance to attendance Google Sheet"""
        try:
            attendance_url = get_attendance_sheets_url()
            if not attendance_url:
                raise ValueError("Attendance Google Sheets URL not configured")
            
            spreadsheet = self.gc.open_by_url(attendance_url)
            worksheet = spreadsheet.sheet1
            
            # Format date to match expected format (YYYY-MM-DD or keep as is)
            # The date comes from frontend as YYYY-MM-DD format
            formatted_date = date
            
            # Get all values to find the date column
            all_values = worksheet.get_all_values()
            
            if not all_values:
                raise ValueError("Attendance sheet is empty")
            
            # Find date column (starting from B1)
            header_row = all_values[0] if all_values else []
            date_col_index = None
            
            # Check if date already exists in header (try both formats)
            for idx, header in enumerate(header_row):
                if idx == 0 or idx == 1:  # Skip column A and column B (B has names)
                    continue
                header_clean = header.strip() if header else ''
                if header_clean == formatted_date or header_clean == date:
                    date_col_index = idx
                    break
            
            # If date not found, add it to the next available column
            if date_col_index is None:
                # Find the next empty column after B (index 1)
                date_col_index = 1  # Start from B (index 1)
                found_empty = False
                for idx in range(1, len(header_row)):
                    if not header_row[idx] or header_row[idx].strip() == '':
                        date_col_index = idx
                        found_empty = True
                        break
                
                # If no empty column found, use the next column after the last one
                if not found_empty:
                    date_col_index = len(header_row)
                
                # Update header with date (gspread uses 1-indexed, so date_col_index + 1)
                # date_col_index is 0-indexed from Python list, so we add 1 for gspread
                worksheet.update_cell(1, date_col_index + 1, formatted_date)
                print(f"Added date '{formatted_date}' to column {date_col_index + 1} (B={2})")
            
            # Get all names from column B (index 1, starting from row 2) with case-insensitive matching
            # Normalize names by stripping whitespace to ensure consistent matching
            names = []
            names_lower_to_original = {}  # Map lowercase to original casing
            for row_idx in range(1, len(all_values)):  # Start from row 2 (index 1)
                if row_idx < len(all_values) and all_values[row_idx]:
                    name = all_values[row_idx][1] if len(all_values[row_idx]) > 1 and all_values[row_idx][1] else ''
                    if name and name.strip():  # Only add non-empty names
                        name_clean = name.strip()  # Normalize by stripping whitespace
                        names.append(name_clean)
                        names_lower_to_original[name_clean.lower()] = name_clean
            
            print(f"Found {len(names)} existing names in sheet: {names[:5]}...")
            print(f"Updating attendance for date column index: {date_col_index} (column {date_col_index + 1})")
            
            # Create case-insensitive lookup for attendance data
            # Normalize names by stripping whitespace to ensure proper matching
            attendance_lower = {name.strip().lower(): (name.strip(), status) for name, status in attendance.items()}
            
            # Update attendance for each member (case-insensitive matching)
            for row_idx, name in enumerate(names, start=2):  # Start from row 2 (1-indexed)
                name_lower = name.lower()
                
                # Find matching attendance (case-insensitive)
                if name_lower in attendance_lower:
                    matched_name, status = attendance_lower[name_lower]
                    # Update the cell (row, col) - both are 1-indexed in gspread
                    # date_col_index is 0-indexed from list, so add 1 for gspread
                    worksheet.update_cell(row_idx, date_col_index + 1, status)
                    print(f"Updated {name}: {status} at row {row_idx}, col {date_col_index + 1}")
                else:
                    # If not in attendance dict, set to "Not Present"
                    worksheet.update_cell(row_idx, date_col_index + 1, "Not Present")
            
            # Also add any new members that aren't in the sheet yet (case-insensitive check)
            existing_names_lower = set(name.lower() for name in names)
            new_members = {}
            for name, status in attendance.items():
                # Normalize name by stripping whitespace for consistent matching
                name_normalized = name.strip()
                name_lower = name_normalized.lower()
                if name_lower not in existing_names_lower:
                    # Avoid duplicates by checking if we already added this name
                    if name_lower not in new_members:
                        new_members[name_lower] = (name_normalized, status)
            
            if new_members:
                # Add new members to the end
                next_row = len(all_values) + 1
                for name_lower, (original_name, status) in new_members.items():
                    # Check if this name already exists in the sheet (double-check)
                    if name_lower not in existing_names_lower:
                        # Add name in column B (index 1, which is column 2 in 1-indexed)
                        worksheet.update_cell(next_row, 2, original_name)
                        # Add attendance status
                        worksheet.update_cell(next_row, date_col_index + 1, status)
                        existing_names_lower.add(name_lower)  # Track to prevent duplicates
                        print(f"Added new member {original_name}: {status} at row {next_row}")
                        next_row += 1
            
            return True
        except Exception as e:
            print(f"Error submitting attendance: {e}")
            import traceback
            print(traceback.format_exc())
            raise

    def parse_attendance_file(self, file_bytes: bytes, filename: str) -> Dict[str, str]:
        """
        Parse an uploaded attendance file (Excel or CSV) and extract attendance data.
        Looks for names in the first column and ticks/checkmarks in subsequent columns.
        Returns a dictionary mapping names to "Present" or "Not Present"
        """
        try:
            # Determine file type
            is_excel = filename.lower().endswith(('.xlsx', '.xls'))
            is_csv = filename.lower().endswith('.csv')
            
            if not (is_excel or is_csv):
                raise ValueError("Unsupported file type. Please upload Excel (.xlsx, .xls) or CSV (.csv) file.")
            
            # Read file into DataFrame
            if is_excel:
                df = pd.read_excel(io.BytesIO(file_bytes), header=None)
            else:
                df = pd.read_csv(io.BytesIO(file_bytes), header=None)
            
            if df.empty:
                raise ValueError("File is empty")
            
            attendance_dict: Dict[str, str] = {}
            seen_names_lower = {}  # Track seen names (case-insensitive) to prevent duplicates
            
            # Find the name column (usually first column, but check for common headers)
            name_col_idx = 0
            start_row = 0
            
            # Check if first row is header
            first_row = df.iloc[0].astype(str).str.lower().str.strip()
            if any(keyword in ' '.join(first_row.values) for keyword in ['name', 'member', 'person', 'attendee']):
                start_row = 1  # Skip header row
            
            # Process each row
            for idx in range(start_row, len(df)):
                row = df.iloc[idx]
                
                # Get name from first column
                name = str(row.iloc[name_col_idx]).strip() if pd.notna(row.iloc[name_col_idx]) else ""
                
                if not name or name.lower() in ['nan', 'none', '']:
                    continue
                
                # Normalize name (trim whitespace, title case for consistency)
                name_normalized = name.strip()
                name_lower = name_normalized.lower()
                
                # Check if we've seen this name before (case-insensitive)
                if name_lower in seen_names_lower:
                    # Use the original casing from first occurrence, but update status if this one is Present
                    original_name = seen_names_lower[name_lower]
                    # If current row has Present, prefer that (last occurrence wins for Present status)
                    pass  # We'll check and update below
                else:
                    seen_names_lower[name_lower] = name_normalized
                
                # Check subsequent columns for ticks/checkmarks
                # Common tick indicators: ✓, ✔, ☑, ✓, X, x, Yes, Y, 1, P, Present, √
                tick_indicators = ['✓', '✔', '☑', '✓', 'x', 'yes', 'y', '1', 'p', 'present', '√', 'true', 't']
                
                is_present = False
                
                # Check all columns after the name column
                for col_idx in range(name_col_idx + 1, len(row)):
                    cell_value = str(row.iloc[col_idx]).strip().lower() if pd.notna(row.iloc[col_idx]) else ""
                    
                    if not cell_value or cell_value == 'nan':
                        continue
                    
                    # Check if cell contains a tick indicator
                    if any(indicator in cell_value for indicator in tick_indicators):
                        is_present = True
                        break
                    
                    # Also check for checkmark characters directly
                    if any(char in cell_value for char in ['✓', '✔', '☑', '√']):
                        is_present = True
                        break
                
                # Store attendance status (use normalized name, last occurrence wins)
                # If name already exists, update only if current is Present (to avoid overwriting Present with Not Present)
                if name_lower in seen_names_lower:
                    original_name = seen_names_lower[name_lower]
                    # If we already have this name, only update if current status is Present
                    # (to preserve Present status if it appears anywhere)
                    if is_present or name_lower not in attendance_dict:
                        attendance_dict[original_name] = "Present" if is_present else "Not Present"
                else:
                    attendance_dict[name_normalized] = "Present" if is_present else "Not Present"
            
            print(f"Parsed attendance file: {len(attendance_dict)} unique names found")
            return attendance_dict
            
        except Exception as e:
            print(f"Error parsing attendance file: {e}")
            import traceback
            print(traceback.format_exc())
            raise ValueError(f"Error parsing attendance file: {str(e)}")
