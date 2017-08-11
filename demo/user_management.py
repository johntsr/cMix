import random
from demo_utils import listDirectories, createDir
from network.network_utils import MessageStatus
from user_utils import usersDir, UserManager

managers = {}       # dictionary of users and user manager objects
botNames = []       # list of names of all bot users


# create the users directory
def init():
    createDir(usersDir)


# check if a username is already registered
def user_exists(username):
    return username in usernames()


# add a new user to the system
def addUser(username):
    managers[username] = UserManager(username)


# add a bot to the system
# return its name in order to add a "User" entity to the network
def addBot():
    botname = "__bot__" + str(len(botNames))
    botNames.append(botname)
    return botname


# get the manager of a user
def getManager(username):
    return managers[username]


# get a random bot name
def getBotname():
    return random.choice(botNames)


# get all the usernamesin the system
def usernames():
    return [name for name in managers]


# return the number of messages that are pending
# i.e. they are "stuck", waiting the batch to fill and trigger their mixing process
def pendingNum():
    usernames = [username for username in listDirectories(usersDir)]
    pendingList = [pendingList for username in usernames for pendingList in
                    managers[username].listFileContents(MessageStatus.PENDING)]
    return len(pendingList)
