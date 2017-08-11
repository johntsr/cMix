import string

import user_management
from demo_utils import createDir, uniqueid, listFiles, moveFile, dateStr, createFile
from network.crypto_utils import CyclicGroup, CyclicGroupVector
from network.network_utils import MessageStatus


usersDir = "./demo/users/"


# class that facilitates the conversion from ascii codes to cyclic group members and backwards
class AsciiConverter:

    asciiMap = {}                       # from ascii to cyclic group
    cyclicMap = {}                      # from cyclic group to ascii

    for char in string.printable:
        id = CyclicGroup.getUniqueId()
        asciiMap[char] = id
        cyclicMap[id] = char

    # given a string, convert it to the appropriate cyclic group vector
    # (matches every character of the string to a cyclic group member)
    @staticmethod
    def convert2cyclic(message):
        return CyclicGroupVector(vector=[AsciiConverter.asciiMap[c] for c in message])

    # given a cyclic group vector, convert it to the appropriate string
    # (matches every element of the vector to a character)
    @staticmethod
    def convert2string(cyclicVector):
        return ''.join([AsciiConverter.cyclicMap[cyclicVector.at(i)] for i in range(0, cyclicVector.size())])


# class that facilitates the management of a user's messages
class UserManager:

    INBOX = "inbox"
    OUTBOX = "outbox"
    outboxStatus = {MessageStatus.NEW: "new", MessageStatus.PENDING: "pending", MessageStatus.SENT: "sent"}

    def __init__(self, username):
        self.username = username
        self.messageFiles = {}      # the files containing the user messages (may be new, pending or sent)

    def userDir(self):
        return usersDir + self.username + "/"

    def inbox(self):
        return self.userDir() + UserManager.INBOX + "/"

    def outbox(self):
        return self.userDir() + UserManager.OUTBOX + "/"

    def outboxDir(self, status):
        return self.outbox() + UserManager.outboxStatus[status] + "/"

    def createDirectories(self):
        createDir(self.userDir())
        createDir(self.inbox())
        createDir(self.outbox())
        createDir(self.outboxDir(MessageStatus.NEW))
        createDir(self.outboxDir(MessageStatus.PENDING))
        createDir(self.outboxDir(MessageStatus.SENT))

    # list all the files in the "new" directory
    # the "uniqueid" is needed when the message is sent to the Network Handler
    def listFiles(self):
        self.messageFiles.update({uniqueid(): {"name": fileName, "status": MessageStatus.NEW} for fileName in
                             listFiles(self.outboxDir(MessageStatus.NEW))})

    # update the status of a message in the dictionary
    # also, move the file to the appropriate directory
    def updateFileStatus(self, fileId, status):
        fileInfo = self.messageFiles[fileId]
        fileInfo["status"] = status
        fileName = fileInfo["name"]
        if status == MessageStatus.PENDING:
            moveFile(self.outboxDir(MessageStatus.NEW) + fileName, self.outboxDir(MessageStatus.PENDING) + fileName)
        elif status == MessageStatus.SENT:
            moveFile(self.outboxDir(MessageStatus.PENDING) + fileName, self.outboxDir(MessageStatus.SENT) + fileName)

    # return the file contents of the files in the dictionary with the given status
    def listFileContents(self, status):
        messageDir = self.outboxDir(status)
        fileContents = []
        for fileId, messageFile in self.messageFiles.iteritems():
            if messageFile["status"] != status:
                continue
            with open(messageDir + messageFile["name"]) as file:
                content = file.readlines()
                receivername, message = content[0].strip(), ''.join(content[1:])
                fileContents.append((receivername, message, fileId))
        return fileContents

    # first, distinguish the sender name from the actual contents based on the message format expected
    # store the message, i.e. create a new file in the "inbox" folder
    def storeMessage(self, message):
        sender, content = message.partition("\n")[0], message.partition("\n")[2]
        fileName = self.inbox() + sender + "_" + dateStr() + ".txt"
        createFile(fileName, "Sender: " + sender + "\nContent: " + content)


# class that contains callbacks of a "User" entity
class CallbackHandler:

    # callback called once in the set up phase (after the key exchange)
    # create the directories of the user in the file system
    @staticmethod
    def setUp(user):
        UserManager(user.name).createDirectories()

    # callback called every time a message arrives
    # store the message and return a response, a simple "OK" is enough
    @staticmethod
    def messageHandler(user, cyclicVector):
        manager = user_management.getManager(user.name)
        message = AsciiConverter.convert2string(cyclicVector)
        manager.storeMessage(message)
        return AsciiConverter.convert2cyclic("OK")

    @staticmethod
    def responseHandler(user, response):
        pass

    # callback called every time a message status changes
    # propagate this change to the user manager object
    @staticmethod
    def messageStatusHandler(user, messageId, status):
        user_management.getManager(user.name).updateFileStatus(messageId, status)
