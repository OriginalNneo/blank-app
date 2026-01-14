from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import io
from typing import Optional

from app.services.minutes_service import MinutesService, MeetingMinutesRequest
from app.routers.auth import get_current_user_dependency

router = APIRouter()

@router.post("/generate")
async def generate_minutes(
    file: UploadFile = File(...),
    meeting_title: Optional[str] = Form(None),
    date_time: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    attendees: Optional[str] = Form(None),
    absent: Optional[str] = Form(None),
    meeting_chair: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Generate meeting minutes from PowerPoint file"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pptx', '.ppt')):
            raise HTTPException(
                status_code=400, 
                detail="Only PowerPoint files (.pptx, .ppt) are supported"
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

        # Read file content
        file_content = await file.read()
        file.file.seek(0)  # Reset file pointer
        
        # Process PowerPoint and generate minutes
        word_data = minutes_service.process_powerpoint_and_generate_minutes(
            io.BytesIO(file_content),
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
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating meeting minutes: {str(e)}"
        )

@router.post("/preview")
async def preview_minutes(
    file: UploadFile = File(...),
    meeting_title: Optional[str] = Form(None),
    date_time: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Preview extracted content from PowerPoint before generating minutes"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pptx', '.ppt')):
            raise HTTPException(
                status_code=400, 
                detail="Only PowerPoint files (.pptx, .ppt) are supported"
            )

        # Create service instance
        print("Creating MinutesService instance...")
        minutes_service = MinutesService()
        print("MinutesService created successfully")

        # Read file content
        print("Reading file content...")
        file_content = await file.read()
        print(f"Read {len(file_content)} bytes from file")
        file.file.seek(0)  # Reset file pointer
        
        # Extract text from PowerPoint
        print("Extracting text from PowerPoint...")
        powerpoint_text = minutes_service.extract_text_from_powerpoint(io.BytesIO(file_content))
        print(f"Extracted {len(powerpoint_text)} characters from PowerPoint")
        
        if not powerpoint_text or len(powerpoint_text.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="No text content found in PowerPoint file. Please ensure the file contains text."
            )

        # Process with Gemini
        print("Processing with Gemini...")
        processed_data = minutes_service.process_powerpoint_with_gemini(powerpoint_text)
        print("Processing complete")

        return {
            "success": True,
            "extracted_data": processed_data,
            "preview_text": powerpoint_text[:500] + "..." if len(powerpoint_text) > 500 else powerpoint_text
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error previewing PowerPoint content: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error previewing PowerPoint content: {str(e)}"
        )
