from key_manager import KeyManager
from crypto_utils import CyclicGroupVector
from network_part import NetworkPart
from network_utils import Status, Callback, Message


class BasicHandler:

    @staticmethod
    def setUp(user):
        pass

    @staticmethod
    def messageHandler(self, message):
        return CyclicGroupVector.random()

    @staticmethod
    def responseHandler(self, reponse):
        pass

    @staticmethod
    def messageStatusHandler(user, messageId, status):
        pass


# class that represents a user in the system
class User (NetworkPart):

    """
    The class consists of:
    - the key manager, whose keys are used to blind and un-blind messages/responses
    - the response handler, that reads a message and produces a response
    - the LAST message and response the user sent and received (or received and sent)
    """

    def __init__(self, name, handler=None):
        NetworkPart.__init__(self)

        self.name = name
        self.messageSent = None
        self.messageGot = None

        self.responseSent = None
        self.responseGot = None

        self.keyManager = KeyManager()

        if handler is None:
            self.setCallbackHandler(BasicHandler)
        else:
            self.setCallbackHandler(handler)

        self.associateCallback(Callback.KEY_USER, self.storeKeyUser)
        self.associateCallback(Callback.USER_MESSAGE, self.readMessage)
        self.associateCallback(Callback.USER_MESSAGE_STATUS, self.messageStatus)
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
        self.callbackHandler.setUp(self)
        return Status.OK

    def setCallbackHandler(self, callbackHandler):
        self.callbackHandler = callbackHandler

    # send a message to a user through the mixnet
    def sendMessage(self, userId, messageId, messageVector):
        # store the message for future reference
        self.messageSent = messageVector.copyVector()

        # append the userId (the receiver)
        # the NH will read this id (after the message is un-blinded) and route the message accordingly
        messageVector.append(userId)

        # blind the message with the combined key and send it to the NH
        combinedKey = self.keyManager.getCombinedKey(type=KeyManager.MESSAGE, inverse=True)
        blindMessage = CyclicGroupVector.scalarMultiply(messageVector, combinedKey)
        self.network.sendToNH(Message(Callback.USER_MESSAGE, [self.id, messageId, blindMessage.vector]))

    # read a message from the mixnet and send a response
    def readMessage(self, message):
        index = message.payload[0]

        # the payload is the message (mapped to cyclic group members)
        messageVector = CyclicGroupVector(vector=message.payload[1])

        # compute a response and send it to the mixnet
        responseVector = self.callbackHandler.messageHandler(self, messageVector)
        # store message and response for future reference
        self.messageGot = messageVector.copyVector()
        self.responseSent = responseVector.copyVector()

        self.network.sendToNH(Message(Callback.USER_RESPONSE, [index, responseVector.vector]))
        return Status.OK

    # read a response (after I sent a message)
    def readResponse(self, message):
        # un-blind the response and store it for future reference
        responseVector = CyclicGroupVector.scalarMultiply(CyclicGroupVector(vector=message.payload),
                                                          self.keyManager.getCombinedKey(type=KeyManager.RESPONSE,
                                                                                         inverse=True))
        self.callbackHandler.responseHandler(self, responseVector)
        self.responseGot = responseVector.copyVector()
        return Status.OK

    def messageStatus(self, message):
        messageId = message.payload[0]
        status = message.payload[1]
        self.callbackHandler.messageStatusHandler(self, messageId, status)
        return Status.OK
