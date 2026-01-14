from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import StreamingResponse
import io
from typing import Optional

from app.services.minutes_service import MinutesService, MeetingMinutesRequest
from app.services.attendance_service import AttendanceService
from app.routers.auth import get_current_user_dependency

router = APIRouter()

@router.post("/generate")
async def generate_minutes(
    meeting_content: str = Form(...),
    meeting_title: Optional[str] = Form(None),
    date_time: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    attendees: Optional[str] = Form(None),
    absent: Optional[str] = Form(None),
    meeting_chair: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Generate meeting minutes from text content"""
    try:
        if not meeting_content or not meeting_content.strip():
            raise HTTPException(
                status_code=400, 
                detail="Meeting content is required"
            )

        # Create service instance
        minutes_service = MinutesService()

        # Create request object
        request = MeetingMinutesRequest(
            meeting_title=meeting_title or "Corporate Board Meeting",
            date_time=date_time,
            company=company,
            location=location,
            attendees=attendees,
            absent=absent,
            meeting_chair=meeting_chair
        )
        
        # Process content and generate minutes
        word_data = minutes_service.process_content_and_generate_minutes(
            meeting_content,
            request
        )

        # Generate filename
        filename = f"{request.meeting_title.replace(' ', '_')}_Minutes.docx"

        return StreamingResponse(
            io.BytesIO(word_data),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error generating meeting minutes: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        # Check for quota error
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
            raise HTTPException(
                status_code=429, 
                detail="Gemini API quota exceeded. Please wait a few minutes and try again, or check your API billing."
            )
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating meeting minutes: {str(e)}"
        )

@router.post("/preview")
async def preview_minutes(
    meeting_content: str = Form(...),
    meeting_title: Optional[str] = Form(None),
    date_time: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Preview processed content before generating minutes"""
    try:
        if not meeting_content or not meeting_content.strip():
            raise HTTPException(
                status_code=400, 
                detail="Meeting content is required"
            )

        # Create service instance
        print("Creating MinutesService instance...")
        try:
            minutes_service = MinutesService()
            print("MinutesService created successfully")
        except Exception as e:
            print(f"Error creating MinutesService: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Error initializing service: {str(e)}"
            )

        # Process with Gemini (with fallback if it fails)
        print("Processing with Gemini...")
        try:
            processed_data = minutes_service.process_content_with_gemini(meeting_content)
            print("Processing complete")
        except Exception as gemini_error:
            print(f"Gemini processing failed: {gemini_error}")
            # Create fallback structure from content
            print("Using fallback: creating basic structure from content...")
            processed_data = {
                "meeting_title": meeting_title or "Meeting",
                "agenda_items": [
                    {
                        "item_number": 1,
                        "title": "General Discussion",
                        "description": meeting_content[:1000] if len(meeting_content) > 0 else "No content provided.",
                        "action_items": []
                    }
                ],
                "extracted_date": None,
                "extracted_location": None,
                "extracted_company": None
            }
            print("Fallback structure created")

        return {
            "success": True,
            "extracted_data": processed_data,
            "preview_text": meeting_content[:500] + "..." if len(meeting_content) > 500 else meeting_content
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error previewing PowerPoint content: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        # Check for quota error
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
            raise HTTPException(
                status_code=429, 
                detail="Gemini API quota exceeded. Please wait a few minutes and try again, or check your API billing."
            )
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error previewing PowerPoint content: {str(e)}"
        )

@router.get("/members")
async def get_members(
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get list of members from Google Sheets"""
    try:
        attendance_service = AttendanceService()
        members = attendance_service.get_members()
        return {
            "success": True,
            "members": members
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error getting members: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting members: {str(e)}"
        )

@router.post("/attendance")
async def submit_attendance(
    date: str = Form(...),
    attendance: str = Form(...),  # JSON string of {name: "Present"/"Not Present"}
    current_user: dict = Depends(get_current_user_dependency)
):
    """Submit attendance to Google Sheets"""
    try:
        import json
        print(f"Received attendance submission - Date: {date}")
        print(f"Attendance data (raw): {attendance}")
        
        attendance_dict = json.loads(attendance)
        print(f"Parsed attendance dict: {attendance_dict}")
        
        attendance_service = AttendanceService()
        result = attendance_service.submit_attendance(date, attendance_dict)
        
        print(f"Attendance submission successful: {result}")
        
        return {
            "success": True,
            "message": "Attendance submitted successfully"
        }
    except json.JSONDecodeError as json_err:
        print(f"JSON decode error: {json_err}")
        print(f"Raw attendance string: {attendance}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid attendance data format: {str(json_err)}"
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error submitting attendance: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting attendance: {str(e)}"
        )

@router.post("/attendance/upload")
async def upload_attendance_file(
    file: UploadFile = File(...),
    date: str = Form(...),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Upload an attendance file (Excel/CSV) and update attendance based on ticks/checkmarks"""
    try:
        # Read file content
        file_bytes = await file.read()
        
        if not file_bytes:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Parse attendance from file
        attendance_service = AttendanceService()
        attendance_dict = attendance_service.parse_attendance_file(file_bytes, file.filename)
        
        if not attendance_dict:
            raise HTTPException(status_code=400, detail="No attendance data found in file. Please ensure names are in the first column and ticks/checkmarks are in subsequent columns.")
        
        # Submit parsed attendance
        result = attendance_service.submit_attendance(date, attendance_dict)
        
        return {
            "success": True,
            "message": f"Attendance uploaded successfully. Processed {len(attendance_dict)} members.",
            "processed_count": len(attendance_dict),
            "attendance": attendance_dict
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error uploading attendance file: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading attendance file: {str(e)}"
        )
