import pandas as pd
import io
import re


def find_column(columns, keywords):
    for col in columns:
        col_lower = col.lower()
        for keyword in keywords:
            if keyword in col_lower:
                return col
    return None


def normalize_transactions(file_content, filename):

    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_content), sep=None, engine="python")

    elif filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(file_content))

    else:
        return {"error": "Unsupported file type"}

    columns = list(df.columns)

    date_col = find_column(columns, ["transaction date", "value date", "date"])
    desc_col = find_column(columns, ["description", "narration", "remarks"])
    amount_col = find_column(columns, ["amount"])
    credit_col = find_column(columns, ["credit", "deposit"])
    debit_col = find_column(columns, ["debit", "withdrawal"])
    type_col = find_column(columns, ["type", "transaction type", "drcr", "crdr"])
    reference_col = find_column(columns, ["reference", "external document", "document no", "document number"])

    transactions = []

    for i, row in df.iterrows():

        date = row.get(date_col) if date_col else None
        desc = row.get(desc_col) if desc_col else ""
        desc = str(desc)

        reference = row.get(reference_col) if reference_col else ""

        if pd.isna(reference):
            reference = ""

        if not reference:
            ref_match = re.search(r'(INV[-]?\d+)', desc, re.IGNORECASE)
            reference = ref_match.group(0) if ref_match else ""

        credit = row.get(credit_col) if credit_col else None
        debit = row.get(debit_col) if debit_col else None
        amount = row.get(amount_col) if amount_col else None

        # ---------- Debit / Credit Columns ----------
        if pd.notna(credit):
            amount = float(credit)
            ttype = "credit"

        elif pd.notna(debit):
            amount = float(debit)
            ttype = "debit"

        # ---------- Single Amount Column ----------
        elif pd.notna(amount):

            amount = float(amount)

            if type_col:
                t = str(row.get(type_col)).lower()

                if "credit" in t or "cr" in t:
                    ttype = "credit"

                elif "debit" in t or "dr" in t:
                    ttype = "debit"

                else:
                    ttype = "unknown"

            else:
                # Detect type using positive / negative amount
                if amount > 0:
                    ttype = "credit"
                elif amount < 0:
                    ttype = "debit"
                else:
                    ttype = "unknown"

            amount = abs(amount)

        else:
            continue

        if pd.isna(date):
            date = ""

        transactions.append({
            "id": f"TXN-{i}",
            "date": str(date),
            "amount": float(amount),
            "type": ttype,
            "description": desc,
            "reference": str(reference),
            "source": "bank",
            "matched": False
        })

    return transactions