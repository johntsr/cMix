class CommNetwork:
    def __init__(self):
        self.networkHandler = None
        self.mixNodes = []
        self.networkParts = {}

    def setNetworkHandler(self, networkHandler):
        networkHandler.setCommNetwork(self)
        self.networkHandler = networkHandler
        self.networkParts[networkHandler.id] = networkHandler

    def addMixNode(self, mixNode):
        mixNode.setCommNetwork(self)
        self.mixNodes.append(mixNode)
        self.networkParts[mixNode.id] = mixNode

    def broadcast(self, senderId, message):
        for partId in self.networkParts:
            if partId == senderId:
                continue
            self.networkParts[partId].receive(message)

    def send(self, recipiendId, message):
        self.networkParts[recipiendId].receive(message)
