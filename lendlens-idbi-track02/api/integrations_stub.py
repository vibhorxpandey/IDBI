"""
MOCK integration stubs — Account Aggregator (AA), ULI, OCEN  (Part 7).

╔════════════════════════════════════════════════════════════════════════╗
║  EVERYTHING IN THIS FILE IS A SIMULATION.                               ║
║  No real Account Aggregator, bank, ULI, OCEN or credit-bureau call is   ║
║  made. No real consent is captured. These typed request/response shapes ║
║  mirror what the production rails WOULD exchange, so (a) the dashboard's ║
║  consent flow has realistic payloads to render, and (b) a reviewer can  ║
║  see precisely where the real integrations slot in for Round-2.         ║
╚════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

MOCK_DISCLAIMER = ("SIMULATED — Round-1 prototype. No real Account Aggregator / "
                   "bank / bureau call is made.")

router = APIRouter(tags=["integrations (MOCK)"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ===========================================================================
# Account Aggregator (AA)  — RBI AA / Sahamati-style consent + FI data fetch
# ===========================================================================
class AAConsentRequest(BaseModel):
    customer_id: str = "CUST_PRIYA"
    purpose: str = "Loan eligibility assessment"
    fi_types: list[str] = Field(default_factory=lambda: ["DEPOSIT", "RECURRING_DEPOSIT"])
    account_refs: list[str] = Field(default_factory=lambda: ["HDFC****1234"])
    duration_months: int = 6


class AAConsentArtefact(BaseModel):
    mock: bool = True
    disclaimer: str = MOCK_DISCLAIMER
    consent_id: str
    consent_handle: str
    status: str = "ACTIVE"
    customer_id: str
    purpose: str
    fi_types: list[str]
    accounts_linked: list[str]
    data_range_from: str
    data_range_to: str
    created_at: str
    expires_at: str
    aa_provider: str = "MockAA (Sahamati-style)"


class AAFetchRequest(BaseModel):
    consent_id: str = "CONSENT-MOCK"
    customer_id: str = "CUST_PRIYA"


class AAFIData(BaseModel):
    mock: bool = True
    disclaimer: str = MOCK_DISCLAIMER
    consent_id: str
    customer_id: str
    account: dict
    summary: dict
    sample_transactions: list[dict]


@router.post("/aa/consent", response_model=AAConsentArtefact,
             summary="MOCK — create an AA consent artefact")
def aa_consent(req: AAConsentRequest) -> AAConsentArtefact:
    """Simulate an Account Aggregator consent grant. In production this is a
    signed consent artefact returned by the AA after the customer approves in
    their AA app. Here it is fabricated locally — no real consent is captured."""
    now = _now()
    start = now - timedelta(days=30 * req.duration_months)
    return AAConsentArtefact(
        consent_id=f"CONSENT-{uuid.uuid4().hex[:12].upper()}",
        consent_handle=f"HANDLE-{uuid.uuid4().hex[:16]}",
        customer_id=req.customer_id,
        purpose=req.purpose,
        fi_types=req.fi_types,
        accounts_linked=req.account_refs,
        data_range_from=start.date().isoformat(),
        data_range_to=now.date().isoformat(),
        created_at=now.isoformat(),
        expires_at=(now + timedelta(days=365)).isoformat(),
    )


@router.post("/aa/fetch", response_model=AAFIData,
             summary="MOCK — fetch FI data against a consent")
def aa_fetch(req: AAFetchRequest) -> AAFIData:
    """Simulate the FI-data pull an AA returns once consent is active. The sample
    below illustrates the recurring business inflows LendLens's income engine
    keys on (declared income would look far lower). Purely illustrative."""
    return AAFIData(
        consent_id=req.consent_id,
        customer_id=req.customer_id,
        account={"masked_acc_no": "HDFC****1234", "type": "SAVINGS",
                 "ifsc": "HDFC0000123", "branch": "Pune"},
        summary={"months": 6, "avg_monthly_credits": 140000,
                 "avg_monthly_debits": 41000, "recurring_inflow_detected": True,
                 "declared_income_on_file": 45000,
                 "note": "Recurring business inflows >> declared income."},
        sample_transactions=[
            {"date": "2026-06-03", "amount": 48000, "type": "CREDIT",
             "narration": "UPI/ORION DESIGNS"},
            {"date": "2026-06-05", "amount": 28000, "type": "DEBIT",
             "narration": "NEFT/RENT/HOUSING"},
            {"date": "2026-06-14", "amount": 39500, "type": "CREDIT",
             "narration": "UPI/MERIDIAN LABS"},
            {"date": "2026-06-22", "amount": 52500, "type": "CREDIT",
             "narration": "UPI/BLUEPEAK LLP"},
        ],
    )


# ===========================================================================
# ULI — Unified Lending Interface (RBI). MOCK borrower-data aggregation.
# ===========================================================================
class ULIProfile(BaseModel):
    mock: bool = True
    disclaimer: str = MOCK_DISCLAIMER
    customer_id: str
    kyc_verified: bool = True
    bureau_score: int = 785
    gst_turnover_annual: int = 1650000
    land_records_verified: bool = True
    note: str = "ULI would aggregate KYC / bureau / GST / land records via consent."


@router.get("/uli/borrower/{customer_id}", response_model=ULIProfile,
            summary="MOCK — ULI borrower data aggregation")
def uli_borrower(customer_id: str) -> ULIProfile:
    """Simulate a ULI pull that stitches together consented borrower data an
    RM would otherwise chase across silos."""
    return ULIProfile(customer_id=customer_id)


# ===========================================================================
# OCEN — Open Credit Enablement Network. MOCK loan-application handoff.
# ===========================================================================
class OCENLoanApplication(BaseModel):
    customer_id: str = "CUST_PRIYA"
    product: str = "Home"
    amount: int = 1800000
    tenor_years: int = 20


class OCENResponse(BaseModel):
    mock: bool = True
    disclaimer: str = MOCK_DISCLAIMER
    application_id: str
    status: str = "PRE_APPROVED"
    customer_id: str
    product: str
    amount: int
    tenor_years: int
    note: str = "OCEN would broadcast this to lender(s) as a structured loan request."


@router.post("/ocen/loan-application", response_model=OCENResponse,
             summary="MOCK — submit a pre-approved offer over OCEN")
def ocen_apply(app: OCENLoanApplication) -> OCENResponse:
    """Simulate handing a pre-approved offer to the OCEN rail for fulfilment."""
    return OCENResponse(
        application_id=f"OCEN-{uuid.uuid4().hex[:10].upper()}",
        customer_id=app.customer_id, product=app.product,
        amount=app.amount, tenor_years=app.tenor_years)
