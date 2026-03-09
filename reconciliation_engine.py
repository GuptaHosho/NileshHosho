from datetime import datetime
from itertools import combinations


def normalize_text(value):
    if not value:
        return ""
    return str(value).lower().replace("-", "").replace(" ", "").strip()


def date_difference(d1, d2):
    try:
        d1 = datetime.fromisoformat(d1.split()[0])
        d2 = datetime.fromisoformat(d2.split()[0])
        return abs((d1 - d2).days)
    except:
        return 999


def calculate_score(bank, ledger):

    score = 0

    if normalize_text(bank["reference"]) == normalize_text(ledger["reference"]):
        score += 50

    diff = date_difference(bank["date"], ledger["date"])

    if diff <= 1:
        score += 20
    elif diff <= 3:
        score += 10

    if normalize_text(bank["description"]) == normalize_text(ledger["description"]):
        score += 20

    return score

def filter_candidates(bank_txn, ledger_transactions):

    candidates = []

    for l in ledger_transactions:

        if l.get("matched"):
            continue

        # amount must not exceed bank amount
        if l["amount"] > bank_txn["amount"]:
            continue

        # date tolerance
        if date_difference(bank_txn["date"], l["date"]) > 5:
            continue

        candidates.append(l)

    return candidates


# ---------- 1 → 1 ----------

def rule_one_to_one(bank_transactions, ledger_transactions, matches):

    for b in bank_transactions:

        if b.get("matched"):
            continue

        candidates = []

        for l in ledger_transactions:

            if l.get("matched"):
                continue

            if b["amount"] == l["amount"]:
                candidates.append(l)

        if not candidates:
            continue

        best = None
        best_score = -1

        for c in candidates:
            score = calculate_score(b, c)

            if score > best_score:
                best_score = score
                best = c

        if best:

            matches.append({
                "type": "1-1",
                "score": best_score,
                "bank_transaction": b,
                "ledger_transaction": best
            })

            b["matched"] = True
            best["matched"] = True


# ---------- 1 → n ----------

def rule_one_to_many(bank_transactions, ledger_transactions, matches):


    for b in bank_transactions:

        if b.get("matched"):
            continue

        ledger_pool = filter_candidates(b, ledger_transactions)    

        for r in range(2, 5):

            for combo in combinations(ledger_pool, r):

                total = sum(l["amount"] for l in combo)

                if total == b["amount"]:

                    matches.append({
                        "type": "1-n",
                        "bank_transaction": b,
                        "ledger_transactions": list(combo)
                    })

                    b["matched"] = True

                    for c in combo:
                        c["matched"] = True

                    break

            if b.get("matched"):
                break


# ---------- n → 1 ----------

def rule_many_to_one(bank_transactions, ledger_transactions, matches):

    for l in ledger_transactions:

        if l.get("matched"):
            continue

        bank_pool = [
            b for b in bank_transactions
            if not b.get("matched") and b["amount"] <= l["amount"]
        ]

        for r in range(2, 5):

            for combo in combinations(bank_pool, r):

                total = sum(b["amount"] for b in combo)

                if total == l["amount"]:

                    matches.append({
                        "type": "n-1",
                        "bank_transactions": list(combo),
                        "ledger_transaction": l
                    })

                    l["matched"] = True

                    for b in combo:
                        b["matched"] = True

                    break

            if l.get("matched"):
                break


# ---------- n → n ----------

def rule_many_to_many(bank_transactions, ledger_transactions, matches):

    bank_pool = [b for b in bank_transactions if not b.get("matched")]
    ledger_pool = [l for l in ledger_transactions if not l.get("matched")]

    for br in range(2, 5):

        for bank_combo in combinations(bank_pool, br):

            bank_total = sum(b["amount"] for b in bank_combo)

            for lr in range(2, 5):

                for ledger_combo in combinations(ledger_pool, lr):

                    ledger_total = sum(l["amount"] for l in ledger_combo)

                    if bank_total == ledger_total:

                        matches.append({
                            "type": "n-n",
                            "bank_transactions": list(bank_combo),
                            "ledger_transactions": list(ledger_combo)
                        })

                        # LOCK transactions
                        for b in bank_combo:
                            b["matched"] = True

                        for l in ledger_combo:
                            l["matched"] = True

                        # STOP search after match
                        return


# ---------- MAIN ENGINE ----------

def reconcile(bank_transactions, ledger_transactions):

    matches = []

    rule_one_to_one(bank_transactions, ledger_transactions, matches)
    rule_one_to_many(bank_transactions, ledger_transactions, matches)
    rule_many_to_one(bank_transactions, ledger_transactions, matches)
    rule_many_to_many(bank_transactions, ledger_transactions, matches)

    unmatched_bank = [b for b in bank_transactions if not b.get("matched")]
    unmatched_ledger = [l for l in ledger_transactions if not l.get("matched")]

    return {
        "matches": matches,
        "unmatched_bank": unmatched_bank,
        "unmatched_ledger": unmatched_ledger
    }