# coding=utf-8
import fileinput
import json

import user_management
from demo_utils import createFile, uniqueid, randomString
from network.user import User
from user_utils import AsciiConverter, CallbackHandler
from network.mix_node import MixNode
from network.network import Network
from network.network_handler import NetworkHandler
from network.network_utils import MessageStatus

networkConfigFile = "./demo/network.json"
b = None
network = Network()

"""
 This app demonstrates the use of the cMix implementation, providing a way to send messages through the mixnet.
 The messages are loaded from and stored to the local file system.
 More specifically, a user's directory structure (let's say Bob's) is shown below:
 Bob
  ├── inbox
  └── outbox
         ├── new
         ├── pending
         └── sent
  Explanation of the directories:
  1) "inbox": the directory where incoming messages are stored
  2) "outbox/new": Bob stores the messages he wants to send here
  3) "outbox/pending": after the app load the Bob's messages, it stores them here until they are finally sent
                        in essence, messages in this directory wait for the mixnet buffer to fill
  4) "outbox/sent": the messages that Bob successfully sent through the mixnet
  
  A user of the app can:
  a) load messages from the file system. This command tries to send through the mixnet every message it discovers.
     If messages are stuck (waiting for the buffer to fill), the user has the option to fill the buffer with "garbage"
     messages. Otherwise, those messages will be sent with the next "load" command.
  b) create new users of the mixnet. This command involves the key exchange mechanism and the creation of the directory
     structure.
  c) exit the app with "Ctrl+D"
"""


# performs the precomputation phase, registers users
def setUpNetwork():

    with open(networkConfigFile) as configFile:
        networkConfig = json.load(configFile)

    # first, read the network configuration from the json file
    global b
    b = networkConfig['globals']['b']
    numOfNodes = networkConfig['globals']['nodes']
    numOfBots = networkConfig['globals']['bots']

    # then, construct the network and perform the precomputation phase
    network.setNetworkHandler(NetworkHandler(b))
    for _ in range(0, numOfNodes):
        network.addMixNode(MixNode(b))
    network.init()

    # finally, register users to the system
    # for convenience, the json file contains messages that are stored to files with "NEW" status
    # those files can be later loaded and sent from the mixnet
    user_management.init()
    for userInfo in networkConfig['users']:
        user = addUser(userInfo['name'])
        manager = user_management.getManager(user.name)
        for index, message in enumerate(networkConfig['messages'][user.name]):
            createFile(manager.outboxDir(MessageStatus.NEW) + "message_" + str(index) + ".txt",
                       message['to'] + "\n" + message['content'])

    # finally, insert "bot" users to the system
    # i.e. fake users used to send garbage then real messages are "stuck"
    for i in range(0, numOfBots):
        addBot()
    return network


def addBot():
    botname = user_management.addBot()
    network.addUser(User(botname))


def addUser(username):
    if not user_management.user_exists(username):
        user_management.addUser(username)
        user = User(username, CallbackHandler())
        network.addUser(user)
        return user


# send the new messages of all users
# first, call the user's manager to list all the new files
# then, read those files and send their contents to the mixnet
def sendMessages():
    for username in user_management.usernames():
        manager = user_management.getManager(username)
        manager.listFiles()
        for receivername, message, messageId in manager.listFileContents(MessageStatus.NEW):
            network.user(username).sendMessage(network.username2id(receivername), messageId,
                                               AsciiConverter.convert2cyclic(username + "\n" + message))


# send the appropriate number of garbage in order to trigger the mixing process
def sendGarbagge(pendingNum):
    garbaggeNum = b - pendingNum
    for i in range(0, garbaggeNum):
        botSender, botReceiver = user_management.getBotname(), user_management.getBotname()
        network.user(botSender).sendMessage(network.username2id(botReceiver), uniqueid(),
                                            AsciiConverter.convert2cyclic(randomString()))


def mainEventLoop():
    print "Available options (optional):"
    print "1) Load messages: load"
    print "1) Add user(s): add [usernames]"
    print "3) Exit: Ctrl+D"
    for line in fileinput.input():
        words = line.split()
        command = words[0]
        if command == "load":
            sendMessages()
            pendingNum = user_management.pendingNum()
            if pendingNum > 0:
                print "Some messages are stuck, fill with garbage? (yes/no)"
                if raw_input() == "yes":
                    sendGarbagge(pendingNum)
                    print "Delivered messages."
                else:
                    print "Some messages are not delivered."
            else:
                print "Delivered messages."
        elif command == "add":
            for username in words[1:]:
                if addUser(username) is not None:
                    print "User added: ", username
                else:
                    print "User", username, "already exists."
        else:
            print "Unknown command inserted."

if __name__ == "__main__":
    setUpNetwork()
    mainEventLoop()
