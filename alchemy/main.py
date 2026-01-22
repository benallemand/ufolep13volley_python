from datetime import datetime

from alchemy.db import database_type, create_db
from alchemy.model import Club, Team, User, Activity


def add_data(_session):
    nouveau_club = Club(nom="Club Alpha")
    nouvelle_equipe = Team(nom_equipe="Equipe A", club=nouveau_club)
    nouvel_utilisateur = User(login="jdupont", email="jdupont@example.com", team=nouvelle_equipe)
    activity = Activity(activity_date=datetime.now(), user=nouvel_utilisateur, comment="j'ai créé cette activité !")
    _session.add(nouvel_utilisateur)
    _session.add(activity)
    _session.commit()

session = create_db()

if database_type == 'sqlite':
    add_data(session)

query = (session.query(User)
         # .filter(User.id == 864)
         )
# user = query.first()
users = query.all()
for user in users:
    print(
        f"User {user.id}: {user.login} - {user.email} - {user.team.nom_equipe if user.team else ''} - {user.team.club.nom if user.team else ''}")
    last_activity = user.activities[-1] if user.activities else None
    if last_activity:
        print(f"{last_activity.activity_date} - {last_activity.comment}")

# Fermer la session
session.close()
