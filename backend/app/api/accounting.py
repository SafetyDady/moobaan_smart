"""
API endpoints for accounting system.

Provides REST endpoints for:
- Invoice management
- Payment processing
- Credit note issuance
- Balance calculation
- Financial reporting

Access control:
- Residents: View own house data (ACTIVE status only)
- Accounting: Full access to all houses
- Super Admin: Full access + payment acceptance
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.timezone import utc_now
import io
import json

from app.core.deps import get_db, get_current_user
from app.core.auth import require_role, require_house_access
from app.core.config import Settings
from app.db.models import User, House, Invoice, PayinReport, IncomeTransaction, CreditNote
from app.services.accounting import AccountingService
from app.services.statement_generator import StatementPDFGenerator, StatementExcelGenerator


router = APIRouter(prefix="/accounting", tags=["accounting"])


# Pydantic models for request/response
class InvoiceCreate(BaseModel):
    house_id: int
    cycle_year: int = Field(..., ge=2000, le=3000)
    cycle_month: int = Field(..., ge=1, le=12)
    total_amount: Decimal = Field(..., gt=0)
    issue_date: date
    due_date: date
    notes: Optional[str] = None


class BulkInvoiceGenerate(BaseModel):
    year: int = Field(..., ge=2000, le=3000)
    month: int = Field(..., ge=1, le=12)
    base_amount: Decimal = Field(default=Decimal("600.00"), gt=0)


class PaymentApplication(BaseModel):
    income_transaction_id: int
    invoice_id: int
    amount: Decimal = Field(..., gt=0)


class CreditNoteCreate(BaseModel):
    house_id: int
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=1)
    reference: Optional[str] = None


class PayinAccept(BaseModel):
    payin_id: int


class AutoApplyPayment(BaseModel):
    income_transaction_id: int


# Invoice endpoints
@router.post("/invoices", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a manual invoice (accounting/admin only)."""
    try:
        # Check if invoice already exists
        existing = db.query(Invoice).filter(
            Invoice.house_id == invoice_data.house_id,
            Invoice.cycle_year == invoice_data.cycle_year,
            Invoice.cycle_month == invoice_data.cycle_month
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invoice already exists for house {invoice_data.house_id}, "
                       f"cycle {invoice_data.cycle_year}-{invoice_data.cycle_month}"
            )
        
        # Verify house exists
        house = db.query(House).filter(House.id == invoice_data.house_id).first()
        if not house:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"House {invoice_data.house_id} not found"
            )
        
        invoice = Invoice(
            house_id=invoice_data.house_id,
            cycle_year=invoice_data.cycle_year,
            cycle_month=invoice_data.cycle_month,
            issue_date=invoice_data.issue_date,
            due_date=invoice_data.due_date,
            total_amount=invoice_data.total_amount,
            notes=invoice_data.notes,
            created_by=current_user.id
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        return {
            "success": True,
            "message": "Invoice created successfully",
            "invoice": invoice.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.post("/invoices/bulk-generate", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def bulk_generate_invoices(
    generate_data: BulkInvoiceGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auto-generate monthly invoices for all houses."""
    try:
        created_invoices = AccountingService.auto_generate_invoices(
            db=db,
            year=generate_data.year,
            month=generate_data.month,
            base_amount=generate_data.base_amount,
            created_by_id=current_user.id
        )
        
        return {
            "success": True,
            "message": f"Generated {len(created_invoices)} invoices for {generate_data.year}-{generate_data.month:02d}",
            "invoices_created": len(created_invoices),
            "invoices": [invoice.to_dict() for invoice in created_invoices]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invoices: {str(e)}"
        )


@router.get("/invoices/house/{house_id}")
async def get_house_invoices(
    house_id: int,
    limit: Optional[int] = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get invoices for a specific house."""
    # Check access permissions
    await require_house_access(house_id, current_user, db)
    
    invoices = db.query(Invoice).filter(
        Invoice.house_id == house_id
    ).order_by(
        Invoice.cycle_year.desc(),
        Invoice.cycle_month.desc()
    ).limit(limit).all()
    
    return {
        "success": True,
        "invoices": [invoice.to_dict() for invoice in invoices],
        "total_count": len(invoices)
    }


# Payment endpoints
@router.post("/payins/accept", dependencies=[Depends(require_role(["super_admin"]))])
async def accept_payin(
    accept_data: PayinAccept,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a PayIn and create IncomeTransaction (SUPER_ADMIN only)."""
    try:
        income_transaction = AccountingService.accept_payin(
            db=db,
            payin_id=accept_data.payin_id,
            accepted_by_user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Payment accepted successfully",
            "income_transaction": income_transaction.to_dict()
        }
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept payment: {str(e)}"
        )


@router.post("/payments/apply", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def apply_payment_to_invoice(
    payment_data: PaymentApplication,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply payment from IncomeTransaction to specific Invoice."""
    try:
        payment = AccountingService.apply_payment_to_invoice(
            db=db,
            income_transaction_id=payment_data.income_transaction_id,
            invoice_id=payment_data.invoice_id,
            amount=payment_data.amount
        )
        
        return {
            "success": True,
            "message": "Payment applied successfully",
            "payment": payment.to_dict()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply payment: {str(e)}"
        )


@router.post("/payments/auto-apply", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def auto_apply_payment_fifo(
    apply_data: AutoApplyPayment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auto-apply payment to oldest unpaid invoices using FIFO method."""
    try:
        payments = AccountingService.auto_apply_payments_fifo(
            db=db,
            income_transaction_id=apply_data.income_transaction_id
        )
        
        return {
            "success": True,
            "message": f"Applied payment to {len(payments)} invoices",
            "payments": [payment.to_dict() for payment in payments],
            "payments_created": len(payments)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-apply payment: {str(e)}"
        )


# Credit Note endpoints
@router.post("/credit-notes", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def create_credit_note(
    credit_data: CreditNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue a credit note for debt reduction."""
    try:
        credit_note = AccountingService.issue_credit_note(
            db=db,
            house_id=credit_data.house_id,
            amount=credit_data.amount,
            reason=credit_data.reason,
            created_by_id=current_user.id,
            reference=credit_data.reference
        )
        
        return {
            "success": True,
            "message": "Credit note issued successfully",
            "credit_note": credit_note.to_dict()
        }
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to issue credit note: {str(e)}"
        )


@router.get("/credit-notes/house/{house_id}", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def get_house_credit_notes(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get credit notes for a specific house (accounting/admin only)."""
    credit_notes = db.query(CreditNote).filter(
        CreditNote.house_id == house_id
    ).order_by(
        CreditNote.created_at.desc()
    ).all()
    
    return {
        "success": True,
        "credit_notes": [note.to_dict() for note in credit_notes],
        "total_count": len(credit_notes)
    }


# Balance and reporting endpoints
@router.get("/balance/house/{house_id}")
async def get_house_balance(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get balance breakdown for a specific house."""
    # Check access permissions
    await require_house_access(house_id, current_user, db)
    
    try:
        balance = AccountingService.calculate_house_balance(db, house_id)
        return {
            "success": True,
            "balance": balance
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/financial-summary/house/{house_id}")
async def get_house_financial_summary(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive financial summary for a house."""
    # Check access permissions
    await require_house_access(house_id, current_user, db)
    
    try:
        summary = AccountingService.get_house_financial_summary(db, house_id)
        
        # Filter credit notes for residents
        if current_user.role == "resident":
            # Remove detailed credit notes for residents, show only summary
            credit_note_total = sum(
                note["amount"] for note in summary["credit_notes"]
            ) if summary["credit_notes"] else 0
            summary["credit_notes"] = {
                "total_amount": credit_note_total,
                "count": len(summary["credit_notes"]),
                "note": "Contact management for credit note details"
            }
        
        return {
            "success": True,
            "financial_summary": summary
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/income-transactions/house/{house_id}", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def get_house_income_transactions(
    house_id: int,
    limit: Optional[int] = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get income transactions for a house (accounting/admin only)."""
    transactions = db.query(IncomeTransaction).filter(
        IncomeTransaction.house_id == house_id
    ).order_by(
        IncomeTransaction.received_at.desc()
    ).limit(limit).all()
    
    return {
        "success": True,
        "income_transactions": [tx.to_dict() for tx in transactions],
        "total_count": len(transactions)
    }


@router.get("/reports/balance-summary", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def get_balance_summary_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get balance summary for all houses (accounting/admin only)."""
    houses = db.query(House).all()
    balances = []
    
    for house in houses:
        balance = AccountingService.calculate_house_balance(db, house.id)
        balances.append(balance)
    
    # Calculate totals
    total_invoiced = sum(b["total_invoiced"] for b in balances)
    total_credited = sum(b["total_credited"] for b in balances)
    total_paid = sum(b["total_paid"] for b in balances)
    total_outstanding = sum(b["outstanding_balance"] for b in balances)
    
    return {
        "success": True,
        "summary": {
            "total_invoiced": total_invoiced,
            "total_credited": total_credited,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "houses_count": len(houses)
        },
        "house_balances": balances
    }


# Month-end snapshot endpoints
@router.get("/snapshot/house/{house_id}")
async def get_month_end_snapshot(
    house_id: int,
    year: int = Query(..., description="Year (e.g., 2024)"),
    month: int = Query(..., description="Month (1-12)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get month-end financial snapshot for a house."""
    # Check access permissions
    await require_house_access(house_id, current_user, db)
    
    try:
        snapshot = AccountingService.calculate_month_end_snapshot(
            db=db, 
            house_id=house_id, 
            year=year, 
            month=month
        )
        return {
            "success": True,
            "snapshot": snapshot
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# House financial statement endpoints
@router.get("/statement/house/{house_id}")
async def get_house_statement(
    house_id: int,
    year: int = Query(..., description="Year (e.g., 2024)", ge=2000, le=3000),
    month: int = Query(..., description="Month (1-12)", ge=1, le=12),
    format: str = Query("json", description="Format: json, pdf, xlsx"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(lambda: Settings())
):
    """Generate house financial statement for specified month.
    
    Access Control:
    - Residents: Own house only (ACTIVE status required)
    - Accounting/Admin: Any house
    """
    # Validate format parameter
    if format not in ["json", "pdf", "xlsx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid format",
                "error_th": "รูปแบบไม่ถูกต้อง",
                "error_en": "Invalid format. Supported formats: json, pdf, xlsx",
                "supported_formats": ["json", "pdf", "xlsx"]
            }
        )
    
    # Enhanced access control with bilingual messages
    try:
        # Check if user has access to this house
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "House not found",
                    "error_th": "ไม่พบข้อมูลบ้านเลขที่นี้",
                    "error_en": "House not found"
                }
            )
        
        # Role-based access control
        if current_user.role == "resident":
            # Residents can only access their own house
            if house.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Access denied",
                        "error_th": "ไม่สามารถเข้าถึงข้อมูลบ้านเลขที่นี้ได้",
                        "error_en": "You can only access your own house statement"
                    }
                )
            
            # House must be ACTIVE for residents
            if house.status != "ACTIVE":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "House not active",
                        "error_th": "บ้านเลขที่นี้ไม่ได้อยู่ในสถานะ ACTIVE",
                        "error_en": "Statement only available for active houses"
                    }
                )
        elif current_user.role not in ["accounting", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Insufficient permissions",
                    "error_th": "สิทธิ์ไม่เพียงพอ",
                    "error_en": "Insufficient permissions to access house statements"
                }
            )
        
        # Generate statement
        statement = AccountingService.generate_house_statement(
            db=db,
            house_id=house_id,
            year=year,
            month=month
        )
        
        # Return based on format
        if format == "json":
            return {
                "success": True,
                "statement": statement,
                "meta": {
                    "generated_at": utc_now().isoformat(),
                    "requested_by": current_user.username,
                    "format": "json"
                }
            }
        elif format == "xlsx":
            # Generate Excel file
            excel_generator = StatementExcelGenerator(settings)
            excel_data = excel_generator.generate_statement_excel(statement)
            
            filename = f"statement_{statement['header']['house_code']}_{year:04d}_{month:02d}.xlsx"
            return Response(
                content=excel_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif format == "pdf":
            # Generate PDF file
            pdf_generator = StatementPDFGenerator(settings)
            pdf_data = pdf_generator.generate_statement_pdf(statement)
            
            filename = f"statement_{statement['header']['house_code']}_{year:04d}_{month:02d}.pdf"
            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid request",
                "error_th": "ข้อมูลที่ส่งมาไม่ถูกต้อง",
                "error_en": str(e)
            }
        )
    except Exception as e:
        # Log the error but don't expose sensitive details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Statement generation failed",
                "error_th": "ไม่สามารถสร้างใบแจ้งยอดได้",
                "error_en": "Unable to generate statement. Please try again or contact support."
            }
        )


# Aging report endpoints
@router.get("/aging", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def get_aging_report(
    year: int = Query(..., description="Year (e.g., 2024)"),
    month: int = Query(..., description="Month (1-12)"),
    house_status: Optional[List[str]] = Query(None, description="Filter by house status"),
    min_outstanding: Optional[float] = Query(None, description="Minimum outstanding amount"),
    export: Optional[str] = Query(None, description="Export format: xlsx"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate aging report for all houses as of month-end (accounting/admin only)."""
    try:
        min_outstanding_decimal = Decimal(str(min_outstanding)) if min_outstanding else None
        
        aging_data = AccountingService.generate_aging_report(
            db=db,
            year=year,
            month=month,
            house_status_filter=house_status,
            min_outstanding=min_outstanding_decimal
        )
        
        if export == "xlsx":
            # Generate Excel file
            excel_data = _generate_aging_excel(aging_data, year, month)
            filename = f"aging_report_{year:04d}_{month:02d}.xlsx"
            return Response(
                content=excel_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            return {
                "success": True,
                "aging_report": aging_data,
                "summary": {
                    "total_houses": len(aging_data),
                    "total_outstanding": sum(house["total_outstanding"] for house in aging_data),
                    "bucket_0_30_total": sum(house["bucket_0_30"] for house in aging_data),
                    "bucket_31_90_total": sum(house["bucket_31_90"] for house in aging_data),
                    "bucket_90_plus_total": sum(house["bucket_90_plus"] for house in aging_data)
                }
            }
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Month-End Snapshot endpoints
@router.get("/snapshot/{house_id}")
async def get_house_snapshot(
    house_id: int,
    year: int = Query(..., ge=2000, le=3000),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get month-end financial snapshot for a specific house.
    
    Access Control:
    - Residents: Can view own house only (if ACTIVE status)
    - Accounting/Admin: Can view any house
    
    Returns:
    - opening_balance: Balance at start of month
    - invoice_total: Invoices issued in month
    - payment_total: Payments received in month
    - credit_total: Credit notes issued in month
    - closing_balance: Final balance at month end
    
    Note: All values are computed on-demand (not stored in DB).
    Negative closing_balance indicates prepayment/overpayment.
    """
    # Access control check
    require_house_access(current_user, house_id, db)
    
    try:
        from app.models import MonthEndSnapshot
        
        snapshot_data = AccountingService.calculate_month_end_snapshot(
            db=db,
            house_id=house_id,
            year=year,
            month=month
        )
        
        return MonthEndSnapshot(**snapshot_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/snapshot", dependencies=[Depends(require_role(["accounting", "super_admin"]))])
async def get_aggregated_snapshot(
    year: int = Query(..., ge=2000, le=3000),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get aggregated month-end snapshot for ALL houses.
    
    Admin/Accounting only.
    
    Returns aggregated totals plus per-house breakdown:
    - total_houses: Number of houses
    - opening_balance: Total opening balance
    - invoice_total: Total invoices issued
    - payment_total: Total payments received
    - credit_total: Total credit notes
    - closing_balance: Total closing balance
    - houses: Array of per-house snapshots
    
    Note: Reuses per-house calculation logic to ensure consistency.
    No double counting - each transaction counted exactly once.
    """
    try:
        from app.models import AggregatedSnapshot
        
        aggregated_data = AccountingService.calculate_aggregated_snapshot(
            db=db,
            year=year,
            month=month
        )
        
        return AggregatedSnapshot(**aggregated_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Financial Statement endpoint (Phase 2.4 - Read-Only)
@router.get("/statement/{house_id}")
async def get_financial_statement(
    house_id: int,
    start_date: date = Query(..., description="Statement start date"),
    end_date: date = Query(..., description="Statement end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get financial statement for a house over a date range.
    
    PHASE 2.4 - READ-ONLY PRESENTATION
    
    This endpoint combines:
    - Opening balance from Phase 2.3 snapshot
    - Ledger transactions in period (invoices, payments, credit notes)
    - Running balance (display-only, not stored)
    - Closing balance from Phase 2.3 snapshot
    
    Access Control:
    - Residents: Can view own house only (if ACTIVE status)
    - Accounting/Admin: Can view any house
    
    Statement Structure:
    - Opening Balance row
    - Transaction rows (sorted by date ASC)
      * Invoices → Debit column
      * Payments → Credit column
      * Credit Notes → Credit column
    - Running balance (calculated for display)
    - Footer summary with totals
    
    Returns:
    - Complete financial statement ready for HTML/JSON rendering
    
    Note: All balances are derived on-demand (nothing persisted).
    """
    # Access control check
    require_house_access(current_user, house_id, db)
    
    try:
        from app.models import FinancialStatement
        
        statement_data = AccountingService.generate_statement(
            db=db,
            house_id=house_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return FinancialStatement(**statement_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )