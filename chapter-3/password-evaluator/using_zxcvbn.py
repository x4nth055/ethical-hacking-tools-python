from zxcvbn import zxcvbn

def assess_password(password):
    """
    Assess the strength of a given password using the zxcvbn library.
    
    Parameters:
    password (str): The password to be assessed.
    
    Returns:
    tuple: A tuple containing the strength score (int) and feedback (dict) of the password.
    """
    # Use the zxcvbn library to analyze the password
    results = zxcvbn(password)
    # Extract the strength score and feedback from the results
    strength_score = results['score']
    feedback = results['feedback']
    return strength_score, feedback

# Example usage
passwords = ["weak", "password", "Password123", "Pass123!", "P@ssw0rd", "P@ssw0rd!", 
             "P@ssw0rd!123", "YouGotMe159@K", "EzatjeqRYTIERsoygjwqer@12"]
for pwd in passwords:
    # Assess the strength of each password in the list
    score, feedback = assess_password(pwd)
    # Print the password, its strength score, and suggestions for improvement
    print(f"Password: {pwd}, Strength Score: {score}/4")
    print(f"Suggestions: {feedback['suggestions']}")
