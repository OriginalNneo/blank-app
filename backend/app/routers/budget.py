from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io

from app.services.budget_service import BudgetService, BudgetRequest
from app.routers.auth import get_current_user_dependency
from app.utils.config import get_telegram_token, get_telegram_group_id

router = APIRouter()

@router.post("/generate")
async def generate_budget(
    request: BudgetRequest,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Generate budget Excel file"""
    try:
        excel_data = BudgetService.generate_budget_excel(request)
        filename = f"{request.event_name}_Budget.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating budget: {str(e)}")

@router.post("/preview")
async def preview_budget(
    request: BudgetRequest,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Generate budget and return data for preview"""
    try:
        import pandas as pd

        income_df = pd.DataFrame(request.income_items)
        expense_df = pd.DataFrame(request.expense_items)

        # Calculate totals
        if not income_df.empty:
            income_df = BudgetService.calculate_budget_totals(income_df)
        if not expense_df.empty:
            expense_df = BudgetService.calculate_budget_totals(expense_df)

        # Calculate summary
        income_total = income_df["$ (Total)"].sum() if not income_df.empty else 0
        expense_total = expense_df["$ (Total)"].sum() if not expense_df.empty else 0
        net = income_total - expense_total

        return {
            "income_total": income_total,
            "expense_total": expense_total,
            "net_amount": net,
            "income_items": income_df.to_dict('records') if not income_df.empty else [],
            "expense_items": expense_df.to_dict('records') if not expense_df.empty else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating budget preview: {str(e)}")

@router.post("/telegram-send")
async def send_budget_to_telegram(
    request: BudgetRequest,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Generate budget and send to Telegram"""
    try:
        import requests
        import json
        import os
        from decouple import config

        # Generate Excel file
        excel_data = BudgetService.generate_budget_excel(request)
        filename = f"{request.event_name}_Budget.xlsx"

        # Get Telegram credentials from configuration
        token = get_telegram_token()
        group_id = get_telegram_group_id()

        if not token or not group_id:
            raise ValueError("Telegram credentials not found in configuration")

        # Send document
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        files = {'document': (filename, io.BytesIO(excel_data), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        data = {
            'chat_id': group_id,
            'caption': f"📄 {filename} - Ready for approval"
        }

        response = requests.post(url, files=files, data=data, timeout=30)
        doc_result = response.json()

        if not doc_result.get('ok'):
            raise HTTPException(status_code=500, detail=f"Document send failed: {doc_result.get('description')}")

        # Send poll
        poll_url = f"https://api.telegram.org/bot{token}/sendPoll"
        poll_data = {
            'chat_id': group_id,
            'question': f"Approval for {request.event_name} Budget",
            'options': '["Yes ✅", "No ❌"]',
            'is_anonymous': False,
            'allows_multiple_answers': False
        }

        poll_response = requests.post(poll_url, data=poll_data, timeout=30)
        poll_result = poll_response.json()

        if not poll_result.get('ok'):
            raise HTTPException(status_code=500, detail=f"Poll creation failed: {poll_result.get('description')}")

        return {
            "success": True,
            "message": "Budget document and approval poll sent to Telegram successfully",
            "filename": filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending to Telegram: {str(e)}")