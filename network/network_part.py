from crypto_utils import CyclicGroup
from network_utils import Status, NetworkError, handleError


# superclass of all parties in the "Network"
class NetworkPart:

    """
    The class consists of:
    - a reference to the network
    - a unique id in the network
    - associations of message codes and callback functions
    Moreover, those callbacks may have a limited number of times that can be called.
    This limit is useful when, for example, the NH waits for all the nodes to send a share. Then, the callback that
    collects the shares must be called a fixed number of times.
    If this limit is exceeded, an error is raised by the network.
    """
    def __init__(self):
        self.network = None
        self.id = CyclicGroup.getUniqueId()
        self.callbacks = {}
        self.timesCalled = {}
        self.timesMax = {}

    def associateCallback(self, code, callback, timesMax=None):
        self.callbacks[code] = callback
        self.timesCalled[code] = 0
        self.timesMax[code] = timesMax

    def setNetwork(self, network):
        self.network = network

    def isLastCall(self, code):
        return self.timesCalled[code] == self.timesMax[code]

    def receive(self, message):
        if self.timesMax[message.callback] is None or self.timesCalled[message.callback] < self.timesMax[message.callback]:
            self.timesCalled[message.callback] += 1
            return self.callbacks[message.callback](message)
        else:
            return Status.ERROR

    def broadcast(self, message):
        try:
            self.network.broadcast(self.id, message)
        except NetworkError as error:
            handleError(error)

