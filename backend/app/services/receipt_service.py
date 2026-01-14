import google.generativeai as genai
from PIL import Image
import base64
import io
import json
from typing import List, Dict, Any, Optional
from app.utils.config import get_gemini_api_key
from pydantic import BaseModel
import os

class ProcessedReceipt(BaseModel):
    merchant_name: str
    income_items: List[Dict[str, Any]] = []
    expenditure_items: List[Dict[str, Any]] = []
    total_income: float = 0.0
    total_expenditure: float = 0.0
    tax_amount: float = 0.0

class ReceiptService:
    def __init__(self):
        # Get API key from configuration
        api_key = get_gemini_api_key()

        if not api_key:
            raise ValueError("Gemini API key not found in configuration")

        genai.configure(api_key=api_key)
        self.model = self._initialize_gemini_model()

    def _initialize_gemini_model(self):
        """Initialize Gemini model with preferred settings"""
        try:
            # Try preferred models in order
            preferred_models = ['gemini-2.5-flash', 'gemini-2.0-flash-exp', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']

            for model_name in preferred_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    print(f"Using Gemini model: {model_name}")
                    return model
                except Exception as e:
                    print(f"Model {model_name} failed: {e}")
                    continue

            # Fallback to any available model
            models = genai.list_models()
            for model_info in models:
                if 'generateContent' in model_info.supported_generation_methods:
                    try:
                        model = genai.GenerativeModel(model_info.name)
                        print(f"Using fallback model: {model_info.name}")
                        return model
                    except:
                        continue

            raise Exception("No suitable Gemini model found")

        except Exception as e:
            raise Exception(f"Failed to initialize Gemini model: {e}")

    def process_receipt_image(self, image_file) -> Optional[ProcessedReceipt]:
        """Process a receipt image and extract data using Gemini AI"""
        try:
            # Convert uploaded file to PIL Image
            image = Image.open(image_file.file)

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Create prompt for receipt analysis
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
            2. Use clear, descriptive names for PRODUCTS, SERVICES, or TRANSACTIONS only
            3. DO NOT extract personal names (e.g., "Shannon Yap", "Cynthia", "John Doe") as items - these are people, not items
            4. DO NOT extract customer names, staff names, or any person names as item descriptions
            5. Only extract actual products, services, or transaction types (e.g., "Chicken Rice", "Venue Rental", "Registration Fee")
            6. Quantity must be a number (default to 1 if not shown)
            7. Amounts must be numbers without currency symbols
            8. Most receipts are EXPENDITURE (purchases), but some might be INCOME (collections)
            9. Always include tax_amount if visible on the receipt (GST, service tax, etc.)
            10. If tax is included in item prices, still extract it separately if shown
            11. Return ONLY the JSON, no other text
            """

            # Process the image
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": "image/png",
                    "data": base64.b64encode(img_byte_arr).decode()
                }
            ])

            # Parse response
            response_text = response.text.strip()

            # Clean the response text
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Find JSON in response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end]

            # Parse JSON
            parsed_data = json.loads(response_text)

            return ProcessedReceipt(**parsed_data)

        except Exception as e:
            print(f"Error processing receipt: {e}")
            return None

    def extract_items_from_receipts(self, processed_receipts: List[ProcessedReceipt]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract and combine items from multiple processed receipts with deduplication"""
        income_items = []
        expenditure_items = []
        seen_income = set()  # Track seen income items by description
        seen_expenditure = set()  # Track seen expenditure items by description

        # Common patterns that indicate a name rather than an item
        def is_likely_name(description: str) -> bool:
            """Check if description is likely a person's name"""
            desc_lower = description.strip().lower()
            # Single word that looks like a name (capitalized, 2-20 chars)
            if len(desc_lower.split()) <= 2 and desc_lower.replace(' ', '').isalpha():
                # Check if it's a common name pattern (not a product/service)
                common_products = ['tax', 'gst', 'service', 'fee', 'rental', 'food', 'beverage', 
                                 'equipment', 'material', 'printing', 'marketing', 'transport',
                                 'logistics', 'registration', 'donation', 'sponsorship', 'ticket',
                                 'merchandise', 'sale', 'purchase']
                if desc_lower not in common_products:
                    return True
            return False

        for receipt in processed_receipts:
            # Handle income items
            for item in receipt.income_items:
                description = item.get("description", "Unknown Income Item").strip()
                
                # Skip if it looks like a name
                if is_likely_name(description):
                    print(f"Skipping likely name in income items: {description}")
                    continue
                
                # Create unique key for deduplication (description + amount)
                unique_key = f"{description.lower()}_{item.get('total_amount', 0.0)}"
                
                # Only add if not already seen
                if unique_key not in seen_income:
                    seen_income.add(unique_key)
                    standardized_item = {
                        "Description": description,
                        "Qty": item.get("quantity", 1),
                        "Actual ($)": item.get("total_amount", 0.0),
                        "Budgeted ($)": 0.0,
                        "Category": item.get("category", "misc_income")
                    }
                    income_items.append(standardized_item)

            # Handle expenditure items
            for item in receipt.expenditure_items:
                description = item.get("description", "Unknown Expense Item").strip()
                
                # Skip if it looks like a name
                if is_likely_name(description):
                    print(f"Skipping likely name in expenditure items: {description}")
                    continue
                
                # Create unique key for deduplication (description + amount)
                unique_key = f"{description.lower()}_{item.get('total_amount', 0.0)}"
                
                # Only add if not already seen
                if unique_key not in seen_expenditure:
                    seen_expenditure.add(unique_key)
                    standardized_item = {
                        "Description": description,
                        "Qty": item.get("quantity", 1),
                        "Actual ($)": item.get("total_amount", 0.0),
                        "Budgeted ($)": 0.0,
                        "Category": item.get("category", "misc_expense")
                    }
                    expenditure_items.append(standardized_item)

            # Add tax amount as separate expenditure item (with deduplication)
            if receipt.tax_amount and receipt.tax_amount > 0:
                tax_description = f"Tax - {receipt.merchant_name}"
                tax_key = f"{tax_description.lower()}_{receipt.tax_amount}"
                
                if tax_key not in seen_expenditure:
                    seen_expenditure.add(tax_key)
                    tax_item = {
                        "Description": tax_description,
                        "Qty": 1,
                        "Actual ($)": receipt.tax_amount,
                        "Budgeted ($)": 0.0,
                        "Category": "tax"
                    }
                    expenditure_items.append(tax_item)

        return {
            "income": income_items,
            "expenditure": expenditure_items
        }