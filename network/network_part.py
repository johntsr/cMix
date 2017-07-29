from network_utils import Status, NetworkError, handleError


class NetworkPart:
    id = 0

    def __init__(self):
        self.network = None
        self.id = NetworkPart.id
        NetworkPart.id += 1
        self.callbacks = {}
        self.timesCalled = {}
        self.timesMax = {}

    def associateCallback(self, code, callback, timesMax=None):
        self.callbacks[code] = callback
        self.timesCalled[code] = 0

        if timesMax is None:
            timesMax = 0

        self.timesMax[code] = timesMax

    def setNetwork(self, network):
        self.network = network

    def isLastCall(self, code):
        return self.timesCalled[code] == self.timesMax[code]

    def receive(self, message):
        if self.timesCalled[message.callback] <= self.timesMax[message.callback]:
            self.timesCalled[message.callback] += 1
            return self.callbacks[message.callback](message)
        else:
            return Status.ERROR

    def broadcast(self, message):
        try:
            self.network.broadcast(self.id, message)
        except NetworkError as error:
            handleError(error)

    # def send(self, recipientId, message):
    #     try:
    #         self.network.send(recipientId, message)
    #     except NetworkError as error:
    #         handleError(error)
