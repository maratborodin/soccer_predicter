import json
from models import Tournament, Tour, Team, Match
from datetime import datetime as dt
from models import engine
from sqlalchemy.orm import sessionmaker
from models import session

file = open('tournaments.json', 'r')
data = json.loads(file.read())
tournament_list = []
team_dict = {}


def get_team(team_name):
    if team_name in team_dict:
        team = team_dict[team_name]
    else:
        team = Team(name=team_name)
        team_dict[team.name] = team
    return team


for tournament_data in data:
    tournament = Tournament(name=tournament_data['name'], years=tournament_data['season'])
    tournament_list.append(tournament)

    for tour_num, match_list in tournament_data['calendar'].items():
        tour = Tour(number=tour_num)
        tournament.tours.append(tour)

        for match_data in match_list:
            team_1 = get_team(match_data['team_1'])
            team_2 = get_team(match_data['team_2'])
            #time = match_data['time'] if match_data['time'] is not None else ''
            if match_data['time'] is not None:
                match_dt = dt.strptime(match_data['date']+match_data['time'], '%Y-%m-%d%H:%M:%S')
            else:
                match_dt = dt.strptime(match_data['date'] + '00:00:00', '%Y-%m-%d%H:%M:%S')
            match = Match(datetime=match_dt, team_1=team_1, team_2=team_2, score_1=match_data['score_1'],\
                          score_2=match_data['score_2'])
            tour.matches.append(match)

session.add_all(tournament_list)
session.commit()


#sqlalchemy документация, как сделать поля необязательными для заполнения, проверить внутри json пустые и в поле datetime заполнить значение None
#если такое есть,  возможно будет другая ошибка