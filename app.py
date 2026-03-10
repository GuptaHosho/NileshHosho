from fastapi import FastAPI
from pydantic import BaseModel
import base64

from parser import normalize_transactions
from reconciliation_engine import reconcile

app = FastAPI()


class ReconcileRequest(BaseModel):
    bank_file: str
    ledger_file: str


@app.get("/")
def home():
    return {"message": "Reconciliation API running"}


@app.post("/reconcile")
async def run_reconciliation(data: ReconcileRequest):

    # Decode base64 files coming from Power Automate
    bank_contents = base64.b64decode(data.bank_file)
    ledger_contents = base64.b64decode(data.ledger_file)

    # Normalize transactions
    bank_transactions = normalize_transactions(bank_contents, "bank_file.csv")
    ledger_transactions = normalize_transactions(ledger_contents, "ledger_file.csv")

    # Run reconciliation
    results = reconcile(bank_transactions, ledger_transactions)

    return results
