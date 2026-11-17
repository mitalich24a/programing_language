
from fastmcp import FastMCP

mcp = FastMCP("Banking MCP Server")


# Simulated banking data
ACCOUNTS = {
    "ACC101": {
        "balance": 50000,
        "currency": "INR"
    },
    "ACC102": {
        "balance": 25000,
        "currency": "INR"
    }
}

TRANSACTIONS = {
    "ACC101": [
        {"type": "CREDIT", "amount": 10000},
        {"type": "DEBIT", "amount": 2000}
    ]
}


@mcp.tool()
def get_balance(account_id: str) -> dict:
    """Get the balance of a bank account."""

    account = ACCOUNTS.get(account_id)

    if not account:
        raise ValueError("Account not found")

    return {
        "account_id": account_id,
        "balance": account["balance"],
        "currency": account["currency"]
    }


@mcp.tool()
def get_transactions(account_id: str) -> list:
    """Get recent transactions for a bank account."""

    if account_id not in ACCOUNTS:
        raise ValueError("Account not found")

    return TRANSACTIONS.get(account_id, [])


if __name__ == "__main__":
    mcp.run()
