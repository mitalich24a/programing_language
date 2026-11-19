
from langchain_core.tools import tool


# Simulated banking data
ACCOUNTS = {
    "ACC101": {
        "balance": 50000,
        "currency": "INR"
    }
}

TRANSACTIONS = {
    "ACC101": [
        {
            "transaction_id": "TXN101",
            "amount": 5000,
            "type": "DEBIT"
        },
        {
            "transaction_id": "TXN102",
            "amount": 10000,
            "type": "CREDIT"
        }
    ]
}


@tool
def get_balance(account_id: str) -> dict:
    """Retrieve the balance of an account."""

    if account_id not in ACCOUNTS:
        raise ValueError("Account not found")

    return ACCOUNTS[account_id]


@tool
def get_transactions(account_id: str) -> list:
    """Retrieve recent transactions for an account."""

    if account_id not in TRANSACTIONS:
        raise ValueError("Account not found")

    return TRANSACTIONS[account_id]
