from crypto_utils import CyclicGroupVector
from network_part import NetworkPart
from key_manager import KeyManager
from network_utils import Status, Callback, Message


class User (NetworkPart):

    def __init__(self):
        NetworkPart.__init__(self)

        self.keyManager = KeyManager()

        self.associateCallback(Callback.KEY_USER, self.storeKeyUser)
        self.associateCallback(Callback.USER_RESPONSE, self.readResponse)

    def setUp(self):
        print "Let's set up"
        self.network.broadcastToNodes(self.id, Message(Callback.KEY_USER, self.id))

    def storeKeyUser(self, message):
        nodeId = message.payload[0]
        messageKey = message.payload[1]
        responseKey = message.payload[2]
        print "Got: ", message.payload
        self.keyManager.addSeeds(nodeId, (messageKey, responseKey))
        return Status.OK

    def sendMessage(self, userId, messageVector):
        combinedKey = self.keyManager.getCombinedKey(type=KeyManager.MESSAGE, inverse=True)
        messageVector.append(userId)
        blindMessage = CyclicGroupVector.scalarMultiply(messageVector, combinedKey)
        payload = self.id, blindMessage
        self.network.sendToNH(Message(Callback.USER_MESSAGE, payload))

    def readResponse(self, message):
        return Status.OK
