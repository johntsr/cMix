from network_part import NetworkPart
from crypto_utils import CyclicGroup, ElGamalVector, CyclicGroupVector, Vector
from network_utils import Status, Callback, Message


class UsersBuffer:

    def __init__(self, b):
        self.b = b
        self.senders = []
        self.messages = []

    def addUser(self, senderId, blindMessage):
        self.senders.append(senderId)
        self.messages.append(blindMessage)

    def isFull(self):
        return len(self.senders) == self.b

    def getSenders(self):
        return self.senders

    def getBlindMessages(self):
        return Vector(vector=self.messages)

    def scalarMultiply(self, cyclicVector):
        for i in range(0, self.b):
            self.messages[i] = CyclicGroupVector.scalarMultiply(self.messages[i], cyclicVector.at(i))


class NetworkHandler (NetworkPart):

    def __init__(self, b):
        NetworkPart.__init__(self)
        self.b = b
        self.buffer = []
        self.nodesNum = 0
        self.d = 1
        self.R_inverseEG = None

        self.usersBuffer = UsersBuffer(self.b)

        self.mixResult = None
        self.decryptionShares = None

        self.associateCallback(Callback.KEY_SHARE, self.appendKeyShare)
        self.associateCallback(Callback.PRE_FOR_PREPROCESS, self.preForPreProcess)
        self.associateCallback(Callback.USER_MESSAGE, self.getUserMessage)
        self.associateCallback(Callback.REAL_FOR_PREPROCESS, self.realForPreProcess)
        self.associateCallback(Callback.REAL_FOR_POSTPROCESS, self.realForPostProcess)

    def includeNode(self):
        self.nodesNum += 1
        self.timesMax[Callback.KEY_SHARE] = self.nodesNum
        self.timesMax[Callback.PRE_FOR_PREPROCESS] = self.nodesNum
        self.timesMax[Callback.REAL_FOR_PREPROCESS] = self.nodesNum
        self.timesMax[Callback.REAL_FOR_POSTPROCESS] = self.nodesNum

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
        self.usersBuffer.addUser(senderId, blindMessage)
        if self.usersBuffer.isFull():
            self.network.broadcastToNodes(self.id, Message(Callback.REAL_FOR_PREPROCESS, self.usersBuffer.getSenders()))
        return Status.OK

    def realForPreProcess(self, message):
        code = message.callback
        cyclicVector = message.payload
        self.usersBuffer.scalarMultiply(cyclicVector)
        if self.isLastCall(code):
            self.network.sendToFirstNode(Message(Callback.REAL_FOR_MIX, self.usersBuffer.getBlindMessages()))
        return Status.OK

    def __appendDecrShare(self, payload):
        if self.decryptionShares is None:
            self.decryptionShares = payload
        else:
            if self.mixResult is None:
                self.decryptionShares = CyclicGroup.multiply(self.decryptionShares, payload)
            else:
                self.decryptionShares = payload

    def realForPostProcess(self, message):
        code = message.callback
        isLastNode = message.payload[0]
        payload = message.payload[1]

        if isLastNode:
            self.mixResult = payload
        else:
            self.__appendDecrShare(payload)

        if self.mixResult is not None and self.decryptionShares is not None:
            self.mixResult = Vector(
                [CyclicGroupVector.scalarMultiply(self.mixResult.at(i), self.decryptionShares.at(i)) for i in
                 range(0, self.mixResult.size())])

        if self.isLastCall(code):
            for i in range(0, self.mixResult.size()):
                userId = self.mixResult.at(i).pop()
                self.network.sendToUser(userId, Message(Callback.USER_MESSAGE, self.mixResult.at(i)))
        return Status.OK
