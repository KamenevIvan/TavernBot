from datetime import datetime


class User:

    def __init__(self, userID, userFirstName, userSecondName, userGameDays, userSystems):
        self.userID = userID
        self.userFirstName = userFirstName
        self.userSecondName = userSecondName
        self.userGameDays = userGameDays
        self.userSystems = userSystems


class Game:

    def __init__(self, gameID, gameText = None, gamePhoto = None, gameDate = None, gamePublicationDate = None, gameSystem = None):
        self.gameID = gameID    
        self.gameText = gameText    
        self.gamePhoto = gamePhoto    
        self.gameDate = gameDate    
        self.gamePublicationDate = gamePublicationDate    
        self.gameSystem = gameSystem

    def load_games():
        pass
