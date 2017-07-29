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
        self.s1 = []
        self.s1_inverse = []
        self.perm = []
        self.e = CyclicGroup.randomPair()

        self.mixForMessageComponents = None
        self.mixRetMessageComponents = None
        self.decryptionShareFor = None
        self.decryptionShareRet = None

        for i in range(0, b):
            self.r.append(CyclicGroup.random())
            self.r_inverse.append(CyclicGroup.inverse(self.r[-1]))

            self.s.append(CyclicGroup.random())
            self.s_inverse.append(CyclicGroup.inverse(self.s[-1]))

            self.s1.append(CyclicGroup.random())
            self.s1_inverse.append(CyclicGroup.inverse(self.s1[-1]))

            self.perm.append(i)

        shuffle(self.perm)

        self.associateCallback(Callback.KEY_SHARE, self.storeSharedKey, 1)
        self.associateCallback(Callback.PRE_FOR_MIX, self.preForwardMix, 1)
        self.associateCallback(Callback.PRE_FOR_POSTPROCESS, self.preForwardPostProcess, 1)
        self.associateCallback(Callback.PRE_RET_MIX, self.preReturnMix, 1)
        self.associateCallback(Callback.PRE_RET_POSTPROCESS, self.preReturnPostProcess, 1)

    def computeSecretShare(self):
        print "compute secret key share..."
        self.network.sendToNH(Message(Callback.KEY_SHARE, self.e[1]))

    def precompute(self):
        print "compute inverse r elgamal..."
        r_inverseEG = [ElGamalCipher(self.sharedKey, r) for r in self.r_inverse]
        self.network.sendToNH(Message(Callback.PRE_FOR_PREPROCESS, r_inverseEG))

    def storeSharedKey(self, message):
        self.sharedKey = message.payload
        return Status.OK

    def preForwardMix(self, message):
        messagePerm = permute(self.perm, message.payload)
        print "permute and multiply..."
        result = [m.multiply(ElGamalCipher(self.sharedKey, s_i)) for m, s_i in zip(messagePerm, self.s_inverse)]
        if not self.network.isLastNode(self.id):
            self.network.sendToNextNode(self.id, Message(Callback.PRE_FOR_MIX, result))
        else:
            self.mixMessageComponents = [r.messageComponent for r in result]
            message = Message(Callback.PRE_FOR_POSTPROCESS, [r.randomComponent for r in result])
            self.network.broadcastToNodes(self.id, message)
            self.preForwardPostProcess(message)

            result = [ElGamalCipher(self.sharedKey, s1_i) for s1_i in self.s1_inverse]
            self.network.sendToPreviousNode(self.id, Message(Callback.PRE_RET_MIX, result))
        return Status.OK

    def preForwardPostProcess(self, message):
        print "compute decryption share..."
        self.decryptionShareFor = [CyclicGroup.exp(r, self.e[0]) for r in message.payload]
        return Status.OK

    def preReturnMix(self, message):
        messagePerm = permute(self.perm, message.payload)
        print "permute and multiply..."
        result = [m.multiply(ElGamalCipher(self.sharedKey, s1_i)) for m, s1_i in zip(messagePerm, self.s1_inverse)]
        if not self.network.isFirstNode(self.id):
            self.network.sendToPreviousNode(self.id, Message(Callback.PRE_RET_MIX, result))
        else:
            self.mixRetMessageComponents = [r.messageComponent for r in result]
            message = Message(Callback.PRE_RET_POSTPROCESS, [r.randomComponent for r in result])
            self.network.broadcastToNodes(self.id, message)
            self.preReturnPostProcess(message)
        return Status.OK

    def preReturnPostProcess(self, message):
        self.decryptionShareRet = [CyclicGroup.exp(r, self.e[0]) for r in message.payload]
        return Status.OK
