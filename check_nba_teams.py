#!/usr/bin/env python3

from libs.common.database import get_db
from libs.common.questionnaire_models import Team, Sport
from sqlalchemy.orm import sessionmaker

def check_nba_teams():
    engine = get_db()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Find Basketball sport
        basketball_sport = session.query(Sport).filter(Sport.name == 'Basketball').first()

        if not basketball_sport:
            print('Basketball sport not found')
            return

        print(f'Basketball sport found: {basketball_sport.name} (ID: {basketball_sport.id})')

        # Find NBA teams
        nba_teams = session.query(Team).filter(
            Team.sport_id == basketball_sport.id,
            Team.league == 'NBA'
        ).all()

        print(f'\nFound {len(nba_teams)} NBA teams:')
        for i, team in enumerate(nba_teams, 1):
            print(f'{i:2d}. {team.name} ({team.city})')

        # Also check all basketball teams
        all_basketball_teams = session.query(Team).filter(
            Team.sport_id == basketball_sport.id
        ).all()

        print(f'\nTotal basketball teams: {len(all_basketball_teams)}')
        leagues = set(team.league for team in all_basketball_teams if team.league)
        print(f'Leagues: {sorted(leagues)}')

    finally:
        session.close()

if __name__ == '__main__':
    check_nba_teams()
