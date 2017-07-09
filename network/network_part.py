import logging
from network_utils import Status, NetworkError, handleError


class NetworkPart:
    id = 0

    def __init__(self):
        self.network = None
        self.id = NetworkPart.id
        NetworkPart.id += 1
        self.callbacks = {}
        print "Network part created with id = ", self.id

    def setNetwork(self, network):
        self.network = network

    def receive(self, message):
        print "Network part ", self.id, " got message: ", message
        self.callbacks[message[0]](message[1])
        return Status.OK

    def broadcast(self, message):
        try:
            self.network.broadcast(self.id, message)
        except NetworkError as error:
            handleError(error)

    def send(self, recipientId, message):
        try:
            self.network.send(recipientId, message)
        except NetworkError as error:
            handleError(error)
