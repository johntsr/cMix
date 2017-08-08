from crypto_utils import CyclicGroupVector, CyclicGroup
from network_part import NetworkPart
from key_manager import KeyManager
from network_utils import Status, Callback, Message


def randomResponse(message):
    return CyclicGroupVector.random()


# class that represents a user in the system
class User (NetworkPart):

    """
    The class consists of:
    - the key manager, whose keys are used to blind and un-blind messages/responses
    - the response handler, that reads a message and produces a response
    - the LAST message and response the user sent and received (or received and sent)
    """

    def __init__(self):
        NetworkPart.__init__(self)

        self.messageSent = None
        self.messageGot = None

        self.responseSent = None
        self.responseGot = None

        self.keyManager = KeyManager()

        self.responseHandler = randomResponse

        self.associateCallback(Callback.KEY_USER, self.storeKeyUser)
        self.associateCallback(Callback.USER_MESSAGE, self.readMessage)
        self.associateCallback(Callback.USER_RESPONSE, self.readResponse)

    # the key establishment takes place here
    def setUp(self):
        self.network.broadcastToNodes(self.id, Message(Callback.KEY_USER, self.id))

    # store the keys that a node sent
    def storeKeyUser(self, message):
        nodeId = message.payload[0]
        messageKey = message.payload[1]
        responseKey = message.payload[2]
        self.keyManager.addSeeds(nodeId, (messageKey, responseKey))
        return Status.OK

    def setResponseHandler(self, responseGen):
        self.responseHandler = responseGen

    # send a message to a user through the mixnet
    def sendMessage(self, userId, messageVector):
        # store the message for future reference
        self.messageSent = messageVector.copyVector()

        # append the userId (the receiver)
        # the NH will read this id (after the message is un-blinded) and route the message accordingly
        messageVector.append(userId)

        # blind the message with the combined key and send it to the NH
        combinedKey = self.keyManager.getCombinedKey(type=KeyManager.MESSAGE, inverse=True)
        blindMessage = CyclicGroupVector.scalarMultiply(messageVector, combinedKey)
        self.network.sendToNH(Message(Callback.USER_MESSAGE, [self.id, blindMessage.vector]))

    # read a message from the mixnet and send a response
    def readMessage(self, message):
        # the payload is the message (mapped to cyclic group members)
        messageVector = CyclicGroupVector(vector=message.payload)

        # compute a response and send it to the mixnet
        responseVector = self.responseHandler(messageVector)
        self.network.sendToNH(Message(Callback.USER_RESPONSE, [self.id, responseVector.vector]))

        # store message and response for future reference
        self.messageGot = messageVector.copyVector()
        self.responseSent = responseVector.copyVector()

        return Status.OK

    # read a response (after I sent a message)
    def readResponse(self, message):
        # un-blind the response and store it for future reference
        responseVector = CyclicGroupVector.scalarMultiply(CyclicGroupVector(vector=message.payload), self.keyManager.getCombinedKey(type=KeyManager.RESPONSE, inverse=True))
        self.responseGot = responseVector.copyVector()
        return Status.OK
