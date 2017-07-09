from network_part import NetworkPart
from crypto_utils import CyclicGroup, shuffle, power
from network_utils import Callback

class NetworkHandler (NetworkPart):

    def __init__(self):
        NetworkPart.__init__(self)
        self.callbacks[Callback.KEY_SHARE] = self.appendKeyShare
        self.d = 1

    def appendKeyShare(self, e):
        print "Will append ", e
        self.d *= e

