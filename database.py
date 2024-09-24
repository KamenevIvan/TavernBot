import sqlite3
from datetime import datetime
from models import User, Game

def startBD():
    conn = sqlite3.connect('telegramVKbotBD.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE  IF NOT EXISTS users (id int auto_increment primary key, userID int, userFirstName varchar(50), userGameDays varchar(100), userSystems varchar(100))')

    conn.commit()

    cur.execute('CREATE TABLE  IF NOT EXISTS games (id int auto_increment primary key, gameID int, gameText varchar(500), gamePhoto varchar(100), gameDate varchar(50), gamePublicationDate varchar(50), gameSystem varchar(50))')

    conn.commit()
    cur.close()
    conn.close()


def addUser(user):
    conn = sqlite3.connect('telegramVKbotBD.sql')
    cur = conn.cursor()

    userDaysStr = ','.join(user.userGameDays)
    userSystems = ','.join(user.userSystems)

    cur.execute("INSERT INTO users (userID, userFirstName, userGameDays, userSystems) VALUES ('%d', '%s', '%s', '%s')" % (user.userID, user.userFirstName, userDaysStr, userSystems))

    conn.commit()
    cur.close()
    conn.close()

def loadUsers():
    conn = sqlite3.connect('telegramVKbotBD.sql')
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")

    usersRaw = cur.fetchall()

    users = []

    for userEl in usersRaw:
        users.append(User(userEl[1], userEl[2], None, userEl[3], userEl[4]))

    cur.close()
    conn.close()

    return users

def delUser(user):
    conn = sqlite3.connect('telegramVKbotBD.sql')
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE userID='%s';" % (user.userID))
    conn.commit()

    cur.close()
    conn.close()

def updateUser(user):
    conn = sqlite3.connect('telegramVKbotBD.sql')
    cur = conn.cursor()

    userDaysStr = ''.join(user.userGameDays)
    userSystems = ''.join(user.userSystems)

    cur.execute("""
        UPDATE users
        SET userFirstName = ?, userGameDays = ?, userSystems = ?
        WHERE userID = ?
    """, (user.userFirstName, userDaysStr, userSystems, user.userID))

    conn.commit()
    cur.close()
    conn.close()

def user_exists(userID):
    conn = sqlite3.connect('telegramVKbotBD.sql')
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM users WHERE userID = ?", (userID,))
    result = cur.fetchone()

    cur.close()
    conn.close()

    return result is not None




def addGame(game):
    conn = sqlite3.connect('telegramVKbotBD.sql')
    cur = conn.cursor()

    gameDateStr = game.gameDate.strftime('%Y-%m-%d')
    gamePubDateStr = game.gamePublicationDate.strftime('%Y-%m-%d %H:%M:%S')

    cur.execute("INSERT INTO games (gameID, gameText, gamePhoto, gameDate, gamePublicationDate, gameSystem) VALUES ('%d', '%s', '%s', '%s', '%s', '%s')" % (game.gameID, game.gameText, game.gamePhoto, gameDateStr, gamePubDateStr, game.gameSystem))

    conn.commit()
    cur.close()
    conn.close()

   
def loadGames():
    conn = sqlite3.connect('telegramVKbotBD.sql')
    cur = conn.cursor()

    cur.execute("SELECT * FROM games")

    gamesRaw = cur.fetchall()

    games = []

    for gameEl in gamesRaw:
        games.append(Game(gameEl[1], gameEl[2], gameEl[3], gameEl[4], gameEl[5], gameEl[6]))

    cur.close()
    conn.close()

    return games