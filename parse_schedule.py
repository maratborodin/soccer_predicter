import requests
from bs4 import BeautifulSoup
import re
from unidecode import unidecode
from datetime import datetime
import json
import time
import random
from models import Tournament, Tour, Team, Match, session, exists
import logging

logger = logging.getLogger(__name__)
handler = logging.FileHandler(f'{__name__}.log', mode='a')
formatter = logging.Formatter('%(module)s %(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

# print(parser)

# for tr in parser.find_all('tr'):
#    print(tr.get_text())

match_schedule = []


def clear_text(text):
    text = text.strip()
    text = re.sub(r'[^а-яА-Яa-zA-Z0-9\-\:\.\s]*', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def cast_score(score):
    score = re.sub("[^0-9]", "", score)
    if not score:
        return None
    return int(score)


team_dict = {}

for team in Team.query.all():
    team_dict[team.name] = team


def get_team(team_name):
    if team_name in team_dict:
        team = team_dict[team_name]
    else:
        team = Team(name=team_name)
        team_dict[team.name] = team
    return team


def parse_calendar(url, tournament):
    new_matches_found = False
    response = requests.get(url, headers=headers)
    # print(response)

    parser = BeautifulSoup(response.content, 'html.parser')
    stats_table = parser.find('table', class_='stat-results__table')
    tournament_calendar = {}
    #print(stats_table.find('tbody').find_all('tr'))
    tour = None
    for tr in stats_table.find('tbody').find_all('tr'):
        # print(tr.get_text().strip())
        # for td in tr.find_all('td'):
        td_list = tr.find_all('td')
        tour_num = int(clear_text(td_list[2].get_text()))
        date_time = clear_text(td_list[3].get_text())  # .split(' ')
        if ' ' in date_time:
            date, time = date_time.split(' ')
        else:
            date = date_time
            time = None
        date = datetime.strptime(date, '%d.%m.%Y').date()
        if time is not None:
            time = datetime.strptime(time, '%H:%M').time()
        # print(date, time)
        # print(tour_num)
        a_list = tr.find_all('a')
        team_1_name = clear_text(a_list[1].get_text())
        team_2_name = clear_text(a_list[2].get_text())
        team_1 = get_team(team_1_name)
        team_2 = get_team(team_2_name)
        # print(url, clear_text(a_list[3].get_text()))
        score_data = a_list[3].get_text().split(':')
        score_1 = cast_score(clear_text(score_data[0]))
        score_2 = cast_score(clear_text(score_data[1]))
        # match = \
        #     {
        #         'date': date,#date.strftime('%d.%m.%Y'),
        #         'time': time,#time.strftime('%H:%M'),
        #         'team_1': team_1,
        #         'team_2': team_2,
        #         'score_1': score_1,
        #         'score_2': score_2
        #     }
        match_dt = datetime.combine(date, time)
        if date and time and team_1 and team_2:
            if not match or not match.score_1 and not match.score_2:
                match = Match.query.filter((Match.datetime==match_dt)&(Match.team_1==team_1)&(Match.team_2==team_2)).first()
                if match:
                    match.score_1 = score_1
                    match.score_2 = score_2
                else:
                    match = Match(datetime=match_dt, team_1=team_1, team_2=team_2, score_1=score_1, score_2=score_2)
                    new_matches_found = True
                if tour is None or tour.number != tour_num:
                    if tournament.id:
                        tour = Tour.query.filter((Tour.number == tour_num)&(Tour.tournament == tournament)).first()
                    if not tour or not tournament.id:
                        tour = Tour(number=tour_num)
                        tournament.tours.append(tour)
                        logger.info('add tour')
                tour.matches.append(match)
                logger.info('add match')
        else:
            break
    return new_matches_found
    # print(tournament)
    # print(match)
    # match_schedule.clear()
    # match_schedule.append(match)
    # print(match_schedule)


def main():

    logger.info('----start----')
    domain = 'https://www.championat.com'
    base_url = f'{domain}/football/_russiapl/tournament/4987/'
    # response = requests.get(base_url, headers=headers)
    # parser = BeautifulSoup(response.content, 'html.parser')
    # year_select = parser.find('select', {'name': 'year'})
    # print(year_select)
    links = ['/football/_russiapl/tournament/4987/'
             # , '/football/_russiapl/tournament/3953/calendar',
             # '/football/_russiapl/tournament/2973/calendar'
             ]  # собрать все календари (3-4 штуки) в список,
    # добавлять слово calendar в конце, отправить ссылку в функцию парсинга
    # получить из функции данные из календаря и встроить его в бОльший словарь (еще один уровень), где ключ - год

    # for i in links:
    #    pars_calendar(f'{domain}'+i)

    # for year_option in year_select.find_all('option'):
    #    if year_option.has_attr('data-href'):
    #        year_url = year_option['data_href']
    #        print(year_url)


    response = requests.get(base_url, headers=headers)
    # # print(response)
    parser = BeautifulSoup(response.content, 'html.parser')
    income_tournaments_data = json.loads(parser.find('script', class_='js-entity-header-select-data').get_text())

    tournaments_data = []
    tournament_list = []
    # print(income_tournaments_data)

    # year_list = parser.find_all('div', class_='select')
    # #print(parser.select_one('option[selected]'))
    for index, tournament in enumerate(income_tournaments_data):
        # print(tournament, '\n\n')
        if not tournament['data']:
            link = tournament["href"]
            name = tournament['name']
        else:
            for sub_tournament in tournament['data']:
                if 'высшая лига' not in sub_tournament['title'].lower() and 'высший дивизион' not in sub_tournament['title'].lower() \
                        and 'премьер-лига' not in sub_tournament['title'].lower():
                    continue

                link = sub_tournament["href"]
                name = sub_tournament['title']
                break
        time.sleep(random.randint(3, 10))
        tournament_object = Tournament.query.filter(Tournament.name==name, Tournament.years==tournament['label']).first()
        if not tournament_object:
            tournament_object = Tournament(name=name, years=tournament['label'])
            logger.info('add tournament')
        else:
            logger.info('already exists')
        tournament_list.append(tournament_object)
        new_matches_found = parse_calendar(f'{domain}{link}calendar', tournament_object)
        if not new_matches_found:
            break

        # current_data = {'season': tournament['label'], 'name': name, 'calendar': calendar}
        # tournaments_data.append(current_data)
        #break
    # print(tournaments_data)
    # tournaments_json = json.dumps(tournaments_data, default=str, ensure_ascii=False)
    # file = open('tournaments.json', 'w')
    # file.write(tournaments_json)
    # file.close()
    session.add_all(tournament_list)
    session.commit()
    logger.info('----finish----')

if __name__=='__main__':
    main()