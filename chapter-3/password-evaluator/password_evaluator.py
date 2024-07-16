import string

def check_password_strength(password):
    """
    Check the strength of a password based on various criteria.

    Parameters:
    password (str): The password to be checked for strength.

    Returns:
    int: The strength score of the password (out of 5).
    """
    strength_score = 0
    # Check if password length is at least 8 characters
    if len(password) >= 8:
        strength_score += 1
    # Check if password contains at least one lowercase letter
    if any(c.islower() for c in password):
        strength_score += 1
    # Check if password contains at least one uppercase letter
    if any(c.isupper() for c in password):
        strength_score += 1
    # Check if password contains at least one digit
    if any(c.isdigit() for c in password):
        strength_score += 1
    # Check if password contains at least one special character
    if any(c in string.punctuation for c in password):
        strength_score += 1

    return strength_score

# Example usage
passwords = ["weak", "password", "Password123", "Pass123!", "P@ssw0rd", "P@ssw0rd!", 
             "P@ssw0rd!123", "YouGotMe159@K", "EzatjeqRYTIERsoygjwqer@12"]
for pwd in passwords:
    score = check_password_strength(pwd)
    print(f"Password: {pwd}, Strength Score: {score}/5")
