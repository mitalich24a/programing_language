
from fastmcp import FastMCP


mcp = FastMCP("Banking Customer Services")


@mcp.tool
def get_branch_information(branch_code: str) -> dict:
    """Retrieve information about a bank branch."""

    branches = {
        "BLR001": {
            "city": "Bangalore",
            "opening_time": "09:30 AM",
            "closing_time": "04:00 PM"
        }
    }

    if branch_code not in branches:
        raise ValueError("Branch not found")

    return branches[branch_code]


@mcp.tool
def get_exchange_rate(
    source_currency: str,
    target_currency: str
) -> dict:
    """Retrieve a simulated currency exchange rate."""

    rates = {
        ("USD", "INR"): 88.0,
        ("EUR", "INR"): 102.0
    }

    key = (source_currency, target_currency)

    if key not in rates:
        raise ValueError("Exchange rate unavailable")

    return {
        "source": source_currency,
        "target": target_currency,
        "rate": rates[key],
        "simulated": True
    }


if __name__ == "__main__":
    mcp.run()
