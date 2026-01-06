import random

def generate_numeric_otp(length=6):
    """
    Generates a numeric OTP of specified length.
    Default length is 6 digits.
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])
