"""
models.py contains all of our database models using SQLAlchemy ORM
each class is a table in PostgreSQL DB
"""


#SQLAlchemy will translate our python commands into SQL and PostgreSQL server runs them
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

#Base class for our ORM models (each models = table in DB)
Base = declarative_base()

#define a Users model (this creates a 'user_data' table in the PostgreSQL DB)
class Users(Base):
    __tablename__ = "user_data" #table name in the DB

    #unique ID for each user 
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String,nullable=False)
    email = Column(String, nullable=False)
    password_hashed = Column(String, nullable=False) #hashed version of user's actual password
    date_created = Column(DateTime, nullable=False) #when user's account was created
    profile_picture = Column(String, nullable=False)
    last_login = Column(DateTime, nullable=False)
    active_status = Column(Boolean, nullable=False)
    is_verified = Column(Boolean, default=False)

    #__repr__() is the official string representation of an object
    #like the toString() method in Java
    def __repr__(self):
        #!r shows the values more clearly, a string will still have its quotes around it
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r}, password_hashed={self.password_hashed!r}, date_created={self.date_created!r}, profile_picture={self.profile_picture!r}, last_login ={self.last_login!r}, active_status={self.active_status!r})"
