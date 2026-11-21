"""The tasks a card waits for: its dispatch option --waits-for, kept in the card's options."""


def waited(card_or_row) -> list:
    text = ((card_or_row or {}).get("options") or {}).get("waits_for") or ""
    return [t for t in text.split(",") if t and t != "yes"]
