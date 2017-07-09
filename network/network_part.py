import logging, sys
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
        print "Network part created with id = ", self.id

    def associateCallback(self, code, callback, timesMax=sys.maxint):
        self.callbacks[code] = callback
        self.timesCalled[code] = 0
        self.timesMax[code] = timesMax

    def setNetwork(self, network):
        self.network = network

    def receive(self, message):
        print "Network part ", self.id, " got message: ", str(message)
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
