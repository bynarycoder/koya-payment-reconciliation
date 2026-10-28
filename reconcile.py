#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Only the latest attempt for each transaction counts.
Run:  python3 reconcile.py
"""

import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

latest_attempts = {}

with open("payments.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            # Ignore malformed JSON lines.
            continue

        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        if txn_id is None or not str(txn_id).strip():
            # Ignore events without a transaction ID.
            continue

        try:
            timestamp = datetime.fromisoformat(
                str(event["ts"]).replace("Z", "+00:00")
            )
        except (KeyError, TypeError, ValueError):
            continue

        previous = latest_attempts.get(str(txn_id))
        # When timestamps tie, the later line in the file wins.
        if previous is None or timestamp >= previous[0]:
            latest_attempts[str(txn_id)] = (timestamp, event)

total = Decimal("0")
count = 0

for _, event in latest_attempts.values():
    if event.get("status") == "success":
        try:
            # Some amounts are strings formatted with thousands separators.
            amount = Decimal(str(event["amount"]).replace(",", ""))
        except (KeyError, TypeError, ValueError):
            continue
        total += amount
        count += 1

with open("expected.txt", "r", encoding="utf-8") as f:
    expected = int(f.read().strip())

if count != expected:
    print(
        f"Check failed: counted {count} successful payments, "
        f"expected {expected}."
    )
    print("Something in the data isn't being handled the way the README describes.")
else:
    rounded_total = total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{rounded_total:.0f}")
