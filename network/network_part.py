class NetworkPart:
    id = 0

    def __init__(self):
        self.commNetwork = None
        self.id = NetworkPart.id
        NetworkPart.id += 1
        print "Network part created with id = ", self.id

    def setCommNetwork(self, commNetwork):
        self.commNetwork = commNetwork

    def receive(self, message):
        print "Network part ", self.id, " got message: ", message

    def broadcast(self, message):
        self.commNetwork.broadcast(self.id, message)

    def send(self, recipientId, message):
        self.commNetwork.send(recipientId, message)
