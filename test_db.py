"""
test_db.py is a simple test script to verify:
* we can connect to PostgreSQL DB
* we can insert a user into the user_data table
* we can read that user back
"""

from db import SessionLocal #our session factory
from models import Users #our Users Model
from datetime import datetime, timezone


#create a new session (our connection to DB)
db = SessionLocal()

try:
    #create a new user obj
    new_user = Users(
        username="kailee",
        email="kailee@example.com",
        password_hashed="kaileepassowrd",
        date_created=datetime.now(timezone.utc),
        profile_picture="123421.jpg",
        last_login=datetime.now(timezone.utc),
        active_status=True
    )

    #add 'new_user' to session
    db.add(new_user) 

    #commit the transaction (saves to DB)
    db.commit()

    #refresh to get the generated ID back
    db.refresh(new_user)


    print(f"User successfully added with ID: {new_user.id!r}")

    #query the user back
    user_from_db = db.query(Users).filter_by(id=new_user.id).first()
    print("User from the DB:", user_from_db)

except Exception as e:
    print("error during DB operation: ",e)
    db.rollback()

finally:
    #always close session
    db.close()
