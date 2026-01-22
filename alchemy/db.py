# Définir la base de données
import os

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker

database_type = "sqlite"
# database_type = "mysql"

if database_type == 'mysql':
    DATABASE_URL = "mysql+pymysql://root:test@localhost:3306/ufolep_13volley"
else:
    db_file = "ufolep_volley.local.db"
    DATABASE_URL = f"sqlite:///{db_file}"

Base = declarative_base()


def create_db():
    # Créer un moteur de base de données
    engine = create_engine(DATABASE_URL)
    # Déclarer une base pour les modèles
    if database_type == 'sqlite':
        if os.path.exists(db_file):
            os.remove(db_file)
        Base.metadata.create_all(bind=engine)
    # Créer une session pour interagir avec la base de données
    Session = sessionmaker(bind=engine)
    return Session()
