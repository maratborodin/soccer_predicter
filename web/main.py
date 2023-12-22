import requests
from bs4 import BeautifulSoup


headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

response = requests.get('https://www.championat.com/football/_russiapl/tournament/4987/table/', headers=headers)
#print(response.content)

parser = BeautifulSoup(response.content, 'html.parser')
results_table = parser.find('table', class_='results-table')
#print(results_table)

team_list = []

for tr in results_table.find('tbody').find_all('tr'):
    #print(tr.get_text())
    for td in tr.find_all('td'):
        print(td.get_text().strip())
    td_list = tr.find_all('td')
    team = \
        {
            'name': td_list[1].get_text().strip(),
            'games': td_list[2].get_text().strip(),
            'wins': td_list[3].get_text().strip(),
            'draws': td_list[4].get_text().strip(),
            'loses': td_list[5].get_text().strip(),
            'scored': td_list[6].get_text().strip().split('-')[0],
            'conceded': td_list[6].get_text().strip().split('-')[1]
        }
    team_list.append(team)

print(team_list)

#сделать похожую структуру для календаря игр
# {номер тура: [{дата: ..., время: ..., команда1: ..., команда2: ..., счет1: ..., счет2: ..., }, ]}
# вместо неизвестного счета использовать NAN



