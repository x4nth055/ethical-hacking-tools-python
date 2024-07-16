from password_strength import PasswordStats

def evaluate_password(password):
    """
    Evaluate the strength of a given password using the PasswordStats class from the password_strength library.

    Parameters:
    password (str): The password to be evaluated.

    Returns:
    float: A numerical value representing the strength of the password.

    The function creates a PasswordStats object using the provided password and returns the strength of the password.
    The strength is calculated based on various factors such as length, complexity, and common patterns.
    """

    stats = PasswordStats(password)
    return stats.strength()

# Example usage
passwords = ["weak", "password", "Password123", "Pass123!", "P@ssw0rd", "P@ssw0rd!", 
             "P@ssw0rd!123", "YouGotMe159@K", "EzatjeqRYTIERsoygjwqer@12"]
for pwd in passwords:
    strength = evaluate_password(pwd)
    print(f"Password: {pwd}, Strength: {strength:.2f}")
