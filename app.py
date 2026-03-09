from fastapi import FastAPI, UploadFile, File
from parser import normalize_transactions
from reconciliation_engine import reconcile

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Reconciliation API running"}


@app.post("/parse")
async def parse_file(file: UploadFile = File(...)):

    contents = await file.read()

    transactions = normalize_transactions(contents, file.filename)

    return {"transactions": transactions}


@app.post("/reconcile")
async def run_reconciliation(
    bank_file: UploadFile = File(...),
    ledger_file: UploadFile = File(...)
):

    bank_contents = await bank_file.read()
    ledger_contents = await ledger_file.read()

    bank_transactions = normalize_transactions(bank_contents, bank_file.filename)
    ledger_transactions = normalize_transactions(ledger_contents, ledger_file.filename)

    results = reconcile(bank_transactions, ledger_transactions)

    return results