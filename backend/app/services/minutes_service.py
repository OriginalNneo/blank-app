import google.generativeai as genai
from pptx import Presentation
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.utils.config import get_gemini_api_key
from pydantic import BaseModel


class MeetingMinutesRequest(BaseModel):
    meeting_title: str = "Corporate Board Meeting"
    date_time: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[str] = None
    absent: Optional[str] = None
    meeting_chair: Optional[str] = None


class MinutesService:
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
            preferred_models = ['gemini-2.0-flash-exp', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']

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

    def extract_text_from_powerpoint(self, pptx_file) -> str:
        """Extract all text content from PowerPoint presentation"""
        try:
            # Read the file content into bytes if it's a file-like object
            if hasattr(pptx_file, 'read'):
                # Reset file pointer to beginning
                pptx_file.seek(0)
                file_content = pptx_file.read()
                # Create a BytesIO object for python-pptx
                file_stream = io.BytesIO(file_content)
            else:
                file_stream = pptx_file
            
            prs = Presentation(file_stream)
            full_text = []
            
            for slide_num, slide in enumerate(prs.slides, 1):
                slide_text = []
                slide_text.append(f"--- Slide {slide_num} ---")
                
                # Extract text from all shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text = shape.text.strip()
                        if text:
                            slide_text.append(text)
                    # Handle tables
                    if shape.has_table:
                        table = shape.table
                        for row in table.rows:
                            row_text = []
                            for cell in row.cells:
                                if cell.text.strip():
                                    row_text.append(cell.text.strip())
                            if row_text:
                                slide_text.append(" | ".join(row_text))
                
                if len(slide_text) > 1:  # More than just the slide header
                    full_text.append("\n".join(slide_text))
            
            return "\n\n".join(full_text)
        except Exception as e:
            raise Exception(f"Error extracting text from PowerPoint: {str(e)}")

    def process_powerpoint_with_gemini(self, powerpoint_text: str) -> Dict[str, Any]:
        """Process PowerPoint content with Gemini to extract meeting information"""
        try:
            # Ensure model is initialized
            if not hasattr(self, 'model') or self.model is None:
                print("Model not initialized, initializing now...")
                self.model = self._initialize_gemini_model()
            
            prompt = """
            You are an expert at analyzing meeting presentations and extracting structured information for meeting minutes.

            Analyze the following PowerPoint presentation content and extract:
            1. Meeting title/type
            2. Agenda items (list of topics discussed)
            3. Key discussion points for each agenda item
            4. Decisions made
            5. Action items (if any)
            6. Any dates, locations, or other relevant details mentioned

            Return ONLY valid JSON with this exact structure:
            {
                "meeting_title": "Meeting title or type",
                "agenda_items": [
                    {
                        "item_number": 1,
                        "title": "Agenda item title (e.g., 'Call to Order', 'Approval of Agenda', 'Chair's Report')",
                        "description": "Detailed description of what was discussed or decided for this agenda item",
                        "action_items": ["Action item 1", "Action item 2"]
                    }
                ],
                "extracted_date": "Date mentioned in presentation (if any)",
                "extracted_location": "Location mentioned (if any)",
                "extracted_company": "Company/organization name (if any)"
            }

            Rules:
            1. Standardize agenda items to common meeting formats (Call to Order, Approval of Agenda, Approval of Previous Meeting Minutes, Chair's Report, CEO's Report, Committee Reports, Old Business, New Business, Other Business, Adjournment)
            2. If agenda items are not explicitly stated, infer them from the content structure
            3. Provide detailed descriptions for each agenda item based on the presentation content
            4. Extract action items if mentioned
            5. Return ONLY the JSON, no other text
            """

            # Process the text
            print(f"Processing {len(powerpoint_text)} characters with Gemini...")
            response = self.model.generate_content([
                prompt,
                powerpoint_text
            ])
            print("Got response from Gemini")

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
            return parsed_data

        except Exception as e:
            print(f"Error processing PowerPoint with Gemini: {e}")
            raise Exception(f"Failed to process PowerPoint content: {str(e)}")

    def generate_minutes_word(
        self, 
        request: MeetingMinutesRequest,
        processed_data: Dict[str, Any]
    ) -> bytes:
        """Generate meeting minutes Word document following the standardized format"""
        doc = Document()
        
        # Set page margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        # Helper function to add underline
        def add_underline_paragraph(text, style=None):
            p = doc.add_paragraph()
            if style:
                p.style = style
            run = p.add_run(text)
            run.font.size = Pt(11)
            run.font.name = 'Calibri'
            # Add underline
            run.underline = True
            return p

        # Helper function to add bordered paragraph (for minutes boxes)
        def add_bordered_paragraph(text, bg_color=None):
            p = doc.add_paragraph()
            p.style = 'Normal'
            run = p.add_run(text)
            run.font.size = Pt(11)
            run.font.name = 'Calibri'
            
            # Add border and background color using shading
            pPr = p._element.get_or_add_pPr()
            shd = OxmlElement('w:shd')
            shd.set(qn('w:fill'), bg_color or 'F5F5F5')
            pPr.append(shd)
            
            # Add border
            pBdr = OxmlElement('w:pBdr')
            for border_name in ['top', 'left', 'bottom', 'right']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'single')
                border.set(qn('w:sz'), '4')
                border.set(qn('w:space'), '0')
                border.set(qn('w:color'), '000000')
                pBdr.append(border)
            pPr.append(pBdr)
            
            return p

        # Title - Centered, large, elegant serif font
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.add_run(request.meeting_title)
        title_run.font.size = Pt(20)
        title_run.font.name = 'Times New Roman'
        title_run.bold = True
        
        # Decorative line
        doc.add_paragraph("_" * 80).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph()  # Spacing

        # Meeting Information Section - Two columns using table
        info_table = doc.add_table(rows=3, cols=4)
        info_table.style = 'Light Grid Accent 1'
        
        # Left column
        info_table.cell(0, 0).text = "Date & Time"
        info_table.cell(0, 1).text = request.date_time or "_________________"
        info_table.cell(1, 0).text = "Company"
        info_table.cell(1, 1).text = request.company or "_________________"
        info_table.cell(2, 0).text = "Attendees"
        info_table.cell(2, 1).text = request.attendees or "_________________"
        
        # Right column
        info_table.cell(0, 2).text = "Location"
        info_table.cell(0, 3).text = request.location or "_________________"
        info_table.cell(1, 2).text = "Absent"
        info_table.cell(1, 3).text = request.absent or "_________________"
        
        # Format table cells - remove borders for cleaner look
        try:
            for row in info_table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(11)
                            run.font.name = 'Calibri'
                    # Remove borders safely
                    try:
                        tcPr = cell._element.get_or_add_tcPr()
                        borders = tcPr.find(qn('w:tcBorders'))
                        if borders is not None:
                            tcPr.remove(borders)
                    except:
                        pass  # Ignore border removal errors
        except Exception as e:
            print(f"Warning: Error formatting info table: {e}")
        
        doc.add_paragraph()  # Spacing

        # Agenda Section
        agenda_heading = doc.add_paragraph()
        agenda_heading_run = agenda_heading.add_run("Agenda")
        agenda_heading_run.font.size = Pt(14)
        agenda_heading_run.font.name = 'Times New Roman'
        agenda_heading_run.bold = True
        
        agenda_items = processed_data.get("agenda_items", [])
        # Display agenda in two columns using table
        mid_point = (len(agenda_items) + 1) // 2
        max_rows = max(mid_point, len(agenda_items) - mid_point)
        agenda_table = doc.add_table(rows=max_rows, cols=2)
        
        for i, item in enumerate(agenda_items):
            if i < mid_point:
                agenda_table.cell(i, 0).text = f"• {item.get('title', '')}"
            else:
                agenda_table.cell(i - mid_point, 1).text = f"• {item.get('title', '')}"
        
        # Format agenda table - remove borders
        try:
            for row in agenda_table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(11)
                            run.font.name = 'Calibri'
                    # Remove borders safely
                    try:
                        tcPr = cell._element.get_or_add_tcPr()
                        borders = tcPr.find(qn('w:tcBorders'))
                        if borders is not None:
                            tcPr.remove(borders)
                    except:
                        pass  # Ignore border removal errors
            
            # Remove table-level borders for agenda table
            try:
                tbl = agenda_table._element
                tblPr = tbl.get_or_add_tblPr()
                tblBorders = tblPr.find(qn('w:tblBorders'))
                if tblBorders is not None:
                    tblPr.remove(tblBorders)
            except:
                pass  # Ignore table border removal errors
        except Exception as e:
            print(f"Warning: Error formatting agenda table: {e}")
        
        doc.add_paragraph()  # Spacing

        # Minutes Section
        minutes_heading = doc.add_paragraph()
        minutes_heading_run = minutes_heading.add_run("Minutes")
        minutes_heading_run.font.size = Pt(14)
        minutes_heading_run.font.name = 'Times New Roman'
        minutes_heading_run.bold = True
        
        # Create minutes items with action by column using table
        for item in agenda_items:
            item_num = item.get('item_number', 1)
            title = item.get('title', '')
            description = item.get('description', '')
            action_items = item.get('action_items', [])
            
            # Minutes item header (bold number and title)
            minutes_header = doc.add_paragraph()
            minutes_header_run = minutes_header.add_run(f"{item_num}. {title.upper()}:")
            minutes_header_run.font.size = Pt(11)
            minutes_header_run.font.name = 'Calibri'
            minutes_header_run.bold = True
            
            # Create table for minutes content and action by
            minutes_table = doc.add_table(rows=1, cols=2)
            minutes_table.columns[0].width = Inches(4.5)
            minutes_table.columns[1].width = Inches(2.5)
            
            # Minutes content in left cell with gray background
            content = description
            if action_items:
                content += "\n\nAction Items:\n" + "\n".join([f"• {ai}" for ai in action_items])
            
            minutes_table.cell(0, 0).text = content
            minutes_table.cell(0, 1).text = ""  # Empty for "Action By"
            
            # Format minutes table
            # Left cell - gray background
            left_cell = minutes_table.cell(0, 0)
            for paragraph in left_cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(11)
                    run.font.name = 'Calibri'
            # Add gray background
            tcPr = left_cell._element.get_or_add_tcPr()
            shd = OxmlElement('w:shd')
            shd.set(qn('w:fill'), 'F5F5F5')
            tcPr.append(shd)
            
            # Right cell - action by
            right_cell = minutes_table.cell(0, 1)
            for paragraph in right_cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(11)
                    run.font.name = 'Calibri'
            
            # Add borders to table
            tbl = minutes_table._element
            tblPr = tbl.get_or_add_tblPr()
            tblBorders = OxmlElement('w:tblBorders')
            for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'single')
                border.set(qn('w:sz'), '4')
                border.set(qn('w:space'), '0')
                border.set(qn('w:color'), '000000')
                tblBorders.append(border)
            tblPr.append(tblBorders)
            
            doc.add_paragraph()  # Spacing between items

        # Adjournment Section
        doc.add_paragraph()  # Spacing
        adjournment_heading = doc.add_paragraph()
        adjournment_heading_run = adjournment_heading.add_run("Adjournment")
        adjournment_heading_run.font.size = Pt(14)
        adjournment_heading_run.font.name = 'Times New Roman'
        adjournment_heading_run.bold = True
        
        chair = request.meeting_chair or "[Meeting Chair]"
        time = request.date_time or "[Meeting Time]"
        adjournment_text = f"The meeting was adjourned by {chair} at {time}."
        adjournment_p = doc.add_paragraph(adjournment_text)
        for run in adjournment_p.runs:
            run.font.size = Pt(11)
            run.font.name = 'Calibri'

        # Secretary Notes Section
        doc.add_paragraph()  # Spacing
        doc.add_paragraph()  # Spacing
        
        secretary_heading = doc.add_paragraph()
        secretary_heading_run = secretary_heading.add_run("Secretary Notes:")
        secretary_heading_run.font.size = Pt(14)
        secretary_heading_run.font.name = 'Times New Roman'
        secretary_heading_run.bold = True
        
        # Attending/Helping
        attending_p = doc.add_paragraph()
        run1 = attending_p.add_run("Attending/Helping: ")
        run1.font.size = Pt(11)
        run1.font.name = 'Calibri'
        run2 = attending_p.add_run("_________________")
        run2.underline = True
        run2.font.size = Pt(11)
        run2.font.name = 'Calibri'
        
        # Remarks
        remarks_p = doc.add_paragraph()
        remarks_run1 = remarks_p.add_run("Remarks: ")
        remarks_run1.font.size = Pt(11)
        remarks_run1.font.name = 'Calibri'
        
        # Add underline lines for remarks
        for _ in range(3):
            remarks_line = doc.add_paragraph()
            remarks_line_run = remarks_line.add_run("_________________")
            remarks_line_run.font.size = Pt(11)
            remarks_line_run.font.name = 'Calibri'
            remarks_line_run.underline = True

        # Save to bytes
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output.getvalue()

    def process_powerpoint_and_generate_minutes(
        self,
        pptx_file,
        request: MeetingMinutesRequest
    ) -> bytes:
        """Complete pipeline: Extract from PowerPoint, process with Gemini, generate minutes"""
        try:
            # Ensure we have a BytesIO object
            if hasattr(pptx_file, 'read'):
                # If it's already a BytesIO or file-like object, use it directly
                if hasattr(pptx_file, 'seek'):
                    pptx_file.seek(0)
                file_stream = pptx_file
            else:
                file_stream = io.BytesIO(pptx_file)
            
            # Extract text from PowerPoint
            print("Extracting text from PowerPoint...")
            powerpoint_text = self.extract_text_from_powerpoint(file_stream)
            print(f"Extracted {len(powerpoint_text)} characters from PowerPoint")
            
            # Process with Gemini
            print("Processing with Gemini...")
            processed_data = self.process_powerpoint_with_gemini(powerpoint_text)
            print(f"Processed data: {processed_data}")
            
            # Update request with extracted data if not provided
            if not request.date_time and processed_data.get("extracted_date"):
                request.date_time = processed_data.get("extracted_date")
            if not request.location and processed_data.get("extracted_location"):
                request.location = processed_data.get("extracted_location")
            if not request.company and processed_data.get("extracted_company"):
                request.company = processed_data.get("extracted_company")
            if processed_data.get("meeting_title") and not request.meeting_title:
                request.meeting_title = processed_data.get("meeting_title")
            
            # Generate Word document
            print("Generating Word document...")
            word_data = self.generate_minutes_word(request, processed_data)
            print(f"Generated Word document: {len(word_data)} bytes")
            
            return word_data
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in process_powerpoint_and_generate_minutes: {str(e)}")
            print(f"Traceback: {error_trace}")
            raise Exception(f"Error processing PowerPoint and generating minutes: {str(e)}")
