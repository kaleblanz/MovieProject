"""
generates and verifies secure, time limited tokens for email confirmation during a new user registering an account
"""
import os
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

#salt is an additional value added to the cryptographic operations
#this salt is specifcally for email confirmations
SECURITY_SALT = "email-confirmation"
 

def generateConfirmationToken(email):
    """
    :param email: user's email address to include in the token
    :return: a signed token string that can be sent via email
    """
    #create a serializer obj that will sign and encode data securley
    serializer = URLSafeTimedSerializer(secret_key=SECRET_KEY)

    #use serializer obj to created a signed token containing the user's email
    #the salt adds extra security and identifies the tokens purpose
    token = serializer.dumps(email, salt=SECURITY_SALT)
    
    #returns the generated token ( a string that can be sent via email)
    return token



def confirmToken(token, expiration=3600):
    """
    Goal: Verify and decode a token to get the origianl email

    :param token: the token string to validate
    :param expiration: the time in seconds before the token expires (default 1 hour)
    :return: the email address if the token is valid and not expired, else None
    """
    #create a serialzer obj with the secret key to decode the token
    serialzer = URLSafeTimedSerializer(secret_key=SECRET_KEY)
    try:
        #try to load and verify the token using the same salt and exp. time
        email = serialzer.loads(token, salt=SECURITY_SALT, max_age=expiration)
    except Exception:
        #if the tokenis invalid or expired, return None
        return None
    #if successful, return the email stored inside the token
    return email