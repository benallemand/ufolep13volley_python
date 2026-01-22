from typing import Any

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from alchemy.db import Base


class Activity(Base):
    __tablename__ = 'activity'

    id = Column(Integer, primary_key=True)
    comment = Column(String(400))
    activity_date = Column(DateTime)
    user_id = Column(Integer, ForeignKey("comptes_acces.id"))

    user = relationship("User", back_populates="activities")

    def __init__(self, comment, activity_date, user, **kw: Any):
        super().__init__(**kw)
        self.comment = comment
        self.activity_date = activity_date
        self.user = user


class Club(Base):
    __tablename__ = 'clubs'

    id = Column(Integer, primary_key=True)
    nom = Column(String(200))


class Team(Base):
    __tablename__ = 'equipes'

    id_equipe = Column(Integer, primary_key=True)
    id_club = Column(Integer, ForeignKey("clubs.id"))
    nom_equipe = Column(String(50))

    club = relationship("Club")

    def __init__(self, nom_equipe, club, **kw: Any):
        super().__init__(**kw)
        self.nom_equipe = nom_equipe
        self.club = club


# Définir une classe représentant une table
class User(Base):
    __tablename__ = 'comptes_acces'

    id = Column(Integer, primary_key=True)
    login = Column(String(200))
    email = Column(String(200))
    id_equipe = Column(Integer, ForeignKey("equipes.id_equipe"), nullable=True)

    team = relationship("Team")

    activities = relationship("Activity", back_populates="user")

    def __init__(self, login, email, team, **kw: Any):
        super().__init__(**kw)
        self.login = login
        self.email = email
        self.team = team
