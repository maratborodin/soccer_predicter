from dotenv import load_dotenv
import os
from telegram.ext import Updater, MessageHandler, CommandHandler, Application, ContextTypes, filters, ConversationHandler
from telegram import Update
from models import Team, Match, Tournament, Tour, TeamDoesNotExist
from sqlalchemy.sql import func
from sqlalchemy import or_
from models import session
from datetime import datetime
import logging

load_dotenv()
TOKEN = os.environ['TG_BOT_TOKEN']
handler = logging.FileHandler(f'telegram_bot.log', mode='a')
logger = logging.getLogger(__name__)
# logger.basicConfig(filename='telegram_bot.log', filemode='a', level=logger.INFO,
#                     format='%(asctime)s %(levelname)s %(message)s')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def show_menu():
    menu = """ Выберите действие:
    /tournament_goals Показать кол-во забитых мячей в конкретном турнире
    /average_goals Показать среднее кол-во забитых мячей за все турниры
    /match_stat Показать статистику матчей между командами
    """
    return menu


async def handle_start(update: Update, context: ContextTypes):
    logger.info('подключился новый пользователь')
    context.user_data['menu'] = 'menu'
    await update.message.reply_text(
        show_menu()
    )
    return 1


def show_tournaments():
    tournaments_data_str = ''
    tournament: Tournament #Аннотация типов
    for tournament in Tournament.query.all():
        tournaments_data_str += f'{tournament.id}. {tournament.name} ({tournament.years}) \n'
    logger.debug(f'вызван метод show_tournaments с результатом {tournaments_data_str}')
    return tournaments_data_str


def show_teams(team_list):
    team_data_str = ''
    team: Team #Аннотация типов
    for team in team_list:
        team_data_str += f'{team.id}. {team.name} \n'
    logger.debug(f'вызван метод show_teams с параметрами {team_list} и результатом {team_data_str}')
    return team_data_str


async def send_team_list(update: Update, context: ContextTypes, teams_data, message_text):
    message = f'{message_text}: \n {show_teams(teams_data)}'
    context.user_data['team'] = 'team'
    logger.debug(f'сформировано сообщение пользователю со списком команд {message}')
    await update.message.reply_text(message)


async def show_teams_for_average_goals(update: Update, context: ContextTypes):
    teams_data = Team.query.all()
    await send_team_list(update, context, teams_data, message_text='Выберите команду')
    logger.info('отправлено сообщение пользователю')
    return 4


def get_average_goals_message(team_id):
    avg_goals_count = Team.get_average_goals_count(team_id)
    message = f'Среднее кол-во забитых мячей командой во всех турнирах: {int(avg_goals_count)}'
    # current_time = datetime.now()
    # print(current_time)
    logger.debug(f'сформировано сообщение о среднем кол-ве голов команды {message}')
    return message


async def show_team_average_goals(update: Update, context: ContextTypes):
    team_id = update.message.text
    logger.info(f'пользователь запросил среднее кол-во голов команды {team_id}')
    try:
        message = get_average_goals_message(team_id)
        context.user_data.clear()
        await update.message.reply_text(message)
    except TeamDoesNotExist as error:
        logger.warning(f'пользователь запросил несуществующую команду {team_id}')
        await update.message.reply_text(error)
    logger.info('диалог завершен')
    return ConversationHandler.END


async def show_tournaments_for_goals(update: Update, context: ContextTypes):
    message = f'Выберите сезон: \n {show_tournaments()}'
    logger.debug(f'сформировано сообщение для выбор сезона {message}')
    context.user_data['tournament_id'] = True
    await update.message.reply_text(message)
    return 2


async def show_teams_for_goals(update: Update, context: ContextTypes):
    tournament_id = update.message.text
    logger.info(f'пользователь запросил демонстрацию команд для турнира {tournament_id}')
    context.user_data['tournament_id'] = tournament_id
    teams_data = Team.get_team_list_by_tournament(tournament_id)
    logger.debug(f'для турнира {tournament_id} получена команда {teams_data}')
    await send_team_list(update, context, teams_data, message_text='Выберите команду')
    return 3


async def show_team_tournament_goals(update: Update, context: ContextTypes):
    team_id = update.message.text
    logger.info(f'пользователь выбрал команду {team_id}')
    context.user_data['team_id'] = team_id
    team = Team.query.filter(Team.id == team_id).first()
    tournament_id = context.user_data['tournament_id']
    total_goals_count = team.get_all_goals_in_tournament(tournament_id)
    logger.debug(f'расчитано кол-во голов, забитых командой {total_goals_count}')
    message = f'Команда в этом турнире забила: {total_goals_count}'
    logger.info(f'сформировано сообщение с кол-вом голов {message}')
    context.user_data.clear()
    print(context.user_data)
    await update.message.reply_text(message)
    logger.info('завершение диалога')
    return ConversationHandler.END


async def choose_teams_for_match_statistic(update: Update, context: ContextTypes):
    teams_data = Team.query.all()
    logger.info(f'пользователю отправлено сообщение для выбора 2х команд из {teams_data}')
    await send_team_list(update, context, teams_data, message_text='Выберите 2 команды. Запишите их через пробел')
    return 5


async def show_teams_match_statistic(update: Update, context: ContextTypes):
    team_1_id, team_2_id = map(int, update.message.text.split(' '))
    logger.info(f'пользователь выбрал команды {team_1_id} {team_2_id}')
    team_1_wins, draws, team_2_wins = Team.get_teams_matches_statistic(team_1_id, team_2_id)
    team_1_name = Team.query.get(team_1_id).name
    team_2_name = Team.query.get(team_2_id).name
    message = f'{team_1_name} {team_1_wins} {team_2_name} {team_2_wins} ничьи {draws}'
    await update.message.reply_text(message)
    logger.info(f'пользователю отправлен результат встреч {team_1_name} {team_2_name} {message}')
    context.user_data.clear()
    return ConversationHandler.END
    # text = update.message.text
    # team_ids = text.split(' ')
    # team_1_id = int(team_ids[0])
    # team_2_id = int(team_ids[1])

async def handle_user_answer(update: Update, context: ContextTypes):
    print(context.user_data)
    if 'menu' in context.user_data:
        if context.user_data['menu'] == '1' or update.message.text == '1':
            message = await show_team_tournament_goals(update, context)
            context.user_data['menu'] = '1'
        elif update.message.text == '2':
            message = await show_team_average_goals(update, context)
            context.user_data['menu'] = '2'
    else:
        await handle_start(update, context)
        return
    await update.message.reply_text(message)


def main():
    logger.info('=====старт=====')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', handle_start))
    #app.add_handler(CommandHandler('tournament_goals', show_tournaments_for_goals))
    #app.add_handler(CommandHandler('start', handle_start))
    chain_1 = ConversationHandler(
        entry_points=[CommandHandler('tournament_goals', show_tournaments_for_goals), \
                      CommandHandler('average_goals', show_teams_for_average_goals),
                      CommandHandler('match_stat', choose_teams_for_match_statistic)],
        states={

            2: [MessageHandler(filters.TEXT, show_teams_for_goals)],
            3: [MessageHandler(filters.TEXT, show_team_tournament_goals)],
            4: [MessageHandler(filters.TEXT, show_team_average_goals)],
            5: [MessageHandler(filters.TEXT, show_teams_match_statistic)]
        },
        fallbacks=[CommandHandler('start', handle_start)]
    )
    app.add_handler(chain_1)
    #app.add_handler(MessageHandler(filters.TEXT, handle_user_answer))
    app.run_polling()
    logger.info('=====финиш=====')


if __name__ == '__main__':
    main()
