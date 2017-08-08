from network_part import NetworkPart
from crypto_utils import CyclicGroup, ElGamalVector, CyclicGroupVector, Vector
from network_utils import Status, Callback, Message


# class that facilitates the management of the user messages buffer (batch of user messages)
class UsersBuffer:

    """
    The class consists of:
    - the size of the buffer (b)
    - the IDs of the users that send a message
    - the messages that the above users send (in the matching index)
    """

    def __init__(self, b):
        self.b = b
        self.users = []
        self.messages = []

    # NOTE: this method is called only during the delivery of responses in the mixnet
    # it is needed to preserve the final order of the messages of the "messages" buffer to the "responses" buffer
    # in order to reverse-permute the responses and deliver them accordingly
    def copyUsers(self, users):
        self.users = list(users)
        self.messages = [None] * (len(self.users))

    # NOTE: this method is called only during the delivery of responses in the mixnet
    # the correct order is preserved, now the responses are gathered one by one and stored to the according index
    def addUser(self, userId, blindMessage):
        if not self.isFull():
            self.users.append(userId)
            self.messages.append(blindMessage)

    # add a user message to the buffer
    def addUserMessage(self, userId, blindMessage):
        for i in range(0, len(self.users)):
            if self.users[i] == userId:
                self.messages[i] = blindMessage

    # full if "b" non-None messages are gathered
    def isFull(self):
        return len([message for message in self.messages if message is not None]) == self.b

    def getUsers(self):
        return self.users

    def getBlindMessages(self):
        return [v.vector for v in self.messages]

    # multiply with a mix node share (un-blind partly)
    def scalarMultiply(self, cyclicVector):
        for i in range(0, self.b):
            self.messages[i] = CyclicGroupVector.scalarMultiply(self.messages[i], cyclicVector.at(i))


# class that represents the network handler of the system
class NetworkHandler (NetworkPart):

    """
    The class mainly consists of:
    - 2 message buffers: 1 for "messages" and 1 for "responses"
    - class fields that serve as accumulators of results between different callback calls.

    These accumulators are:
    - self.d                : the ElGamal public key of the scheme
    - self.R_inverseEG      : the value that is precomputed in the precomputation phase
    - self.decryptionShares : the decryption shares that each node sends that finally un-blind messages
    - self.mixResult        : the result of the mixing process that is un-blinded with the decryption shares
    """

    def __init__(self, b):
        NetworkPart.__init__(self)
        self.b = b
        self.nodesNum = 0
        self.d = 1
        self.R_inverseEG = None

        self.sendersBuffer = UsersBuffer(self.b)
        self.receiversBuffer = UsersBuffer(self.b)

        self.mixResult = {'FOR': None, 'RET': None}
        self.decryptionShares = {'FOR': None, 'RET': None}
        self.sendCallback = {'FOR': Callback.USER_MESSAGE, 'RET': Callback.USER_RESPONSE}

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

    # called after a successful message batch-response batch phase
    # resets counters, buffers and accumulators
    def reset(self):
        self.timesCalled[Callback.REAL_FOR_PREPROCESS] = 0
        self.timesCalled[Callback.REAL_FOR_POSTPROCESS] = 0
        self.timesCalled[Callback.REAL_RET_POSTPROCESS] = 0

        self.sendersBuffer = UsersBuffer(self.b)
        self.receiversBuffer = UsersBuffer(self.b)

        self.mixResult = {'FOR': None, 'RET': None}
        self.decryptionShares = {'FOR': None, 'RET': None}

    # callback called before the precomputation phase, when the public key is collectively constructed
    def appendKeyShare(self, message):
        code = message.callback
        share = message.payload
        self.d = CyclicGroup.multiply(self.d, share)
        if self.isLastCall(code):
            self.broadcast(Message(Callback.KEY_SHARE, self.d))

        return Status.OK

    # callback that computes the precomputation value needed and then broadcasts
    def preForPreProcess(self, message):
        code = message.callback
        r_inverseEG = ElGamalVector(vector=message.payload)

        if not self.R_inverseEG:
            self.R_inverseEG = r_inverseEG
        else:
            self.R_inverseEG = ElGamalVector.multiply(self.R_inverseEG, r_inverseEG)
            if self.isLastCall(code):
                self.network.sendToFirstNode(Message(Callback.PRE_FOR_MIX, self.R_inverseEG.vector))
        return Status.OK

    # called by a user that wants to send a "message"
    def getUserMessage(self, message):
        senderId = message.payload[0]
        blindMessage = CyclicGroupVector(vector=message.payload[1])
        self.sendersBuffer.addUser(senderId, blindMessage)
        if self.sendersBuffer.isFull():
            self.network.broadcastToNodes(self.id, Message(Callback.REAL_FOR_PREPROCESS, self.sendersBuffer.getUsers()))
        return Status.OK

    # called by a user that wants to send a "reponse"
    def getUserResponse(self, message):
        receiverId = message.payload[0]
        blindMessage = CyclicGroupVector(vector=message.payload[1])
        self.receiversBuffer.addUserMessage(receiverId, blindMessage)
        if self.receiversBuffer.isFull():
            self.network.sendToLastNode(Message(Callback.REAL_RET_MIX, self.receiversBuffer.getBlindMessages()))
        return Status.OK

    # callback in real-time phase, gradually replaces "keys" in blind messages with "random values" of mix nodes
    def realForPreProcess(self, message):
        code = message.callback
        cyclicVector = CyclicGroupVector(vector=message.payload)
        self.sendersBuffer.scalarMultiply(cyclicVector)
        if self.isLastCall(code):
            self.network.sendToFirstNode(Message(Callback.REAL_FOR_MIX, self.sendersBuffer.getBlindMessages()))
        return Status.OK

    # callback in real-time phase, gradually un-blinds the mix results and delivers "messages" to users
    def realForPostProcess(self, message):

        # receivers are gathered from the message vectors (remember: they are appended!)
        def getUsers():
            users = [self.mixResult['FOR'].at(i).pop() for i in range(0, self.b)]
            self.receiversBuffer.copyUsers(users)
            return users

        return self.__realPostProcess(message=message, path='FOR', getUsersCallback=getUsers)

    # callback in real-time phase, gradually un-blinds the mix results and delivers "responses" to users
    def realRetPostProcess(self, message):
        def getUsers():
            return self.sendersBuffer.getUsers()

        def cleanUp():
            self.reset()

        return self.__realPostProcess(message=message, path='RET', getUsersCallback=getUsers, cleanUp=cleanUp)

    # accumulate decryption shares if the mix results are not ready yet
    def __appendDecrShare(self, payload, path):
        if self.decryptionShares[path] is None:
            self.decryptionShares[path] = payload
        else:
            if self.mixResult[path] is None:
                self.decryptionShares[path] = CyclicGroupVector.multiply(self.decryptionShares[path], payload)
            else:
                self.decryptionShares[path] = payload

    # callback in real-time phase, gradually un-blinds the mix results and delivers messages (data) to users
    def __realPostProcess(self, message, path, getUsersCallback, cleanUp=None):
        code = message.callback
        isLastNode = message.payload[0]

        # the last node send the mix results along with his decryption share
        if isLastNode:
            self.mixResult[path] = Vector(vector=[CyclicGroupVector(vector=v) for v in message.payload[1]])
        else:
            self.__appendDecrShare(CyclicGroupVector(vector=message.payload[1]), path)

        # gradually un-blind messages
        if self.mixResult[path] is not None and self.decryptionShares[path] is not None:
            self.mixResult[path] = Vector(
                [CyclicGroupVector.scalarMultiply(self.mixResult[path].at(i), self.decryptionShares[path].at(i)) for i
                 in
                 range(0, self.b)])

        # when they are un-blinded, send to users
        if self.isLastCall(code):
            users = getUsersCallback()
            for i in range(0, self.b):
                self.network.sendToUser(users[i], Message(self.sendCallback[path], self.mixResult[path].at(i).vector))
            if cleanUp is not None:
                cleanUp()
        return Status.OK
