from network_utils import Status, NetworkError


# a mocking network class
class Network:

    """
    The class consists of:
    - the Network Handler (NH)
    - the mix nodes
    - the users of the system

    All the above parties implement the "NetworkPart" class

    Proper usage:
    - first, set the NH
    - the, add all the mix nodes
    - afterwards, call the "init" method and add users to the system (the order here doesn't matter)
    """
    def __init__(self):
        self.networkHandler = None
        self.mixNodes = []
        self.users = {}
        self.networkParts = {}

    def setNetworkHandler(self, networkHandler):
        networkHandler.setNetwork(self)
        self.networkHandler = networkHandler
        self.networkParts[networkHandler.id] = networkHandler

    def addMixNode(self, mixNode):
        mixNode.setNetwork(self)
        self.mixNodes.append(mixNode)
        self.networkParts[mixNode.id] = mixNode
        self.networkHandler.includeNode()

    def addUser(self, user):
        user.setNetwork(self)
        self.users[user.id] = user
        self.networkParts[user.id] = user
        user.setUp()

    def __receive(self, recipientId, message):
        code = self.networkParts[recipientId].receive(message.toJSON())
        if code != Status.OK:
            raise NetworkError((code, recipientId, str(message)))

    def broadcast(self, senderId, message):
        for partId in self.networkParts:
            if partId != senderId:
                self.__receive(partId, message)

    def sendToNH(self, message):
        self.__receive(self.networkHandler.id, message)

    def sendToFirstNode(self, message):
        self.__receive(self.mixNodes[0].id, message)

    def sendToLastNode(self, message):
        self.__receive(self.mixNodes[-1].id, message)

    def isLastNode(self, id):
        return self.mixNodes[-1].id == id

    def sendToNextNode(self, id, message):
        if self.isLastNode(id):
            raise NetworkError((Status.ERROR, id, "Cannot send to next node, I am last!" + " (message = " + str(message)))

        for i in range(0, len(self.mixNodes) - 1):
            if self.mixNodes[i].id == id:
                self.__receive(self.mixNodes[i+1].id, message)

    def isFirstNode(self, id):
        return self.mixNodes[0].id == id

    def sendToPreviousNode(self, id, message):
        if self.isFirstNode(id):
            raise NetworkError((Status.ERROR, id, "Cannot send to previous node, I am first!" + " (message = " + str(message)))

        for i in range(1, len(self.mixNodes)):
            if self.mixNodes[i].id == id:
                self.__receive(self.mixNodes[i-1].id, message)

    def broadcastToNodes(self, id, message):
        for node in self.mixNodes:
            if node.id != id:
                self.__receive(node.id, message)

    def sendToUser(self, id, message):
        if self.users[id] is None:
            raise NetworkError((Status.ERROR, id, "Cannot find user with id = " + id))
        self.__receive(id, message)

    def init(self):
        print "Initializing precomputation phase..."
        for mixNode in self.mixNodes:
            mixNode.computeSecretShare()

        for mixNode in self.mixNodes:
            mixNode.precompute()

        print "Done precomputations!"
