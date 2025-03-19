import secrets

def generate_unique_nickname():
    """
    Generates a unique nickname.
    You could add extra logic to ensure uniqueness against the Card model,
    but for now it just returns a random hexadecimal string.
    """
    return secrets.token_hex(8)
