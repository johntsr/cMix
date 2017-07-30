from network_part import NetworkPart
from crypto_utils import shuffle, CyclicGroup, ElGamalVector, CyclicGroupVector, CyclicGroupDualArray
from network_utils import Status, Callback, Message


class MixNode (NetworkPart):

    def __init__(self, b):
        NetworkPart.__init__(self)
        self.sharedKey = None
        self.b = b

        self.r = CyclicGroupDualArray(self.b)
        self.s = CyclicGroupDualArray(self.b)
        self.s1 = CyclicGroupDualArray(self.b)

        self.perm = range(0, b)
        shuffle(self.perm)
        self.e = CyclicGroup.randomPair()

        self.mixForMessageComponents = None
        self.mixRetMessageComponents = None
        self.decryptionShareFor = None
        self.decryptionShareRet = None

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
        self.network.sendToNH(Message(Callback.PRE_FOR_PREPROCESS, self.r.inverse().encrypt(self.sharedKey)))

    def storeSharedKey(self, message):
        self.sharedKey = message.payload
        return Status.OK

    def preForwardMix(self, message):
        print "permute and multiply..."
        result = ElGamalVector.multiply(
            message.payload.permute(self.perm),
            self.s.inverse().encrypt(self.sharedKey)
        )
        if not self.network.isLastNode(self.id):
            self.network.sendToNextNode(self.id, Message(Callback.PRE_FOR_MIX, result))
        else:
            self.mixForMessageComponents = result.messageComponents
            message = Message(Callback.PRE_FOR_POSTPROCESS, result.randomComponents())
            self.network.broadcastToNodes(self.id, message)
            self.preForwardPostProcess(message)

            self.network.sendToPreviousNode(self.id, Message(Callback.PRE_RET_MIX, self.s1.inverse().encrypt(self.sharedKey)))
        return Status.OK

    def preForwardPostProcess(self, message):
        print "compute decryption share..."
        self.decryptionShareFor = message.payload.exp(self.e[0])
        return Status.OK

    def preReturnMix(self, message):
        print "permute and multiply..."
        result = ElGamalVector.multiply(
            message.payload.permute(self.perm),
            self.s1.inverse().encrypt(self.sharedKey)
        )
        if not self.network.isFirstNode(self.id):
            self.network.sendToPreviousNode(self.id, Message(Callback.PRE_RET_MIX, result))
        else:
            self.mixRetMessageComponents = result.messageComponents()
            message = Message(Callback.PRE_RET_POSTPROCESS, result.randomComponents())
            self.network.broadcastToNodes(self.id, message)
            self.preReturnPostProcess(message)
        return Status.OK

    def preReturnPostProcess(self, message):
        self.decryptionShareRet = message.payload.exp(self.e[0])
        return Status.OK
