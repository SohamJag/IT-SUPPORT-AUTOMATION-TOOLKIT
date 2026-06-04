import secrets
import string

def generate_password(length=12, include_symbols=True, include_numbers=True, include_upper=True, include_lower=True):
    """Generate a cryptographically secure random password based on selections."""
    # Ensure at least one category is selected, default to lowercase
    if not (include_symbols or include_numbers or include_upper or include_lower):
        include_lower = True

    # Assemble alphabet
    chars = ""
    mandatory_chars = []
    
    if include_lower:
        chars += string.ascii_lowercase
        mandatory_chars.append(secrets.choice(string.ascii_lowercase))
    if include_upper:
        chars += string.ascii_uppercase
        mandatory_chars.append(secrets.choice(string.ascii_uppercase))
    if include_numbers:
        chars += string.digits
        mandatory_chars.append(secrets.choice(string.digits))
    if include_symbols:
        # Standard clean symbols for IT support environments (avoiding space or confusing quotes)
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        chars += symbols
        mandatory_chars.append(secrets.choice(symbols))

    # Fill up the rest of the password length
    remaining_length = max(0, length - len(mandatory_chars))
    password_chars = [secrets.choice(chars) for _ in range(remaining_length)]
    
    # Merge and shuffle to make it unpredictable
    full_password_list = mandatory_chars + password_chars
    secrets.SystemRandom().shuffle(full_password_list)
    
    return "".join(full_password_list)

def assess_strength(password):
    """Assess the strength of the generated password, returning status and structural analysis."""
    if not password:
        return "Weak", "bg-danger", 0
        
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)
    
    # Calculate score
    score = 0
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if has_upper and has_lower:
        score += 1
    if has_digit:
        score += 1
    if has_symbol:
        score += 1
        
    # Standard security rule: any password shorter than 8 characters is immediately Weak
    if length < 8:
        return "Weak", "bg-danger", 15
        
    if score >= 5:
        return "Strong", "bg-success", 100
    elif score >= 3:
        return "Medium", "bg-warning", 60
    else:
        return "Weak", "bg-danger", 30
