from asyncio import create_subprocess_shell
import telebot
import webbrowser
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from models import User, Game
import database

bot = telebot.TeleBot('6959698313:AAFdydVvZvEbJ-n8kb6OKlZTJyATQPCVkIQ')

#=======================================================================ADMINS_LOADER====================================================
adminsIdFile = open('adminsID.txt', 'r')
adminsId = [int(line.strip()) for line in adminsIdFile]
adminsIdFile.close()

#========================================================================REQUIRED_ADDITIONAL_STUFF=======================================

users = {} #Возможная идея, хранить юзеров в словаре по системам игр, а не по id
#basicUser = User(000000000, 'Karl', 'Karlovich', ['Понедельник'], ['DnD'])
games = {}
#basicGame = Game(0, "Базовая Игра", 'url:address', datetime(2024, 9, 1), datetime(2024, 9, 1, 15, 30), 'DnD') 
#games[basicGame.gameID] = basicGame
gamesID = 0

database.startBD()
usersFromDB = database.loadUsers()
gamesFromBD = database.loadGames()


for el in usersFromDB:
    rawGameDays = el.userGameDays.split(',')
    rawSystems = el.userSystems.split(',')
    users[el.userID] = User(el.userID, el.userFirstName, None, rawGameDays, rawSystems)

for el in gamesFromBD:
    rawGameDate = datetime.strptime(el.gameDate, '%Y-%m-%d')
    rawGamePubDate = datetime.strptime(el.gamePublicationDate, '%Y-%m-%d %H:%M:%S') #2024-02-01 01:09:00
    games[el.gameID] = Game(el.gameID, el.gameText, el.gamePhoto, rawGameDate, rawGamePubDate, el.gameSystem)

user_choices = {}
user_choices_dub = {}
user_game_systems = {}

days_translation = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}


#=======================================================================SCHEDULER_FUNC====================================================

def load_games():
    today = datetime.now().date()
    users_send_to = []

    for game_id, game in games.items():
        publication_date = game.gamePublicationDate

        if publication_date.date() == today:
            game_day = days_translation[game.gameDate.strftime('%A')]

            for userId, user in users.items():
                if game.gameSystem in user.userSystems and game_day in user.userGameDays:
                    users_send_to.append(user)

            scheduler.add_job(publish_game, 'date', run_date=publication_date, args=[game_id, users_send_to[:]])
            users_send_to = []

    #gameLoaded = Game()
    #gameLoaded.load_games()


#========================================================================SCHEDULER========================================================

scheduler = BackgroundScheduler()
scheduler.add_job(load_games, 'cron', hour=19, minute=10)  # Загружаем игры на этот день
scheduler.start()

#=======================================================================START_HANDLER====================================================

@bot.message_handler(commands = ['start'])
def start(message):
    
    
    flagNewUser = True

    for user in users:
        if message.from_user.id == user:
            flagNewUser = False
            break

    #=======================================================================ADMIN====================================================

    if message.from_user.id in adminsId:
        addGameBut = types.InlineKeyboardMarkup()
        addGameBut.add(types.InlineKeyboardButton('Добавить игру', callback_data= 'add_game'))
        bot.send_message(message.chat.id, f'Привет админ, {message.from_user.first_name} id: {message.from_user.id}', reply_markup=addGameBut )

    #=======================================================================OLD_USER====================================================
    
    elif flagNewUser != True:
        editNotBut = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Настроить уведомления', callback_data= 'ed_not')
        btn2 = types.InlineKeyboardButton('Остановить отправку уведомлений', callback_data= 'stopNotifications')
        editNotBut.row(btn1, btn2)
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} ID: {message.from_user.id}', reply_markup = editNotBut)

    #=======================================================================NEW_USER====================================================

    else:
        editNotBut = types.InlineKeyboardMarkup()
        editNotBut.add(types.InlineKeyboardButton('Настроить уведомления', callback_data= 'ed_not'))

        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} , ты у нас новенький, мы тебя запомним')
        newUser = User(message.from_user.id, message.from_user.first_name, message.from_user.last_name, [], [])
        users[newUser.userID] = newUser
        bot.send_message(message.chat.id, 'Также давай определимся, когда и во что ты хочешь играть', reply_markup = editNotBut)


#=======================================================================VK_HANDLER====================================================

@bot.message_handler(commands = ['vk'])
def vk(message):
    bot.send_message(message.chat.id, f'Наша группа вк: https://vk.com/trpg_nsu')


#=======================================================================BUTTONS_HANDLER====================================================

@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    chat_id = callback.message.chat.id

    if callback.data == 'add_game':
        global gamesID 
        gamesID+=1
        bot.send_message(callback.message.chat.id, 'Введите текст сообщения к игре')
        bot.register_next_step_handler(callback.message, gameText_handler)

    elif callback.data == 'add_photo':
        bot.send_message(callback.message.chat.id, 'Добавьте фото к игре')
        bot.register_next_step_handler(callback.message, get_photo)

    elif callback.data == 'add_date':
        bot.send_message(callback.message.chat.id, 'Введите дату игры в формате дд.мм.гггг')
        bot.register_next_step_handler(callback.message, gameDate_handler)

    elif callback.data == 'add_system':
        sysBut = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('DnD 5e', callback_data= 'system1') #Переделать этот пиздец нормально после релиза
        btn2 = types.InlineKeyboardButton('DnD 2024', callback_data= 'system2')
        btn3 = types.InlineKeyboardButton('Cyberpunk RED', callback_data= 'system3')
        btn4 = types.InlineKeyboardButton('FATE Core', callback_data= 'system4')
        btn5 = types.InlineKeyboardButton('10 свечей', callback_data= 'system5')
        btn6 = types.InlineKeyboardButton('Другие системы', callback_data= 'system6')
        sysBut.add(btn1, btn2, btn3, btn4, btn5, btn6)

        bot.send_message(callback.message.chat.id, 'Выберете систему:', reply_markup=sysBut)

    elif callback.data == 'system1':
        addpubDateoBut = types.InlineKeyboardMarkup()
        addpubDateoBut.add(types.InlineKeyboardButton('Добавить время публикации', callback_data= 'add_pubDate'))

        bot.send_message(callback.message.chat.id, 'Система сохранена', reply_markup=addpubDateoBut)
   
        games[gamesID].gameSystem = 'DnD 5e'

        gameSys = open('gameSys.txt', 'w')
        gameSys.write('DnD 5e')
        gameSys.close()

    elif callback.data == 'system2':
        addpubDateoBut = types.InlineKeyboardMarkup()
        addpubDateoBut.add(types.InlineKeyboardButton('Добавить время публикации', callback_data= 'add_pubDate'))

        bot.send_message(callback.message.chat.id, 'Система сохранена', reply_markup=addpubDateoBut)

        games[gamesID].gameSystem = 'DnD 2024'

        gameSys = open('gameSys.txt', 'w')
        gameSys.write('DnD 2024')
        gameSys.close()

    elif callback.data == 'system3':
        addpubDateoBut = types.InlineKeyboardMarkup()
        addpubDateoBut.add(types.InlineKeyboardButton('Добавить время публикации', callback_data= 'add_pubDate'))

        bot.send_message(callback.message.chat.id, 'Система сохранена', reply_markup=addpubDateoBut)

        games[gamesID].gameSystem = 'Cyberpunk RED'

        gameSys = open('gameSys.txt', 'w')
        gameSys.write('Cyberpunk RED')
        gameSys.close()

    elif callback.data == 'system4':
        addpubDateoBut = types.InlineKeyboardMarkup()
        addpubDateoBut.add(types.InlineKeyboardButton('Добавить время публикации', callback_data= 'add_pubDate'))

        bot.send_message(callback.message.chat.id, 'Система сохранена', reply_markup=addpubDateoBut)

        games[gamesID].gameSystem = 'FATE Core'

        gameSys = open('gameSys.txt', 'w')
        gameSys.write('FATE Core')
        gameSys.close()

    elif callback.data == 'system5':
        addpubDateoBut = types.InlineKeyboardMarkup()
        addpubDateoBut.add(types.InlineKeyboardButton('Добавить время публикации', callback_data= 'add_pubDate'))

        bot.send_message(callback.message.chat.id, 'Система сохранена', reply_markup=addpubDateoBut)

        games[gamesID].gameSystem = '10 свечей'

        gameSys = open('gameSys.txt', 'w')
        gameSys.write('10 свечей')
        gameSys.close()

    elif callback.data == 'system6':
        addpubDateoBut = types.InlineKeyboardMarkup()
        addpubDateoBut.add(types.InlineKeyboardButton('Добавить время публикации', callback_data= 'add_pubDate'))

        bot.send_message(callback.message.chat.id, 'Система сохранена', reply_markup=addpubDateoBut)

        games[gamesID].gameSystem = 'Другие системы'

        gameSys = open('gameSys.txt', 'w')
        gameSys.write('Другие системы')
        gameSys.close()

    elif callback.data == 'add_pubDate':
        
        bot.send_message(callback.message.chat.id, 'Введите дату публикации в формате дд.мм.гггг чч:мм')
        bot.register_next_step_handler(callback.message, gamePubDate_handler)

    elif callback.data == 'add_end':
         bot.send_message(callback.message.chat.id, 'Добавление игры успешно завершено')

    elif callback.data == 'ed_not':
        user_choices[callback.message.chat.id] = []
        bot.send_message(callback.message.chat.id, 'Выбери дни, когда хочешь играть', reply_markup=create_weekday_keyboard())

    elif callback.data == 'stopNotifications':
        stopNotButt = types.InlineKeyboardMarkup()
        bt1 = types.InlineKeyboardButton('Да', callback_data= 'yes_stopNotifications')
        bt2 = types.InlineKeyboardButton('Нет', callback_data= 'no_stopNotifications')
        stopNotButt.row(bt1, bt2)
        bot.send_message(callback.message.chat.id,'Вы точно хотите остановить отправку сообщений? Это приведёт к удалению ваших настроек', reply_markup=stopNotButt)

    elif callback.data == 'yes_stopNotifications':
        bot.send_message(callback.message.chat.id,'Вам больше не будут приходить оповещения')
        database.delUser(users[callback.message.chat.id])
        del users[callback.message.chat.id]
        

    elif callback.data == 'no_stopNotifications':
        bot.send_message(callback.message.chat.id,'Опопвещения продолжат приходить')
        

    if callback.data == "done":
  
        eddNotSysBut = types.InlineKeyboardMarkup()
        eddNotSysBut.add(types.InlineKeyboardButton('Выбрать игровую систему', callback_data= 'ed_gameSys'))
       
        chosen_days = user_choices.get(chat_id, [])
        response_text = "Вы выбрали: " + ", ".join(chosen_days) if chosen_days else "Вы выбрали все дни."
        bot.send_message(chat_id, response_text, reply_markup=eddNotSysBut)
        bot.edit_message_reply_markup(chat_id, callback.message.message_id, reply_markup=None)
        if not chosen_days:
            user_choices[chat_id] = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        user_choices_dub[chat_id] = user_choices[chat_id]
        user_choices[chat_id]=[]
        
        return

    if callback.data == "ed_gameSys":
        user_game_systems[callback.message.chat.id] = []
        bot.send_message(callback.message.chat.id, 'Выбери системы, в которые хочешь играть', reply_markup=create_game_systems_keyboard())

    if callback.data.startswith("game_"):
       system = callback.data.replace("game_", "")
       if system in user_game_systems[chat_id]:
           user_game_systems[chat_id].remove(system)
       else:
           user_game_systems[chat_id].append(system)
        
       bot.edit_message_reply_markup(chat_id, callback.message.message_id, reply_markup=create_game_systems_keyboard(user_game_systems[chat_id]))
       return

    if callback.data == "done_games":
        chosen_systems = user_game_systems.get(chat_id, [])
        response_text = "Вы выбрали системы: " + ", ".join(chosen_systems) if chosen_systems else "Вы выбрали все системы."
        bot.send_message(chat_id, response_text)
        if not chosen_systems:
            chosen_systems = ["DnD 5e", "DnD 2024", "Cyberpunk RED", "FATE Core", "10 свечей", "Другие системы"]

        chosen_days = user_choices_dub.get(chat_id, [])
        save_user_choices_to_file(chat_id, chosen_days, chosen_systems)
        
        bot.edit_message_reply_markup(chat_id, callback.message.message_id, reply_markup=None)
        bot.send_message(chat_id,"Настройка уведомлений завершена")

        usersFromDB = database.loadUsers()
        info = ''
        for el in usersFromDB:
            info+=f'Id: {el.userID} Имя: {el.userFirstName} \nДни игры: {el.userGameDays} \nСистемы: {el.userSystems} \n'
        bot.send_message(chat_id, f'Зарегестрированные пользователи {info}')

        return

    if not(chat_id in adminsId) and callback.data in ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]:     
        if callback.data in user_choices[chat_id]:
            user_choices[chat_id].remove(callback.data)
        elif callback.data != 'ed_not' and callback.data != 'ed_gameSys':
            user_choices[chat_id].append(callback.data)
        if user_choices.get(chat_id, []):
            bot.edit_message_reply_markup(chat_id, callback.message.message_id, reply_markup=create_weekday_keyboard(user_choices[chat_id]))


#=======================================================================ADD_GAME_TEXT====================================================  

def gameText_handler(message):
    addPhotoBut = types.InlineKeyboardMarkup()
    addPhotoBut.add(types.InlineKeyboardButton('Добавить фото', callback_data= 'add_photo'))

    bot.send_message(message.chat.id, 'Текст сохранён', reply_markup=addPhotoBut)
    msgText = message.text

    global gamesID
    newGame = Game(gamesID, msgText, "", "", "")
    games[newGame.gameID] = newGame
    gameText = open('GameText.txt', 'w+', encoding='utf-8')
    gameText.write(msgText)
    #bot.send_message(message.chat.id, f'Your message:{msgText}')
    gameText.close()


#=======================================================================GAME_PHOTO_HANDLER====================================================

@bot.message_handler(content_types=['photo'])
def get_photo(message):
    if message.from_user.id in adminsId:
        addDateBut = types.InlineKeyboardMarkup()
        addDateBut.add(types.InlineKeyboardButton('Добавить дату', callback_data= 'add_date'))

        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'
        response = requests.get(file_url)
        file_name = f'photo_{message.chat.id}_{message.message_id}.jpg'  
        with open(file_name, 'wb') as file:
            file.write(response.content)

        global gamesID
        games[gamesID].gamePhoto = message.photo[-1].file_id
        bot.send_message(message.chat.id, f'Получил изображение', reply_markup=addDateBut)

    else:
        bot.send_message(message.chat.id, f'Извините, не понял вас')


#=======================================================================ADD_GAME_DATE====================================================

def gameDate_handler(message):
    addSysBut = types.InlineKeyboardMarkup()
    addSysBut.add(types.InlineKeyboardButton('Добавить систему игры', callback_data= 'add_system'))

    bot.send_message(message.chat.id, 'Дата сохранена', reply_markup=addSysBut)
    msgText = message.text

    global gamesID
    games[gamesID].gameDate = datetime.strptime(msgText, "%d.%m.%Y")# дд.мм.гггг

    gameD = open('GameDate.txt', 'w')
    gameD.write(msgText)
    gameD.close()


#=======================================================================ADD_GAME_PUBDATE====================================================

def gamePubDate_handler(message):
    endAddBut = types.InlineKeyboardMarkup()
    endAddBut.add(types.InlineKeyboardButton('Закончить', callback_data= 'add_end'))

    bot.send_message(message.chat.id, 'Дата сохранена', reply_markup=endAddBut)
    msgText = message.text

    global gamesID
    games[gamesID].gamePublicationDate = datetime.strptime(msgText, "%d.%m.%Y %H:%M") #дд.мм.гггг чч:мм

    database.addGame(games[gamesID])

    gamesFromBD = database.loadGames() #Убрать на релизе

    info = ''
    for el in gamesFromBD:
        #info+=f'Id: {el.gameID} \nТекст: {el.gameText} \nФото: {el.gamePhoto} \nДата игры: {el.gameDate} \nДата публицации {el.gamePublicationDate} \nСистема игры {el.gameSystem}\n'
        bot.send_photo(chat_id=message.chat.id, photo=el.gamePhoto, caption=el.gameText)#Убрать на релизе

    #bot.send_message(message.chat.id, f'Текущие игры: \n{info}')

    gamePubDate = open('gamePubDate.txt', 'w')
    gamePubDate.write(msgText)
    gamePubDate.close()


#=======================================================================CREATE_WEEKDAY_KEEBOARD====================================================

def create_weekday_keyboard(selected_days=None):
    if selected_days is None:
        selected_days = []
    
    markup = InlineKeyboardMarkup(row_width=2)
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    buttons = []
    
    for day in days:
       
        text = f"{day} {'✅' if day in selected_days else ''}"
        buttons.append(InlineKeyboardButton(text, callback_data=day))
    
    buttons.append(InlineKeyboardButton("Завершить выбор", callback_data="done"))
    
    markup.add(*buttons)
    return markup


#=======================================================================CREATE_GAME_SYSTEM_KEEBOARD====================================================

def create_game_systems_keyboard(selected_systems=None):
    if selected_systems is None:
        selected_systems = []
    
    systems = ["DnD 5e", "DnD 2024", "Cyberpunk RED", "FATE Core", "10 свечей", "Другие системы"]
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    for system in systems:
        text = f"{system} {'✅' if system in selected_systems else ''}"
        buttons.append(InlineKeyboardButton(text, callback_data=f"game_{system}"))
    
    buttons.append(InlineKeyboardButton("Завершить выбор", callback_data="done_games"))
    markup.add(*buttons)
    return markup


#=======================================================================SAVE_USER_DATA====================================================

def save_user_choices_to_file(chat_id, chosen_days, chosen_systems):
    filename = "user_choices.txt"
    users[chat_id].userGameDays = chosen_days
    users[chat_id].userSystems = chosen_systems

    if database.user_exists(users[chat_id].userID):
        database.updateUser(users[chat_id])
        print(f"User {chat_id} updated in the database.")
    else:
        database.addUser(users[chat_id])
        print(f"New user {chat_id} added to the database.")



    with open(filename, "a") as file:
        days_str = ", ".join(chosen_days)
        systems_str = ", ".join(chosen_systems) 
        file.write(f"User {chat_id} выбрал дни: {days_str}, системы: {systems_str}\n")
    print(f"Choices for user {chat_id} saved to {filename} and to data base")

    


#=======================================================================PUBLISH_GAME====================================================

def publish_game(gameID, users):
    game = games[gameID]
    if game:
       for user in users:
           bot.send_photo(chat_id=user.userID, photo=game.gamePhoto, caption=game.gameText)



#=======================================================================BOT_RUNNING====================================================

bot.polling(none_stop=True)
