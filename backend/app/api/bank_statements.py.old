from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from datetime import datetime, date
from app.models import (
    BankStatement, BankStatementRow,
    BankStatementUploadResponse
)
from app.mock_data import MOCK_BANK_STATEMENTS, MOCK_BANK_STATEMENT_ROWS

router = APIRouter(prefix="/api/bank-statements", tags=["bank-statements"])

# In-memory storage
statements_db = list(MOCK_BANK_STATEMENTS)
statement_rows_db = list(MOCK_BANK_STATEMENT_ROWS)
next_statement_id = max([s.id for s in statements_db]) + 1
next_row_id = max([r.id for r in statement_rows_db]) + 1


@router.get("", response_model=List[BankStatement])
async def list_bank_statements():
    """List all bank statements"""
    return sorted(statements_db, key=lambda x: x.upload_date, reverse=True)


@router.get("/{statement_id}", response_model=BankStatement)
async def get_bank_statement(statement_id: int):
    """Get a specific bank statement by ID"""
    statement = next((s for s in statements_db if s.id == statement_id), None)
    if not statement:
        raise HTTPException(status_code=404, detail="Bank statement not found")
    return statement


@router.get("/{statement_id}/rows", response_model=List[BankStatementRow])
async def get_bank_statement_rows(statement_id: int):
    """Get all rows for a specific bank statement"""
    statement = next((s for s in statements_db if s.id == statement_id), None)
    if not statement:
        raise HTTPException(status_code=404, detail="Bank statement not found")
    
    rows = [r for r in statement_rows_db if r.statement_id == statement_id]
    return sorted(rows, key=lambda x: (x.date, x.time), reverse=True)


@router.post("/upload", response_model=BankStatementUploadResponse)
async def upload_bank_statement(file: UploadFile = File(...)):
    """
    Upload a bank statement file (Excel)
    
    NOTE: This is a MOCK implementation for Phase 1.
    It generates fake rows instead of actually parsing the Excel file.
    """
    global next_statement_id, next_row_id
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload Excel (.xlsx, .xls) or CSV file"
        )
    
    # Create new statement record
    new_statement = BankStatement(
        id=next_statement_id,
        filename=file.filename,
        upload_date=datetime.now(),
        total_rows=0,
        matched_rows=0
    )
    statements_db.append(new_statement)
    
    # Generate mock rows (in real implementation, parse the Excel file here)
    mock_rows = [
        BankStatementRow(
            id=next_row_id,
            statement_id=next_statement_id,
            date=date.today(),
            time="10:30",
            amount=3000.0,
            reference="TRF-NEW001",
            matched=False,
            matched_payin_id=None
        ),
        BankStatementRow(
            id=next_row_id + 1,
            statement_id=next_statement_id,
            date=date.today(),
            time="14:15",
            amount=2500.0,
            reference="TRF-NEW002",
            matched=False,
            matched_payin_id=None
        ),
        BankStatementRow(
            id=next_row_id + 2,
            statement_id=next_statement_id,
            date=date.today(),
            time="16:45",
            amount=3000.0,
            reference="TRF-NEW003",
            matched=False,
            matched_payin_id=None
        ),
    ]
    
    statement_rows_db.extend(mock_rows)
    new_statement.total_rows = len(mock_rows)
    
    next_statement_id += 1
    next_row_id += len(mock_rows)
    
    return BankStatementUploadResponse(
        statement_id=new_statement.id,
        filename=file.filename,
        total_rows=new_statement.total_rows,
        message=f"Successfully uploaded and parsed {new_statement.total_rows} rows (MOCK)"
    )


@router.post("/{statement_id}/rows/{row_id}/match")
async def match_statement_row(statement_id: int, row_id: int, payin_id: int):
    """Match a statement row with a pay-in report"""
    # Find statement row
    row = next((r for r in statement_rows_db 
                if r.statement_id == statement_id and r.id == row_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Statement row not found")
    
    # Update row
    row.matched = True
    row.matched_payin_id = payin_id
    
    # Update statement matched count
    statement = next((s for s in statements_db if s.id == statement_id), None)
    if statement:
        statement.matched_rows = len([r for r in statement_rows_db 
                                     if r.statement_id == statement_id and r.matched])
    
    return {
        "message": "Statement row matched with pay-in report",
        "row_id": row_id,
        "payin_id": payin_id
    }


@router.delete("/{statement_id}")
async def delete_bank_statement(statement_id: int):
    """Delete a bank statement and all its rows"""
    global statements_db, statement_rows_db
    
    statement = next((s for s in statements_db if s.id == statement_id), None)
    if not statement:
        raise HTTPException(status_code=404, detail="Bank statement not found")
    
    # Delete statement and its rows
    statements_db = [s for s in statements_db if s.id != statement_id]
    statement_rows_db = [r for r in statement_rows_db if r.statement_id != statement_id]
    
    return {"message": "Bank statement deleted successfully"}
