from network_utils import Status, NetworkError


class Network:
    def __init__(self):
        self.networkHandler = None
        self.mixNodes = []
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

    def __receive(self, recipientId, message):
        code = self.networkParts[recipientId].receive(message)
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

    def init(self):
        for mixNode in self.mixNodes:
            mixNode.computeSecretShare()

        for mixNode in self.mixNodes:
            mixNode.precompute()
