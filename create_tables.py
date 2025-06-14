"""
this is a one-time set up script that creates all the tables in our PostgreSQL DB
imports the models and the engine, then runs Base.metadata.create_all(engine) to build
this create_tables.py is only ran when initializing or updating the DB
"""

from sqlalchemy import create_engine
from models import Base #import Base and my models from models.py file
import os

from db import engine
from models import Base


#******************
#Database set up:
#******************

#create tables
Base.metadata.create_all(engine)