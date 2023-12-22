from fastapi import FastAPI, APIRouter
from models import Team, session, Tournament
from schemes import TeamScheme
from typing_extensions import TypedDict

app = FastAPI()
team_router = APIRouter(prefix="/teams", tags=['teams'])
tournament_router = APIRouter(prefix="/tournaments", tags=['tournaments'])

@team_router.get('/')
async def get_team_list():
    return Team.query.all()


@tournament_router.get('/')
async def get_tournament_list():
    return Tournament.query.all()


@team_router.get('/{team_id}')
async def get_team_detail(team_id:int):
    return Team.query.get(team_id)


@team_router.post('/')
async def add_team(team_data:TeamScheme):
    team = Team(name=team_data.name)
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


@team_router.put('/{team_id}')
async def update_team(team_id:int, team_data:TeamScheme):
    team = Team.query.get(team_id)
    team.name = team_data.name
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


@team_router.delete('/{team_id}')
async def delete_team(team_id:int):
    team = Team.query.get(team_id)
    session.delete(team)
    session.commit()
    return {'status': f'{team_id} is deleted'}


@team_router.patch('/{team_id}')
async def partial_update_team(team_id:int, team_data:TeamScheme):
    team = Team.query.get(team_id)
    team.name = team_data.name
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


class GoalsCountScheme(TypedDict):
    team_id:int
    count:float

@team_router.get('/{team_id}/get_average_goals_count')
async def get_average_goals_count(team_id:int)->GoalsCountScheme:
    count = Team.get_average_goals_count(team_id)
    result:GoalsCountScheme = {'team_id': team_id, 'count': count}
    return result


@team_router.get('/{tournament_id}/team_list_by_tournament')
async def get_team_list_by_tournament(tournament_id:int):
    teams = Team.get_team_list_by_tournament(tournament_id)
    teams_data = []
    for team in teams:
        teams_data.append({'id':team[0],'name':team[1]})
    print(teams_data)
    return teams_data


@team_router.get('/{team_id}/{tournament_id}/get_goals_count_by_tournament/')
async def get_goals_count_by_tournament(team_id:int, tournament_id:int):
    team = Team.query.get(team_id)
    total_goals_count = team.get_all_goals_in_tournament(tournament_id)
    return {'total_goals_count': total_goals_count}


@team_router.get('/{team_id_1}/{team_id_2}/get_teams_matches_statistic/')
async def get_teams_matches_statistic(team_id_1:int, team_id_2:int):
    """
    Получение статистики результатов игр между 2мя командами. Отображает сколько какая команда матчей выиграла и сколько было ничей

    Arguments
        team_id_1: номер первой команды
        team_id_2: номер второй команды

    Returns
        json с количеством побед каждой из команд и количество нечей. Данные отображаются в telegramm боте
    """
    matches_data = Team.get_teams_matches_statistic(team_id_1, team_id_2)
    return {'team_1_wins':matches_data[0], 'draws':matches_data[1], 'team_2_wins':matches_data[2]}

app.include_router(team_router)
app.include_router(tournament_router)