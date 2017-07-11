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
            if partId == senderId:
                continue
            self.__receive(partId, message)

    def sendToNH(self, message):
        self.__receive(self.networkHandler.id, message)

    def init(self):
        for mixNode in self.mixNodes:
            mixNode.computeSecretShare()

        for mixNode in self.mixNodes:
            mixNode.computeR_ElGamal()
