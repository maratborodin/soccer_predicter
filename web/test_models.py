from unittest import TestCase
from unittest.mock import patch
from models import Team, TeamDoesNotExist, Match, Tour
from src.telegram.telegram_bot import get_average_goals_message
from datetime import datetime
from src.telegram import telegram_bot


class TeamTestCase(TestCase):


    def test_get_average_goals_count(self):
        count = Team.get_average_goals_count(5)
        self.assertEqual(float(count), 32.5)


    def test_get_average_goals_count_for_non_exist_team(self):
        with self.assertRaises(TeamDoesNotExist) as context:
            Team.get_average_goals_count(100)


class BotTestCase(TestCase):


    def test_show_team_average_goals(self):
        team_id = 5
        message = get_average_goals_message(team_id)
        self.assertEqual(message, 'Среднее кол-во забитых мячей командой во всех турнирах: 32')


    def test_time_mock(self):
        with patch('telegram_bot.datetime') as mock_time:
            mock_time.now.return_value = datetime(2000, 12, 5, 12, 0)
            message = get_average_goals_message(5)
            self.assertEqual(message, 'Среднее кол-во забитых мячей командой во всех турнирах: 32')


    @patch.object(telegram_bot.Team, '_get_tournaments',
                  lambda team_id: Team.query.filter(Team.id == team_id)
                  .join(Match, Team.id == Match.team_1_id)
                  .join(Tour)
                  .with_entities(Tour.tournament_id)
                  .distinct()
                  .filter(Match.datetime < datetime(2022, 1, 1)))
    def test_historic_average_goals_count(self):
        message = get_average_goals_message(5)
        self.assertEqual(message, 'Среднее кол-во забитых мячей командой во всех турнирах: 32')
