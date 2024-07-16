from faker import Faker
from pprint import pprint

def generate_user_data(locale='en_US'):
    """
    Generates fake user data.
    
    Args:
    locale (str): Locale code to generate data for specific regions.
    
    Returns:
    dict: A dictionary containing fake user details.
    """
    fake = Faker(locale)
    user_data = {
        "name": fake.name(),
        "address": fake.address(),
        "email": fake.email(),
        "date_of_birth": fake.date_of_birth(),
        "company": fake.company(),
        "job": fake.job(),
        "ssn": fake.ssn(),
        "phone_number": fake.phone_number(),
        "profile": fake.simple_profile()
    }
    return user_data

# Example usage
for _ in range(5):
    print("*"*50)
    pprint(generate_user_data())
