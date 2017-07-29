from network_part import NetworkPart
from crypto_utils import shuffle, CyclicGroup, ElGamalCipher, permute
from network_utils import Status, Callback, Message


class MixNode (NetworkPart):

    def __init__(self, b):
        NetworkPart.__init__(self)
        self.sharedKey = None
        self.R_inverseEG = None
        self.b = b
        self.r = []
        self.r_inverse = []
        self.s = []
        self.s_inverse = []
        self.perm = []
        self.e = CyclicGroup.randomPair()

        self.mixMessageComponents = None
        self.decryptionShare = None

        for i in range(0, b):
            self.r.append(CyclicGroup.random())
            self.r_inverse.append(CyclicGroup.inverse(self.r[-1]))

            self.s.append(CyclicGroup.random())
            self.s_inverse.append(CyclicGroup.inverse(self.s[-1]))

            self.perm.append(i)

        shuffle(self.perm)

        self.associateCallback(Callback.KEY_SHARE, self.storeSharedKey, 1)
        self.associateCallback(Callback.PRE_MIX, self.preMix, 1)
        self.associateCallback(Callback.PRE_POSTPROCESS, self.prePostProcess, 1)

    # def decrypt(self, cipher):
    #     return power(cipher, -self.e[0])

    def storeSharedKey(self, message):
        self.sharedKey = message.payload
        return Status.OK

    def computeSecretShare(self):
        print "compute secret key share..."
        self.network.sendToNH(Message(Callback.KEY_SHARE, self.e[1]))

    def computeR_ElGamal(self):
        print "compute inverse r elgamal..."
        r_inverseEG = [ElGamalCipher(self.sharedKey, r) for r in self.r_inverse]
        self.network.sendToNH(Message(Callback.PRE_PREPROCESS, r_inverseEG))

    def preMix(self, message):
        messagePerm = permute(self.perm, message.payload)
        print "permute and multiply..."
        result = [m.multiply(ElGamalCipher(self.sharedKey, s_i)) for m, s_i in zip(messagePerm, self.s_inverse)]
        if not self.network.isLastNode(self.id):
            self.network.sendToNextNode(self.id, Message(Callback.PRE_MIX, result))
        else:
            self.mixMessageComponents = [r.messageComponent for r in result]
            message = Message(Callback.PRE_POSTPROCESS, [r.randomComponent for r in result])
            self.network.broadcastToNodes(self.id, message)
            self.prePostProcess(message)
        return Status.OK

    def prePostProcess(self, message):
        print "compute decryption share..."
        self.decryptionShare = [CyclicGroup.exp(r, self.e[0]) for r in message.payload]
        return Status.OK
