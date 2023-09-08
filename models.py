'''
Модуль, отвечающий за модели в БД
Основные классы:
Team - Команды, уччаствующие в турнирах РПЛ
Tournament - Турнир РПЛ(сезон), проводимый в определенный год
Tour - Тур в рамках одного турнира(1 матч в туре для каждой команды)
Match - Игра между двумя командами в туре
'''

import sqlalchemy as db
from sqlalchemy.orm import relationship, sessionmaker, declarative_base, mapped_column, scoped_session
from sqlalchemy.sql import func, exists
from sqlalchemy.pool import NullPool
import logging

engine = db.create_engine('sqlite:///tournament.sqlite', poolclass=NullPool)
Base = declarative_base()
Session = sessionmaker(engine)
ScopedSession = scoped_session(Session)
session = ScopedSession()
logger = logging.getLogger(__name__)
handler = logging.FileHandler(f'{__name__}.log', mode='a')
formatter = logging.Formatter('%(module)s %(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

class Model:
    '''
    Технический класс, используемый в качестве базового для других моделей. Дополняет каждый класс-наследник полем ID и
    атрибутом query, предоставляющим возможность формирования запросов к БД
    '''
    query = ScopedSession.query_property()
    id = db.Column(db.Integer, primary_key=True)


class Tournament(Model, Base):
    __tablename__ = 'tournament'
    name = db.Column(db.String(255))
    years = db.Column(db.String(9))
    tours = relationship('Tour', back_populates='tournament')


class Tour(Model, Base):
    __tablename__ = 'tour'
    number = db.Column(db.Integer)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))
    tournament = relationship('Tournament', back_populates='tours')
    matches = relationship('Match', back_populates='tour')


class TeamDoesNotExist(Exception):
    pass


class Team(Model, Base):
    '''
    Класс команды-участника турнира.

    Attributes:
        name - название команды
        host_matches - связь с объектами матчей, являющимися домашними для команды
        guest_matches - связь с объектами матчей, являющимися гостевыми для команды

    Methods:
        get_all_goals_in_tournament - метод, возвращающий общее кол-во голов в турнире
        get_average_goals_count - метод, возвращающий среднее кол-во забитых голов командой во всех турнирах
        get_teams_matches_statistic - метод, возвращающий статистику между командами (победы, ничьи и поражения)
        get_team_list_by_tournament - статический метод, возвращающий список команд в турнире

    Properties:
        players_count - кол-во игроков в команде
    '''
    __tablename__ = 'team'
    name = db.Column(db.String(255))
    host_matches = relationship('Match', back_populates='team_1', lazy='dynamic', foreign_keys='Match.team_1_id')
    guest_matches = relationship('Match', back_populates='team_2', lazy='dynamic', foreign_keys='Match.team_2_id')
    __players_count = 15

    @property
    def players_count(self) -> int:
        '''
        getter свойство возвращает кол-во игроков в команде

        Return:
            число игроков в команде
        '''
        return self.__players_count

    @players_count.setter
    def players_count(self, value: int):
        '''
        setter свойство устанавливает кол-во игроков в команде, проверяя его на требование минимального кол-ва игроков

        Arguments:
            value - устанавливаемое кол-во игроков в команде
        '''
        if value < 11:
            raise ValueError('Not enough players count in the team')
        self.__players_count = value

    @staticmethod
    def _get_tournaments(team_id):
        return Team.query.filter(Team.id == team_id) \
            .join(Match, Team.id == Match.team_1_id) \
            .join(Tour) \
            .with_entities(Tour.tournament_id).distinct()


    @staticmethod
    def get_average_goals_count(team_id: int) -> float:
        '''
        Вычисляет на основе данных БД среднее кол-во забитых голов во всех турнирах

        Arguments:
            team_id - идентификатор команды в БД

        Return:
            возвращает результат расчета среднего кол-ва забитых голов во всех турнирах
        '''
        if not session.query(exists().where(Team.id == team_id)).scalar():
            raise TeamDoesNotExist(f"Team with {team_id} does not exist in a database")
        tournaments = Team._get_tournaments(team_id).subquery()

        tournaments_count = session.query(tournaments) \
            .with_entities(func.count(tournaments.c.tournament_id) \
                           .label('count')).subquery()

        goals_count_1 = Team.query.filter(Team.id == team_id) \
            .join(Match, Team.id == Match.team_1_id) \
            .with_entities(func.sum(Match.score_1).label('total_1')) \
            .subquery()

        goals_count_2 = Team.query.filter(Team.id == team_id) \
            .join(Match, Team.id == Match.team_1_id) \
            .with_entities(func.sum(Match.score_2).label('total_2')) \
            .subquery()

        avg_goals_count: float = session.query(goals_count_1, goals_count_2) \
            .with_entities \
                (
                (goals_count_1.c.total_1 + goals_count_2.c.total_2)
                / tournaments_count.c.count
            ) \
            .scalar()
        logger.debug(f'расчитанное среднее кол-во голов для команды {team_id} = {avg_goals_count}')
        return avg_goals_count

    @staticmethod
    def get_team_list_by_tournament(tournament_id):
        teams_data = Tournament.query.filter(Tournament.id == tournament_id) \
            .join(Tour) \
            .join(Match) \
            .join(Team, Team.id == Match.team_1_id) \
            .with_entities(Team.id, Team.name) \
            .distinct() \
            .order_by(Team.id) \
            .all()
        return teams_data

    def get_all_goals_in_tournament(self, tournament_id):
        goals_count_1 = Match.query.join(Tour) \
            .join(Tournament) \
            .filter(Tournament.id == tournament_id, \
                    Match.team_1_id == self.id, \
                    Match.score_1 != None) \
            .with_entities(func.sum(Match.score_1).label('total_1')) \
            .subquery()
        goals_count_2 = Match.query.join(Tour) \
            .join(Tournament) \
            .filter(Tournament.id == tournament_id, \
                    Match.team_2_id == self.id, \
                    Match.score_2 != None) \
            .with_entities(func.sum(Match.score_2).label('total_2')) \
            .subquery()
        total_goals_count = session.query(goals_count_1, goals_count_2) \
            .with_entities((goals_count_1.c.total_1 + goals_count_2.c.total_2)) \
            .scalar()
        return total_goals_count

    @staticmethod
    def _get_won_matches(team_1_id, team_2_id):
        return Match.query.filter(((Match.team_1_id == team_1_id) & \
                            (Match.team_2_id == team_2_id) & (Match.score_1 > Match.score_2)) | \
                           ((Match.team_1_id == team_2_id) & \
                            (Match.team_2_id == team_1_id) & (Match.score_2 > Match.score_1))
                           ).count()

    @staticmethod
    def get_teams_matches_statistic(team_1_id, team_2_id):
        team_1_wins = Team._get_won_matches(team_1_id, team_2_id)
        team_2_wins = Team._get_won_matches(team_2_id, team_1_id)
        draws = Match.query.filter((((Match.team_1_id == team_1_id) & \
                            (Match.team_2_id == team_2_id)) | \
                           ((Match.team_1_id == team_2_id) & \
                            (Match.team_2_id == team_1_id))) & \
                            (Match.score_1 == Match.score_2)
                           ).count()
        #for x in team_1_wins:
        #    print(x.team_1_id, x.team_2_id, x.score_1, x.score_2)
        return team_1_wins, draws, team_2_wins

class Match(Model, Base):
    __tablename__ = 'match'
    datetime = db.Column(db.DateTime, nullable=True, default=None)
    score_1 = db.Column(db.SmallInteger, nullable=True)
    score_2 = db.Column(db.SmallInteger, nullable=True)

    team_1_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team_1 = relationship('Team', back_populates='host_matches', foreign_keys=[team_1_id])

    team_2_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team_2 = relationship('Team', back_populates='guest_matches', foreign_keys=[team_2_id])

    tour_id = db.Column(db.Integer, db.ForeignKey('tour.id'))
    tour = relationship('Tour', back_populates='matches')

#TODO почитать по UML про визуализацию