from network_part import NetworkPart
from crypto_utils import CyclicGroup, shuffle, power
from network_utils import Status, Callback, Message


class MixNode (NetworkPart):

    def __init__(self, b):
        NetworkPart.__init__(self)
        self.sharedKey = None
        self.b = b
        self.r = []
        self.s = []
        self.perm = []
        self.e = CyclicGroup.randomWithExp()

        for i in range(0, b):
            self.r.append(CyclicGroup.random())
            self.s.append(CyclicGroup.random())
            self.perm.append(i)

        shuffle(self.perm)
        # print "b = ", self.b
        # print "r = ", self.r
        # print "s = ", self.s
        # print "perm = ", self.perm

        self.associateCallback(Callback.KEY_SHARE, self.storeSharedKey, 1)

    def decrypt(self, cipher):
        return power(cipher, -self.e[0])

    def init(self):
        self.network.sendToNH(Message(Callback.KEY_SHARE, self.e[1]))

    def storeSharedKey(self, key):
        self.sharedKey = key
        return Status.OK
