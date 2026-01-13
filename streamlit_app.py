import streamlit as st
import pandas as pd
import io
import xlsxwriter
from datetime import date
import base64
import hashlib
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from PIL import Image
import json

# --- Page Configuration ---
st.set_page_config(page_title="Teck Ghee Admin Portal", layout="wide", initial_sidebar_state="collapsed")

# --- Authentication Functions ---
def get_users_db():
    """Connect to Google Sheets and get users data"""
    try:
        # Get credentials from Streamlit secrets
        creds_dict = st.secrets["connections"]["gsheets"]

        # Create credentials object
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])

        # Authorize gspread client
        gc = gspread.authorize(creds)

        # Open the spreadsheet
        spreadsheet_url = creds_dict["spreadsheet"]
        spreadsheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
        sh = gc.open_by_key(spreadsheet_id)

        # List all worksheets to help debug
        worksheets = sh.worksheets()
        worksheet_names = [ws.title for ws in worksheets]
        print(f"Available worksheets: {worksheet_names}")  # Debug info

        # Check if "Users" worksheet exists
        if "Users" not in worksheet_names:
            st.error("❌ **Google Sheet Setup Required**")
            st.error("The worksheet 'Users' doesn't exist in your Google Sheet.")
            st.info("📋 **To fix this:**")
            st.info("1. Open your Google Sheet")
            st.info("2. Create a new worksheet named exactly 'Users' (case-sensitive)")
            st.info("3. Add these column headers in row 1: username, password, role, email")
            st.info("4. Add user data in the rows below")
            st.info(f"5. Available worksheets in your sheet: {worksheet_names}")
            return pd.DataFrame()

        # Read the Users worksheet
        worksheet = sh.worksheet("Users")
        data = worksheet.get_all_records()

        return pd.DataFrame(data)

    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "access" in error_msg.lower():
            st.error("❌ **Permission Error**")
            st.error("The service account doesn't have access to your Google Sheet.")
            st.info("📋 **To fix this:**")
            st.info("1. Open your Google Sheet")
            st.info(f"2. Share it with: tgyn-admin@tgyn-admin.iam.gserviceaccount.com")
            st.info("3. Give 'Editor' permissions")
        else:
            st.error(f"❌ Error connecting to Google Sheets: {error_msg}")
        return pd.DataFrame()

def check_credentials(username, password):
    """Check if username and password are valid against Google Sheets"""
    df = get_users_db()

    if df.empty:
        return False, None

    # Clean whitespace
    username = username.strip()
    password = password.strip()

    # Filter for the specific user
    user_match = df[df['username'].str.strip() == username]

    if not user_match.empty:
        # Check password (assuming passwords are stored in plain text for now)
        stored_password = str(user_match.iloc[0]['password']).strip()
        if stored_password == password:
            return True, user_match.iloc[0]

    return False, None

# --- Telegram Functions ---

def send_telegram_notification_sync(event_name, excel_data, excel_filename, document_type):
    """Synchronous function for sending to Telegram with live status updates"""
    import requests
    import json
    import tempfile
    import os

    # Create a status container for live updates
    status_container = st.container()

    with status_container:
        st.info(f"📋 Sending {document_type} for event: **{event_name}**")
        progress_text = st.empty()

    try:
        # Step 1: Get credentials
        progress_text.write("🔑 Getting Telegram credentials...")

        token = st.secrets["telegram"]["token"]
        group_id = st.secrets["telegram"]["group_id"]

        progress_text.write(f"✅ Credentials loaded. Group ID: {group_id}")

        # Step 2: Prepare file
        progress_text.write(f"💾 Preparing {document_type} file...")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(excel_data)
            excel_file_path = tmp_file.name

        progress_text.write(f"✅ File prepared: {excel_filename}")

        # Step 3: Send document
        progress_text.write("📤 Sending document to Telegram...")

        url = f"https://api.telegram.org/bot{token}/sendDocument"
        with open(excel_file_path, 'rb') as file:
            files = {'document': (excel_filename, file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {
                'chat_id': group_id,
                'caption': f"📄 {excel_filename} - Ready for approval"
            }

            response = requests.post(url, files=files, data=data, timeout=30)
            doc_result = response.json()

            # Debug: Show full API response
            with st.expander("🔍 Document API Response (Debug)"):
                st.json(doc_result)

        if not doc_result.get('ok'):
            st.error(f"❌ Document send failed!")
            st.error(f"**Error:** {doc_result.get('description', 'Unknown error')}")
            st.error(f"**Error Code:** {doc_result.get('error_code', 'N/A')}")
            # Clean up temp file
            try:
                os.unlink(excel_file_path)
            except:
                pass
            return False

        progress_text.write("✅ Document sent successfully!")

        # Step 4: Send poll
        progress_text.write(f"🗳️ Creating approval poll for '{event_name}'...")

        poll_url = f"https://api.telegram.org/bot{token}/sendPoll"
        poll_data = {
            'chat_id': group_id,
            'question': f"Approval for {event_name}",
            'options': json.dumps(["Yes ✅", "No ❌"]),
            'is_anonymous': False,
            'allows_multiple_answers': False
        }

        poll_response = requests.post(poll_url, data=poll_data, timeout=30)
        poll_result = poll_response.json()

        # Debug: Show full API response
        with st.expander("🔍 Poll API Response (Debug)"):
            st.json(poll_result)

        # Clean up temp file
        try:
            os.unlink(excel_file_path)
        except:
            pass

        if poll_result.get('ok'):
            progress_text.empty()
            st.success("✅ SUCCESS! Document and poll sent to Telegram!")
            st.balloons()
            st.info("📊 Check your Telegram group for the approval poll!")
            return True
        else:
            st.error(f"❌ Poll creation failed!")
            st.error(f"**Error:** {poll_result.get('description', 'Unknown error')}")
            st.error(f"**Error Code:** {poll_result.get('error_code', 'N/A')}")
            return False

    except KeyError as e:
        st.error(f"❌ Configuration Error: Missing key {str(e)}")
        st.error("💡 **Check your `.streamlit/secrets.toml` file has:**")
        st.code('[telegram]\ntoken = "YOUR_BOT_TOKEN"\ngroup_id = "YOUR_GROUP_ID"', language='toml')
        return False

    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. Please try again.")
        return False

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network error: {str(e)}")
        return False

    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        st.error("💡 **Common issues:**")
        st.error("1. Bot not added to the group")
        st.error("2. Bot doesn't have permission to send messages")
        st.error("3. Invalid group_id (should be negative for groups)")
        return False

def login_page():
    """Display the login page"""
    # Page title
    st.title("🔐 Portal Login")

    # Login form
    with st.form("login_form"):
        st.subheader("Please Login")

        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")

        submit_button = st.form_submit_button("Login")

        if submit_button:
            if not username_input or not password_input:
                st.error("Please enter both username and password")
            else:
                is_valid, user_data = check_credentials(username_input, password_input)
                if is_valid:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_data
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Incorrect username or password")


def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    logo_b64 = get_base64_of_bin_file("Image/logo_nobg.png")
except:
    logo_b64 = ""

# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if "page" not in st.session_state:
    st.session_state["page"] = "Budget Planner"
# Session state for storing generated Excel data (persists across button clicks)
if "budget_excel_data" not in st.session_state:
    st.session_state.budget_excel_data = None
if "budget_excel_filename" not in st.session_state:
    st.session_state.budget_excel_filename = None
if "budget_event_name" not in st.session_state:
    st.session_state.budget_event_name = None
if "soa_excel_data" not in st.session_state:
    st.session_state.soa_excel_data = None
if "soa_excel_filename" not in st.session_state:
    st.session_state.soa_excel_filename = None
if "soa_event_name" not in st.session_state:
    st.session_state.soa_event_name = None

# Session state for receipt processing
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []
if "processed_receipts" not in st.session_state:
    st.session_state.processed_receipts = []
if "soa_expense_data" not in st.session_state:
    st.session_state.soa_expense_data = pd.DataFrame([
        {"Description": "Food & Bev", "Actual ($)": 0.0, "Budgeted ($)": 0.0},
        {"Description": "Logistics", "Actual ($)": 0.0, "Budgeted ($)": 0.0},
        {"Description": "Transport", "Actual ($)": 0.0, "Budgeted ($)": 0.0}
    ])
if "soa_income_data" not in st.session_state:
    st.session_state.soa_income_data = pd.DataFrame([
        {"Description": "Participant Fees", "Actual ($)": 0.0, "Budgeted ($)": 0.0},
        {"Description": "Misc Income", "Actual ($)": 0.0, "Budgeted ($)": 0.0}
    ])

# --- Authentication Check ---
if not st.session_state.logged_in:
    login_page()
    st.stop()  # Stop execution here if not authenticated

# Get current page name for header
current_page = "Budget Planner" if st.session_state["page"] == "Budget Planner" else "SOA"

import streamlit.components.v1 as components

# --- Custom Fixed Header & CSS ---
st.markdown(f"""
    <style>
        /* Hide default Streamlit header decoration */
        header {{visibility: hidden;}}

        /* Custom Fixed Header */
        .fixed-header {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #2A0944; /* Theme Background Purple */
            color: white;
            padding: 1rem 2rem;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            height: 90px;
        }}
        .fixed-header-left {{
            display: flex;
            align-items: center;
        }}
        .fixed-header img {{
            height: 70px;
            margin-right: 20px;
        }}
        .fixed-header h1 {{
            margin: 0;
            font-size: 1.8rem;
            color: white;
            font-family: sans-serif;
            font-weight: 600;
        }}
        .fixed-header-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        /* Navigation Links Styles */
        .nav-links-container {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .nav-link {{
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            font-size: 1rem;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: all 0.3s ease;
            cursor: pointer;
        }}

        .nav-link:hover {{
            color: white;
            background-color: rgba(255, 255, 255, 0.1);
        }}

        .nav-link.active {{
            color: white;
            background: linear-gradient(135deg, #D0BCFF 0%, #3B185F 100%);
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(208, 188, 255, 0.4);
        }}

        /* Adjust main content to start below the fixed header */
        .block-container {{
            padding-top: 6rem;
            padding-left: 2rem;
            padding-right: 2rem;
            padding-bottom: 2rem;
        }}

        /* Hide Streamlit's default button styling in header */
        .fixed-header .stButton > button {{
            background: none;
            border: none;
            color: inherit;
            font: inherit;
            cursor: pointer;
            padding: 0.3rem 0.8rem;
            border-radius: 6px;
            transition: all 0.3s ease;
            width: auto !important;
            height: auto !important;
            min-height: auto !important;
            font-size: 0.9rem;
        }}

        .fixed-header .stButton > button:hover {{
            color: white;
            background-color: rgba(255, 255, 255, 0.1);
        }}

        .fixed-header .stButton > button:focus {{
            outline: none;
            box-shadow: none;
        }}
    </style>
""", unsafe_allow_html=True)

# Define active states for styling
budget_active = st.session_state["page"] == "Budget Planner"
soa_active = st.session_state["page"] == "Statement of Accounts (SOA)"

# Header layout: Logo | Navigation Buttons (shifted right)
col_logo, col_nav = st.columns([2, 3])

with col_logo:
    st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="height: 70px;">', unsafe_allow_html=True)

with col_nav:
    # Navigation buttons in a horizontal layout
    nav_col1, nav_col2, nav_col3 = st.columns([2, 2, 1])  # Budget | SOA | Logout

    with nav_col1:
        # Budget Planner button
        if st.button("💰 Budget Planner", key="nav_budget",
                    help="Switch to Budget Planner",
                    use_container_width=True):
            st.session_state["page"] = "Budget Planner"
            st.rerun()

    with nav_col2:
        # SOA button
        if st.button("📄 SOA", key="nav_soa",
                    help="Switch to Statement of Accounts",
                    use_container_width=True):
            st.session_state["page"] = "Statement of Accounts (SOA)"
            st.rerun()

    with nav_col3:
        # Logout button
        if st.button("🚪 Logout", key="logout",
                    help="Logout from the portal",
                    use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

# Apply conditional styling after buttons are rendered
if budget_active:
    st.markdown("""
        <style>
            button[data-testid*="nav_budget"] {
                color: white !important;
                background: linear-gradient(135deg, #D0BCFF 0%, #3B185F 100%) !important;
                font-weight: 600 !important;
                box-shadow: 0 2px 8px rgba(208, 188, 255, 0.4) !important;
            }
        </style>
    """, unsafe_allow_html=True)
elif soa_active:
    st.markdown("""
        <style>
            button[data-testid*="nav_soa"] {
                color: white !important;
                background: linear-gradient(135deg, #D0BCFF 0%, #3B185F 100%) !important;
                font-weight: 600 !important;
                box-shadow: 0 2px 8px rgba(208, 188, 255, 0.4) !important;
            }
        </style>
    """, unsafe_allow_html=True)

# Simple page navigation handling
# This is now handled directly by the Streamlit buttons in the header

# --- MAIN APP CONTENT ---
st.success(f"Welcome back, {st.session_state.user_info['username']}!")

# User is now logged in and can access the main application

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

def list_available_models():
    """List available Gemini models for debugging"""
    try:
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)

        models = genai.list_models()
        vision_models = []

        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                vision_models.append(model.name)

        return vision_models
    except Exception as e:
        st.error(f"❌ Error listing models: {str(e)}")
        return []

def initialize_gemini():
    """Initialize Gemini API with API key"""
    try:
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)

        # First, check what models are available
        available_models = list_available_models()

        if not available_models:
            st.error("❌ No models available. Please check your Gemini API key.")
            return None

        # Try different model names in order of preference (prioritize Gemini 2.5 Flash)
        preferred_models = ['gemini-2.5-flash', 'gemini-2.0-flash-exp', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro-vision', 'gemini-pro']

        for model_name in preferred_models:
            if model_name in available_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    if model_name == 'gemini-2.5-flash':
                        st.success(f"✅ Using preferred model: {model_name} (Gemini 2.5 Flash)")
                    elif model_name.startswith('gemini-2.0'):
                        st.success(f"✅ Using advanced model: {model_name} (Gemini 2.0 Flash)")
                    elif model_name == 'gemini-1.5-pro':
                        st.success(f"✅ Using model: {model_name} (Gemini 1.5 Pro)")
                    else:
                        st.success(f"✅ Using model: {model_name}")
                    return model
                except Exception as e:
                    st.warning(f"Model {model_name} failed to initialize: {str(e)}")
                    continue

        # If preferred models don't work, try any available vision model
        for model_name in available_models:
            try:
                model = genai.GenerativeModel(model_name)
                st.info(f"ℹ️ Using fallback model: {model_name}")
                return model
            except Exception as e:
                continue

        st.error("❌ No suitable Gemini model found. Please check your API key and model availability.")
        with st.expander("🔍 Available Models"):
            st.write("Available models:")
            for model in available_models:
                st.write(f"- {model}")
        return None

    except KeyError:
        st.error("❌ Gemini API key not found in secrets. Please add your API key to `.streamlit/secrets.toml`")
        st.code('[gemini]\napi_key = "YOUR_GEMINI_API_KEY"', language='toml')
        return None

def process_receipt_image(image, filename):
    """Process a receipt image with Gemini API to extract items"""
    try:
        model = initialize_gemini()
        if not model:
            return None

        # Convert PIL Image to bytes if needed
        if isinstance(image, Image.Image):
            import io as io_module
            img_byte_arr = io_module.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
        else:
            img_byte_arr = image

        # Create prompt for receipt analysis with categorization
        prompt = """
        You are a receipt analysis expert for event management. Analyze this receipt and categorize items as INCOME or EXPENDITURE.

        IMPORTANT: Return ONLY valid JSON with this exact structure:
        {
            "merchant_name": "Store or restaurant name",
            "income_items": [
                {
                    "description": "Item name (e.g., 'Registration Fee', 'Donation')",
                    "quantity": 1,
                    "total_amount": 50.00,
                    "category": "registration_fees"
                }
            ],
            "expenditure_items": [
                {
                    "description": "Item name (e.g., 'Chicken Rice', 'Venue Rental')",
                    "quantity": 1,
                    "total_amount": 10.50,
                    "category": "food_beverage"
                }
            ],
            "total_income": 50.00,
            "total_expenditure": 10.50,
            "tax_amount": 0.80
        }

        INCOME Categories: registration_fees, donations, sponsorships, ticket_sales, merchandise_sales
        EXPENDITURE Categories: food_beverage, logistics, transport, equipment, materials, printing, marketing

        Rules:
        1. Categorize each item as either INCOME or EXPENDITURE based on context
        2. Use clear, descriptive names
        3. Quantity must be a number (default to 1 if not shown)
        4. Amounts must be numbers without currency symbols
        5. Most receipts are EXPENDITURE (purchases), but some might be INCOME (collections)
        6. Always include tax_amount if visible on the receipt (GST, service tax, etc.)
        7. If tax is included in item prices, still extract it separately if shown
        8. Return ONLY the JSON, no other text
        """

        # Process the image
        try:
            response = model.generate_content([
                prompt,
                {
                    "mime_type": "image/png",
                    "data": base64.b64encode(img_byte_arr).decode()
                }
            ])
        except Exception as api_error:
            st.error(f"❌ API Error: {str(api_error)}")
            st.error("💡 This could be due to:")
            st.error("- Invalid API key")
            st.error("- Model not available for your account")
            st.error("- Rate limiting")
            return None

        # Parse the response
        try:
            response_text = response.text.strip()
        except Exception as text_error:
            st.error(f"❌ Error getting response text: {str(text_error)}")
            return None

        # Clean the response text
        original_response = response_text

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        # Try to find JSON in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            response_text = response_text[json_start:json_end]

        try:
            parsed_data = json.loads(response_text)
            return parsed_data
        except json.JSONDecodeError as e:
            st.error(f"❌ Failed to parse Gemini response as JSON: {e}")
            with st.expander("🔍 Raw AI Response"):
                st.text("Original response:")
                st.code(original_response)
                st.text("Cleaned response:")
                st.code(response_text)
            return None

    except Exception as e:
        st.error(f"❌ Error processing receipt: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

def extract_items_from_receipts(processed_receipts):
    """Extract and combine items from multiple processed receipts with categorization"""
    income_items = []
    expenditure_items = []

    for receipt_data in processed_receipts:
        if receipt_data:
            # Handle new categorization format
            if "income_items" in receipt_data:
                for item in receipt_data["income_items"]:
                    standardized_item = {
                        "Description": item.get("description", "Unknown Income Item"),
                        "Qty": item.get("quantity", 1),
                        "Actual ($)": item.get("total_amount", 0.0),
                        "Budgeted ($)": 0.0,
                        "Category": item.get("category", "misc_income")
                    }
                    income_items.append(standardized_item)

            if "expenditure_items" in receipt_data:
                for item in receipt_data["expenditure_items"]:
                    standardized_item = {
                        "Description": item.get("description", "Unknown Expense Item"),
                        "Qty": item.get("quantity", 1),
                        "Actual ($)": item.get("total_amount", 0.0),
                        "Budgeted ($)": 0.0,
                        "Category": item.get("category", "misc_expense")
                    }
                    expenditure_items.append(standardized_item)

            # Add tax amount as a separate expenditure item if present
            tax_amount = receipt_data.get("tax_amount", 0.0)
            if tax_amount and tax_amount > 0:
                merchant_name = receipt_data.get("merchant_name", "Unknown Store")
                tax_item = {
                    "Description": f"Tax - {merchant_name}",
                    "Qty": 1,
                    "Actual ($)": tax_amount,
                    "Budgeted ($)": 0.0,
                    "Category": "tax"
                }
                expenditure_items.append(tax_item)

            # Handle legacy format (backwards compatibility)
            elif "items" in receipt_data:
                # Assume all legacy items are expenditures
                for item in receipt_data["items"]:
                    standardized_item = {
                        "Description": item.get("description", "Unknown Item"),
                        "Qty": item.get("quantity", 1),
                        "Actual ($)": item.get("total_amount", 0.0),
                        "Budgeted ($)": 0.0,
                        "Category": "misc_expense"
                    }
                    expenditure_items.append(standardized_item)

                # Also check for tax in legacy format
                tax_amount = receipt_data.get("tax_amount", 0.0)
                if tax_amount and tax_amount > 0:
                    merchant_name = receipt_data.get("merchant_name", "Unknown Store")
                    tax_item = {
                        "Description": f"Tax - {merchant_name}",
                        "Qty": 1,
                        "Actual ($)": tax_amount,
                        "Budgeted ($)": 0.0,
                        "Category": "tax"
                    }
                    expenditure_items.append(tax_item)

    return {
        "income": income_items,
        "expenditure": expenditure_items
    }

# --- EXCEL GENERATOR: BUDGET (Side-by-Side) ---
def generate_budget_excel(event_name, event_date, participants, volunteers, inc_df, exp_df, prep_by, des_prep, vet_by):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    sheet = workbook.add_worksheet("Budget")

    # Styles
    fmt_title = workbook.add_format({'font_name': 'Calibri', 'font_size': 14, 'bold': True, 'align': 'center'})
    fmt_bold = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True})
    fmt_bold_center = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'align': 'center'})
    fmt_header = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'border': 1, 'align': 'center', 'bg_color': '#D9D9D9'})
    fmt_text = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1})
    fmt_currency = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'border': 1, 'num_format': '$#,##0.00'})
    fmt_curr_bold = workbook.add_format({'font_name': 'Calibri', 'font_size': 11, 'bold':True, 'num_format': '$#,##0.00'})
    
    # Columns (A-H)
    sheet.set_column('A:A', 30); sheet.set_column('E:E', 30)
    sheet.set_column('B:B', 12); sheet.set_column('F:F', 12)
    sheet.set_column('C:C', 8);  sheet.set_column('G:G', 8)
    sheet.set_column('D:D', 12); sheet.set_column('H:H', 12)

    # Header (Merged and Centralized A-H)
    sheet.merge_range('A1:H1', "Teck Ghee Youth Network", fmt_title)
    sheet.merge_range('A2:H2', f"{event_date.strftime('%d-%b-%y')}", fmt_bold_center)
    sheet.merge_range('A3:H3', event_name, fmt_bold_center)
    sheet.merge_range('A4:H4', "Projected Statement of Accounts", fmt_bold_center)
    sheet.merge_range('A5:H5', "", fmt_bold_center)
    sheet.merge_range('A6:H6', f"No. of Expected Participants: {participants} | Volunteers: {volunteers}", fmt_bold_center)

    # Insert Logo
    try:
        sheet.insert_image('A1', 'Image/logo_nobg.png', {'x_scale': 0.15, 'y_scale': 0.15, 'x_offset': 10, 'y_offset': 10})
    except:
        pass

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
    sheet.write(r_tot+2, 4, "Deficit/Surplus:", fmt_bold)
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
    
    # Approved By (Below Vetted By)
    r_app = r_sig + 6
    sheet.write(r_app, 4, "_"*25); sheet.write(r_app+1, 4, "Approved By:")
    sheet.write(r_app+2, 4, "[Name]"); sheet.write(r_app+3, 4, "Chairman/Treasurer")
    sheet.write(r_app+4, 4, "Teck Ghee Youth Network")

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
    sheet.write(r, 1, "EXPENSES", fmt_table_header)
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

# Get current page
page = st.session_state["page"]

if page == "Budget Planner":
    st.title("💰 Event Budget Planner")
    
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
        if not e_name or e_name.strip() == "":
            st.warning("⚠️ Please enter an Event Name first")
        else:
            f = generate_budget_excel(e_name, e_date, pax, vol, ed_i, ed_e, prep, des_p, vet)
            # Store in session state so data persists across reruns
            st.session_state.budget_excel_data = f.getvalue()
            st.session_state.budget_excel_filename = f"{e_name}_Budget.xlsx"
            st.session_state.budget_event_name = e_name
            st.success("✅ Budget generated! You can now download or send to Telegram.")

    # Show download and telegram buttons if we have generated data
    if st.session_state.budget_excel_data is not None:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.download_button(
                "📥 Download Budget.xlsx",
                st.session_state.budget_excel_data,
                st.session_state.budget_excel_filename,
                key="download_budget"
            )
        with col2:
            if st.button("📤 Send to Telegram", key="telegram_budget"):
                try:
                    send_telegram_notification_sync(
                        st.session_state.budget_event_name,
                        st.session_state.budget_excel_data,
                        st.session_state.budget_excel_filename,
                        "Budget"
                    )
                except Exception as e:
                    st.error(f"❌ Telegram error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        with col3:
            if st.button("🗑️ Clear", key="clear_budget"):
                st.session_state.budget_excel_data = None
                st.session_state.budget_excel_filename = None
                st.session_state.budget_event_name = None
                st.rerun()

elif page == "Statement of Accounts (SOA)":
    st.title("📄 Statement of Accounts (SOA)")
    
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

    # Create two distinct columns for Income and Expenditure
    st.markdown("""
    <style>
    .income-column { background-color: rgba(208, 188, 255, 0.1); padding: 10px; border-radius: 10px; border-left: 5px solid #D0BCFF; }
    .expense-column { background-color: rgba(59, 24, 95, 0.1); padding: 10px; border-radius: 10px; border-left: 5px solid #3B185F; }
    </style>
    """, unsafe_allow_html=True)

    col_income, col_expense = st.columns([1, 1], gap="large")

    with col_income:
        st.markdown('<div class="income-column">', unsafe_allow_html=True)
        st.subheader("💰 Income Data")
        if st.button("🔄 Reset Income Data", key="reset_income"):
            st.session_state.soa_income_data = pd.DataFrame([
        {"Description": "Participant Fees", "Actual ($)": 0.0, "Budgeted ($)": 0.0},
        {"Description": "Misc Income", "Actual ($)": 0.0, "Budgeted ($)": 0.0}
    ])
            st.rerun()

        ed_i = calculate_soa_totals(st.data_editor(
            st.session_state.soa_income_data,
            num_rows="dynamic",
            use_container_width=True,
            key="income_editor"
        ))
        st.markdown('</div>', unsafe_allow_html=True)

    with col_expense:
        st.markdown('<div class="expense-column">', unsafe_allow_html=True)
        st.subheader("💸 Expenditure Data")
        if st.button("🔄 Reset Expense Data", key="reset_expense"):
            st.session_state.soa_expense_data = pd.DataFrame([
        {"Description": "Food & Bev", "Actual ($)": 0.0, "Budgeted ($)": 0.0},
        {"Description": "Logistics", "Actual ($)": 0.0, "Budgeted ($)": 0.0},
        {"Description": "Transport", "Actual ($)": 0.0, "Budgeted ($)": 0.0}
    ])
            st.rerun()

        ed_e = calculate_soa_totals(st.data_editor(
            st.session_state.soa_expense_data,
            num_rows="dynamic",
            use_container_width=True,
            key="expense_editor"
        ))
        st.markdown('</div>', unsafe_allow_html=True)

    # Live Totals for verification
    tot_inc = ed_i["Actual ($)"].sum()
    tot_exp = ed_e["Actual ($)"].sum()
    st.write(f"**Net Surplus/Deficit (Actual):** ${tot_inc - tot_exp:,.2f}")

    # Receipt Processing Section
    st.markdown("---")
    st.subheader("📸 Upload Receipts for Auto-Processing")

    # Debug section for API key and models
    with st.expander("🔧 Gemini API Debug"):
        st.info("🎯 **Preferred Model:** Gemini 2.5 Flash")
        st.info("If Gemini 2.5 Flash is not available, the system will try Gemini 2.0 Flash, then Gemini 1.5 Pro.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Check Available Models"):
                models = list_available_models()
                if models:
                    st.success(f"✅ Found {len(models)} available models:")
                    for model in models:
                        if 'gemini-2.5-flash' in model:
                            st.write(f"⭐⭐ **{model}** (Preferred - Gemini 2.5 Flash)")
                        elif 'gemini-2.0' in model:
                            st.write(f"⭐ **{model}** (Gemini 2.0 Flash)")
                        elif 'gemini-1.5-pro' in model:
                            st.write(f"🟡 **{model}** (Gemini 1.5 Pro)")
                        elif 'gemini-1.5-flash' in model:
                            st.write(f"🟢 **{model}** (Gemini 1.5 Flash)")
                        else:
                            st.write(f"- {model}")
                else:
                    st.error("❌ No models found. Check your API key.")

        with col2:
            if st.button("🧪 Test API Key"):
                try:
                    api_key = st.secrets["gemini"]["api_key"]
                    if api_key and api_key != "YOUR_GEMINI_API_KEY":
                        genai.configure(api_key=api_key)
                        st.success("✅ API key configured successfully")
                    else:
                        st.error("❌ API key not set or is placeholder")
                except Exception as e:
                    st.error(f"❌ API key test failed: {str(e)}")

    # File uploader for multiple images
    uploaded_files = st.file_uploader(
        "Upload receipt images (PNG, JPG, JPEG)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload multiple receipt images to automatically extract expense items"
    )

    if uploaded_files:
        st.write(f"📎 {len(uploaded_files)} file(s) uploaded")

        # Process button
        if st.button("🔍 Process Receipts with AI", type="primary"):
            with st.spinner("🤖 Analyzing receipts with Gemini AI..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                new_processed_receipts = []
                new_items = []

                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.write(f"Processing receipt {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
                    progress_bar.progress((i) / len(uploaded_files))

                    # Read the image
                    image = Image.open(uploaded_file)

                    # Process with Gemini
                    receipt_data = process_receipt_image(image, uploaded_file.name)

                    if receipt_data:
                        new_processed_receipts.append(receipt_data)
                        status_text.write(f"✅ Processed: {uploaded_file.name}")

                        # Show extracted data in expander
                        with st.expander(f"📄 Receipt: {uploaded_file.name}"):
                            st.write(f"**Merchant:** {receipt_data.get('merchant_name', 'Unknown')}")

                            # Display totals
                            total_income = receipt_data.get('total_income', 0)
                            total_expenditure = receipt_data.get('total_expenditure', 0)
                            tax_amount = receipt_data.get('tax_amount', 0)

                            if total_income > 0:
                                st.write(f"**Income Total:** ${total_income:.2f}")
                            if total_expenditure > 0:
                                st.write(f"**Expenditure Total:** ${total_expenditure:.2f}")
                            if tax_amount > 0:
                                st.write(f"**Tax Amount:** ${tax_amount:.2f}")

                            # Display income items
                            if receipt_data.get('income_items'):
                                st.write("**💰 Income Items:**")
                                for item in receipt_data['income_items']:
                                    st.write(f"- {item['description']}: Qty {item['quantity']}, ${item['total_amount']:.2f}")

                            # Display expenditure items
                            if receipt_data.get('expenditure_items'):
                                st.write("**💸 Expenditure Items:**")
                                for item in receipt_data['expenditure_items']:
                                    st.write(f"- {item['description']}: Qty {item['quantity']}, ${item['total_amount']:.2f}")

                            # Handle legacy format (backwards compatibility)
                            if receipt_data.get('items') and not receipt_data.get('income_items') and not receipt_data.get('expenditure_items'):
                                st.write("**Items:**")
                                for item in receipt_data['items']:
                                    st.write(f"- {item['description']}: Qty {item['quantity']}, ${item['total_amount']:.2f}")
                    else:
                        st.error(f"❌ Failed to process: {uploaded_file.name}")

                progress_bar.progress(1.0)
                status_text.empty()

                # Store processed receipts
                st.session_state.processed_receipts.extend(new_processed_receipts)

                # Extract and add items to appropriate tables
                if new_processed_receipts:
                    categorized_items = extract_items_from_receipts(new_processed_receipts)

                    total_income_items = len(categorized_items["income"])
                    total_expense_items = len(categorized_items["expenditure"])

                    if total_income_items > 0 or total_expense_items > 0:
                        st.success(f"✅ Extracted {total_income_items} income items and {total_expense_items} expense items from receipts!")

                        # Add income items
                        if categorized_items["income"]:
                            new_income_df = pd.DataFrame(categorized_items["income"])
                            st.session_state.soa_income_data = pd.concat([
                                st.session_state.soa_income_data,
                                new_income_df
                            ], ignore_index=True)
                            st.info(f"💰 Added {total_income_items} items to Income table")

                        # Add expenditure items
                        if categorized_items["expenditure"]:
                            new_expense_df = pd.DataFrame(categorized_items["expenditure"])
                            st.session_state.soa_expense_data = pd.concat([
                                st.session_state.soa_expense_data,
                                new_expense_df
                            ], ignore_index=True)
                            st.info(f"💸 Added {total_expense_items} items to Expenditure table")

                        st.success("🎉 Receipt processing complete! Items automatically categorized and added to appropriate tables.")
                    else:
                        st.warning("⚠️ No valid items could be extracted from the receipts.")
                else:
                    st.error("❌ No receipts were successfully processed.")

    # Show previously processed receipts if any
    if st.session_state.processed_receipts:
        with st.expander("📋 Previously Processed Receipts"):
            for i, receipt in enumerate(st.session_state.processed_receipts):
                st.write(f"**Receipt {i+1}:** {receipt.get('merchant_name', 'Unknown Store')}")
                st.write(f"Total: ${receipt.get('total_amount', 0):.2f}")
                if receipt.get('items'):
                    for item in receipt['items']:
                        st.write(f"- {item['description']}: ${item['total_amount']:.2f}")

        # Clear processed receipts button
        if st.button("🗑️ Clear Processed Receipts"):
            st.session_state.processed_receipts = []
            st.rerun()

    if st.button("Generate SOA"):
        if not e_name or e_name.strip() == "":
            st.warning("⚠️ Please enter an Event Name first")
        else:
            f = generate_soa_excel(e_name, e_date, venue, act_code, ed_i, ed_e, prep, des_p, cert, des_c)
            # Store in session state so data persists across reruns
            st.session_state.soa_excel_data = f.getvalue()
            st.session_state.soa_excel_filename = f"{e_name}_SOA.xlsx"
            st.session_state.soa_event_name = e_name
            st.success("✅ SOA generated! You can now download or send to Telegram.")

    # Show download and telegram buttons if we have generated data
    if st.session_state.soa_excel_data is not None:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.download_button(
                "📥 Download SOA.xlsx",
                st.session_state.soa_excel_data,
                st.session_state.soa_excel_filename,
                key="download_soa"
            )
        with col2:
            if st.button("📤 Send to Telegram", key="telegram_soa"):
                try:
                    send_telegram_notification_sync(
                        st.session_state.soa_event_name,
                        st.session_state.soa_excel_data,
                        st.session_state.soa_excel_filename,
                        "SOA"
                    )
                except Exception as e:
                    st.error(f"❌ Telegram error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        with col3:
            if st.button("🗑️ Clear", key="clear_soa"):
                st.session_state.soa_excel_data = None
                st.session_state.soa_excel_filename = None
                st.session_state.soa_event_name = None
                st.rerun()