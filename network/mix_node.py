from network_part import NetworkPart
from crypto_utils import shuffle, power, CyclicGroup, ElGamalCipher
from network_utils import Status, Callback, Message


class MixNode (NetworkPart):

    def __init__(self, b):
        NetworkPart.__init__(self)
        self.sharedKey = None
        self.R_inverseEG = None
        self.b = b
        self.r = []
        self.s = []
        self.perm = []
        self.e = CyclicGroup.randomPair()

        self.r_inverse = []
        for i in range(0, b):
            exp = CyclicGroup.randomExp()
            self.r.append(CyclicGroup.exp2group(exp))
            self.r_inverse.append(CyclicGroup.exp2inverse(exp))

            self.s.append(CyclicGroup.random())
            self.perm.append(i)

        shuffle(self.perm)
        # print "b = ", self.b
        # print "r = ", self.r
        # print "s = ", self.s
        # print "perm = ", self.perm

        self.associateCallback(Callback.KEY_SHARE, self.storeSharedKey, 1)
        self.associateCallback(Callback.R_INVERSE_EG, self.storeR_inverseEG, 1)

    # def decrypt(self, cipher):
    #     return power(cipher, -self.e[0])

    def storeSharedKey(self, message):
        self.sharedKey = message.payload
        return Status.OK

    def storeR_inverseEG(self, message):
        self.R_inverseEG = message.payload
        # print self.R_inverseEG[0].messageComponent, self.R_inverseEG[0].randomComponent
        return Status.OK

    def computeSecretShare(self):
        self.network.sendToNH(Message(Callback.KEY_SHARE, self.e[1]))
        print "computed key!"

    def computeR_ElGamal(self):
        r_inverseEG = [ElGamalCipher(self.sharedKey, r) for r in self.r_inverse]
        print "compute elgamal!"
        self.network.sendToNH(Message(Callback.R_INVERSE_EG, r_inverseEG))
