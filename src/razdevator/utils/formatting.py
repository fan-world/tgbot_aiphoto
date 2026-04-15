from __future__ import annotations


def format_money(cents: int, currency: str = "USD") -> str:
    symbol = "$" if currency.upper() == "USD" else "₽"
    return f"{cents / 100:.2f}{symbol}"
