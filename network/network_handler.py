from network_part import NetworkPart
from crypto_utils import CyclicGroup, ElGamalVector, CyclicGroupVector
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
        return self.messages

    def scalarMultiply(self, cyclicVector):
        for i in range(0, self.b):
            self.messages[i] = CyclicGroupVector.scalarMultiply(self.messages[i], cyclicVector[i])

class NetworkHandler (NetworkPart):

    def __init__(self, b):
        NetworkPart.__init__(self)
        self.b = b
        self.buffer = []
        self.nodesNum = 0
        self.d = 1
        self.R_inverseEG = None

        self.usersBuffer = UsersBuffer(self.b)

        self.associateCallback(Callback.KEY_SHARE, self.appendKeyShare)
        self.associateCallback(Callback.PRE_FOR_PREPROCESS, self.preForPreProcess)
        self.associateCallback(Callback.USER_MESSAGE, self.getUserMessage)
        self.associateCallback(Callback.REAL_FOR_PREPROCESS, self.realForPreProcess, self.b)

    def includeNode(self):
        self.nodesNum += 1
        self.timesMax[Callback.KEY_SHARE] = self.nodesNum
        self.timesMax[Callback.PRE_FOR_PREPROCESS] = self.nodesNum

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
