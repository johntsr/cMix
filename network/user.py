from crypto_utils import CyclicGroupVector, CyclicGroup
from network_part import NetworkPart
from key_manager import KeyManager
from network_utils import Status, Callback, Message


def randomResponse(message):
    return CyclicGroupVector.random()


class User (NetworkPart):

    def __init__(self):
        NetworkPart.__init__(self)

        self.messageSent = None
        self.messageGot = None

        self.responseSent = None
        self.responseGot = None

        self.keyManager = KeyManager()

        self.responseGenerator = randomResponse

        self.associateCallback(Callback.KEY_USER, self.storeKeyUser)
        self.associateCallback(Callback.USER_MESSAGE, self.readMessage)
        self.associateCallback(Callback.USER_RESPONSE, self.readResponse)

    def setUp(self):
        self.network.broadcastToNodes(self.id, Message(Callback.KEY_USER, self.id))

    def setResponseGenerator(self, responseGen):
        self.responseGenerator = responseGen

    def storeKeyUser(self, message):
        nodeId = message.payload[0]
        messageKey = message.payload[1]
        responseKey = message.payload[2]
        self.keyManager.addSeeds(nodeId, (messageKey, responseKey))
        return Status.OK

    def sendMessage(self, userId, messageVector):
        self.messageSent = messageVector.copyVector()

        combinedKey = self.keyManager.getCombinedKey(type=KeyManager.MESSAGE, inverse=True)
        messageVector.append(self.id)
        messageVector.append(userId)
        # print "Will send message: "
        # print messageVector.vector
        blindMessage = CyclicGroupVector.scalarMultiply(messageVector, combinedKey)
        payload = self.id, blindMessage
        self.network.sendToNH(Message(Callback.USER_MESSAGE, payload))


    def readMessage(self, message):

        messageVector = message.payload
        senderId = messageVector.pop()
        responseVector = self.responseGenerator(messageVector)

        # print "\n\nUser "
        # print self.id
        # print "Got Message:"
        # print messageVector.vector
        # print "From user:"
        # print senderId
        # print "Will respond: "
        # print responseVector.vector

        payload = self.id, responseVector
        self.network.sendToNH(Message(Callback.USER_RESPONSE, payload))

        self.messageGot = messageVector.copyVector()
        self.responseSent = responseVector.copyVector()

        return Status.OK

    def readResponse(self, message):
        responseVector = CyclicGroupVector.scalarMultiply(message.payload, self.keyManager.getCombinedKey(type=KeyManager.RESPONSE, inverse=True))
        self.responseGot = responseVector.copyVector()
        return Status.OK
