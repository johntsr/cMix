from network_part import NetworkPart
from crypto_utils import CyclicGroup, shuffle, power
from network_utils import Status, Callback, Message


class NetworkHandler (NetworkPart):

    def __init__(self):
        NetworkPart.__init__(self)
        self.associateCallback(Callback.KEY_SHARE, self.appendKeyShare)
        self.d = 1
        self.nodesNum = 0

    def includeNode(self):
        self.nodesNum += 1
        self.timesMax[Callback.KEY_SHARE] = self.nodesNum

    def appendKeyShare(self, message):
        share = message.payload
        # print "Will append ", share
        self.d *= share
        if self.timesCalled[message.callback] == self.nodesNum:
            self.broadcast(Message(Callback.KEY_SHARE, self.d))

        return Status.OK
