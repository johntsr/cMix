from crypto_utils import CyclicGroupVector, CyclicGroup
from network_part import NetworkPart
from key_manager import KeyManager
from network_utils import Status, Callback, Message


class User (NetworkPart):

    def __init__(self):
        NetworkPart.__init__(self)

        self.keyManager = KeyManager()

        self.associateCallback(Callback.KEY_USER, self.storeKeyUser)
        self.associateCallback(Callback.USER_MESSAGE, self.readMessage)
        self.associateCallback(Callback.USER_RESPONSE, self.readResponse)

    def setUp(self):
        self.network.broadcastToNodes(self.id, Message(Callback.KEY_USER, self.id))

    def storeKeyUser(self, message):
        nodeId = message.payload[0]
        messageKey = message.payload[1]
        responseKey = message.payload[2]
        self.keyManager.addSeeds(nodeId, (messageKey, responseKey))
        return Status.OK

    def sendMessage(self, userId, messageVector):
        combinedKey = self.keyManager.getCombinedKey(type=KeyManager.MESSAGE, inverse=True)
        messageVector.append(self.id)
        messageVector.append(userId)
        print "Will send message: "
        print messageVector.vector
        blindMessage = CyclicGroupVector.scalarMultiply(messageVector, combinedKey)
        payload = self.id, blindMessage
        self.network.sendToNH(Message(Callback.USER_MESSAGE, payload))

    def readMessage(self, message):

        responseVector = message.payload
        senderId = responseVector.pop()
        print "\n\nUser "
        print self.id
        print "Got Message:"
        print responseVector.vector
        print "From user:"
        print senderId

        blindResponse = CyclicGroupVector(vector=[CyclicGroup.random()])
        print "Will respond: "
        print blindResponse.vector
        payload = self.id, blindResponse
        self.network.sendToNH(Message(Callback.USER_RESPONSE, payload))

        return Status.OK

    def readResponse(self, message):

        responseVector = CyclicGroupVector.scalarMultiply(message.payload, self.keyManager.getCombinedKey(type=KeyManager.RESPONSE, inverse=True))
        print "\n\nUser "
        print self.id
        print "Got Response:"
        print responseVector.vector

        return Status.OK
