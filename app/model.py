from sqlalchemy import *

from app import db

class House(db.Model):
    id = Column(Integer, primary_key=True)
    guid = Column(String, nullable=False) #, unique=True
    link = Column(String, nullable=False)
    size = Column(Integer, nullable=True)
    expense = Column(Float, nullable=False)
    address = Column(String, nullable = True)
    price = Column(Float, nullable=False)
    favorite = Column(Boolean, nullable=False)
