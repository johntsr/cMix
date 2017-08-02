from network_part import NetworkPart
from crypto_utils import CyclicGroup, ElGamalVector, CyclicGroupVector, Vector
from network_utils import Status, Callback, Message


class UsersBuffer:

    def __init__(self, b):
        self.b = b
        self.users = []
        self.messages = []

    def copyUsers(self, users):
        self.users = list(users)
        self.messages = [None] * (len(self.users))

    def addUser(self, userId, blindMessage):
        if not self.isFull():
            self.users.append(userId)
            self.messages.append(blindMessage)

    def addUserMessage(self, userId, blindMessage):
        for i in range(0, len(self.users)):
            if self.users[i] == userId:
                self.messages[i] = blindMessage

    def isFull(self):
        return len([message for message in self.messages if message is not None]) == self.b

    def getUsers(self):
        return self.users

    def getBlindMessages(self):
        return Vector(vector=self.messages)

    def scalarMultiply(self, cyclicVector):
        for i in range(0, self.b):
            self.messages[i] = CyclicGroupVector.scalarMultiply(self.messages[i], cyclicVector.at(i))


class NetworkHandler (NetworkPart):

    def __init__(self, b):
        NetworkPart.__init__(self)
        self.b = b
        self.nodesNum = 0
        self.d = 1
        self.R_inverseEG = None

        self.sendersBuffer = UsersBuffer(self.b)
        self.receiversBuffer = UsersBuffer(self.b)

        self.mixResult = {'FOR': None, 'RET': None}
        self.sendCallback = {'FOR': Callback.USER_MESSAGE, 'RET': Callback.USER_RESPONSE}
        self.decryptionShares = {'FOR': None, 'RET': None}

        self.associateCallback(Callback.KEY_SHARE, self.appendKeyShare)
        self.associateCallback(Callback.PRE_FOR_PREPROCESS, self.preForPreProcess)
        self.associateCallback(Callback.USER_MESSAGE, self.getUserMessage)
        self.associateCallback(Callback.REAL_FOR_PREPROCESS, self.realForPreProcess)
        self.associateCallback(Callback.REAL_FOR_POSTPROCESS, self.realForPostProcess)
        self.associateCallback(Callback.USER_RESPONSE, self.getUserResponse)
        self.associateCallback(Callback.REAL_RET_POSTPROCESS, self.realRetPostProcess)

    def includeNode(self):
        self.nodesNum += 1
        self.timesMax[Callback.KEY_SHARE] = self.nodesNum
        self.timesMax[Callback.PRE_FOR_PREPROCESS] = self.nodesNum
        self.timesMax[Callback.REAL_FOR_PREPROCESS] = self.nodesNum
        self.timesMax[Callback.REAL_FOR_POSTPROCESS] = self.nodesNum
        self.timesMax[Callback.REAL_RET_POSTPROCESS] = self.nodesNum

    def reset(self):
        self.timesCalled[Callback.REAL_FOR_PREPROCESS] = 0
        self.timesCalled[Callback.REAL_FOR_POSTPROCESS] = 0
        self.timesCalled[Callback.REAL_RET_POSTPROCESS] = 0

        self.sendersBuffer = UsersBuffer(self.b)
        self.receiversBuffer = UsersBuffer(self.b)

        self.mixResult = {'FOR': None, 'RET': None}
        self.decryptionShares = {'FOR': None, 'RET': None}

    def appendKeyShare(self, message):
        share = message.payload
        code = message.callback
        self.d = CyclicGroup.multiply(self.d, share)
        if self.isLastCall(code):
            self.broadcast(Message(Callback.KEY_SHARE, self.d))

        return Status.OK

    def preForPreProcess(self, message):
        r_inverseEG = message.payload
        code = message.callback

        if not self.R_inverseEG:
            self.R_inverseEG = r_inverseEG
        else:
            self.R_inverseEG = ElGamalVector.multiply(self.R_inverseEG, r_inverseEG)
            if self.isLastCall(code):
                self.network.sendToFirstNode(Message(Callback.PRE_FOR_MIX, self.R_inverseEG))
        return Status.OK

    def getUserMessage(self, message):
        senderId = message.payload[0]
        blindMessage = message.payload[1]
        self.sendersBuffer.addUser(senderId, blindMessage)
        if self.sendersBuffer.isFull():
            self.network.broadcastToNodes(self.id, Message(Callback.REAL_FOR_PREPROCESS, self.sendersBuffer.getUsers()))
        return Status.OK

    def realForPreProcess(self, message):
        code = message.callback
        cyclicVector = message.payload
        self.sendersBuffer.scalarMultiply(cyclicVector)
        if self.isLastCall(code):
            self.network.sendToFirstNode(Message(Callback.REAL_FOR_MIX, self.sendersBuffer.getBlindMessages()))
        return Status.OK

    def realForPostProcess(self, message):
        def getUsers():
            users = [self.mixResult['FOR'].at(i).pop() for i in range(0, self.b)]
            self.receiversBuffer.copyUsers(users)
            return users

        def cleanUp():
            pass

        return self.__realPostProcess(message=message, path='FOR', getUsersCallback=getUsers, cleanUp=cleanUp)

    def realRetPostProcess(self, message):
        def getUsers():
            return self.sendersBuffer.getUsers()

        def cleanUp():
            self.reset()

        return self.__realPostProcess(message=message, path='RET', getUsersCallback=getUsers, cleanUp=cleanUp)

    def __appendDecrShare(self, payload, path):
        if self.decryptionShares[path] is None:
            self.decryptionShares[path] = payload
        else:
            if self.mixResult[path] is None:
                self.decryptionShares[path] = CyclicGroupVector.multiply(self.decryptionShares[path], payload)
            else:
                self.decryptionShares[path] = payload

    def __realPostProcess(self, message, path, getUsersCallback, cleanUp):
        code = message.callback
        isLastNode = message.payload[0]
        payload = message.payload[1]

        if isLastNode:
            self.mixResult[path] = payload
        else:
            self.__appendDecrShare(payload, path)

        if self.mixResult[path] is not None and self.decryptionShares[path] is not None:
            self.mixResult[path] = Vector(
                [CyclicGroupVector.scalarMultiply(self.mixResult[path].at(i), self.decryptionShares[path].at(i)) for i in
                 range(0, self.b)])

        if self.isLastCall(code):
            users = getUsersCallback()
            for i in range(0, self.b):
                self.network.sendToUser(users[i], Message(self.sendCallback[path], self.mixResult[path].at(i)))
            cleanUp()
        return Status.OK

    def getUserResponse(self, message):
        receiverId = message.payload[0]
        blindMessage = message.payload[1]
        self.receiversBuffer.addUserMessage(receiverId, blindMessage)
        if self.receiversBuffer.isFull():
            self.network.sendToLastNode(Message(Callback.REAL_RET_MIX, self.receiversBuffer.getBlindMessages()))
        return Status.OK

