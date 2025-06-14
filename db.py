"""
db.py file sets up the conenction to the PostgreSQL DB using SQLAlchemy
it defines the engine (which connects to the DB) and a session maker (used to communicate with the DB in our app)
db.py file is imported in our app.py so app can enable DB operations
"""



from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  
print("DATABASE_URL =", DATABASE_URL)

#create SQLAlchemy engine that manages the connection pool to the PostgreSQL db
engine = create_engine(DATABASE_URL)

#create a 'session' class, we will use this to create sessions for interacting to our PostgreSQL db
SessionLocal = sessionmaker(bind=engine)
