from crypto_utils import shuffle, inversePermute, CyclicGroup, ElGamalVector, CyclicGroupDualArray, CyclicGroupVector, \
    Vector
from key_manager import KeyManager
from network_part import NetworkPart
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
        self.permInverse = inversePermute(self.perm)

        self.e = CyclicGroup.randomPair()

        self.mixForMessageComponents = None
        self.mixRetMessageComponents = None
        self.decryptionShareFor = None
        self.decryptionShareRet = None
        self.realForMixCommitment = None

        self.keyManager = KeyManager()

        self.associateCallback(Callback.KEY_SHARE, self.storeSharedKey, 1)
        self.associateCallback(Callback.PRE_FOR_MIX, self.preForwardMix, 1)
        self.associateCallback(Callback.PRE_FOR_POSTPROCESS, self.preForwardPostProcess, 1)
        self.associateCallback(Callback.PRE_RET_MIX, self.preReturnMix, 1)
        self.associateCallback(Callback.PRE_RET_POSTPROCESS, self.preReturnPostProcess, 1)
        self.associateCallback(Callback.KEY_USER, self.sendUserKey)
        self.associateCallback(Callback.REAL_FOR_PREPROCESS, self.realForPreProcess)
        self.associateCallback(Callback.REAL_FOR_MIX, self.realForMix)
        self.associateCallback(Callback.REAL_FOR_MIX_COMMIT, self.realForMixCommit)

    def computeSecretShare(self):
        print "compute secret key share..."
        self.network.sendToNH(Message(Callback.KEY_SHARE, self.e[1]))

    def storeSharedKey(self, message):
        self.sharedKey = message.payload
        return Status.OK

    def precompute(self):
        print "compute inverse r elgamal..."
        self.network.sendToNH(Message(Callback.PRE_FOR_PREPROCESS, self.r.inverse.encrypt(self.sharedKey)))

    def preForwardMix(self, message):
        print "permute and multiply..."
        result = ElGamalVector.multiply(
            message.payload.permute(self.perm),
            self.s.inverse.encrypt(self.sharedKey)
        )
        if not self.network.isLastNode(self.id):
            self.network.sendToNextNode(self.id, Message(Callback.PRE_FOR_MIX, result))
        else:
            self.mixForMessageComponents = result.messageComponents()
            print "mixForMessageComponents -> ", self.mixForMessageComponents.size()
            message = Message(Callback.PRE_FOR_POSTPROCESS, result.randomComponents())
            self.network.broadcastToNodes(self.id, message)
            self.preForwardPostProcess(message)

            self.network.sendToPreviousNode(self.id, Message(Callback.PRE_RET_MIX, self.s1.inverse.encrypt(self.sharedKey)))
        return Status.OK

    def preForwardPostProcess(self, message):
        print "compute decryption share..."
        randomComponents = message.payload
        self.decryptionShareFor = randomComponents.exp(self.e[0]).inverse()
        print "decryptionShareFor -> ", self.decryptionShareFor.size()
        return Status.OK

    def preReturnMix(self, message):
        print "permute and multiply..."
        result = ElGamalVector.multiply(
            message.payload.permute(self.permInverse),
            self.s1.inverse.encrypt(self.sharedKey)
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
        randomComponents = message.payload
        self.decryptionShareRet = randomComponents.exp(self.e[0]).inverse()
        return Status.OK

    def sendUserKey(self, message):
        userId = message.payload
        self.keyManager.addSeeds(userId)
        payload = self.id, self.keyManager.getSeed(userId, KeyManager.MESSAGE), self.keyManager.getSeed(userId, KeyManager.RESPONSE)
        self.network.sendToUser(userId, Message(Callback.KEY_USER, payload))
        return Status.OK

    def realForPreProcess(self, message):
        senders = message.payload
        keyVector = [self.keyManager.getNextKey(id=sender, type=KeyManager.MESSAGE, inverse=False) for sender in senders]
        cyclicVector = CyclicGroupVector(vector=keyVector)
        product = CyclicGroupVector.multiply(cyclicVector, self.r.array)
        self.network.sendToNH(Message(Callback.REAL_FOR_PREPROCESS, product))
        return Status.OK

    def realForMix(self, message):
        print "permute and multiply..."
        temp = message.payload.permute(self.perm)
        result = Vector(
            [CyclicGroupVector.scalarMultiply(temp.at(i), self.s.array.at(i)) for i in range(0, temp.size())])
        if not self.network.isLastNode(self.id):
            self.network.sendToNextNode(self.id, Message(Callback.REAL_FOR_MIX, result))
        else:
            self.network.broadcastToNodes(self.id, Message(Callback.REAL_FOR_MIX_COMMIT, result))

            print "result -> ", result.size()
            print "result.at(0) -> ", result.at(0).size()

            temp = CyclicGroupVector.multiply(self.decryptionShareFor, self.mixForMessageComponents)
            result = Vector(
                [CyclicGroupVector.scalarMultiply(result.at(i), temp.at(i)) for i in range(0, result.size())])
            self.network.sendToNH(Message(Callback.REAL_FOR_POSTPROCESS, (True, result)))
        return Status.OK

    def realForMixCommit(self, message):
        self.realForMixCommitment = message.payload
        print "commitment = ", self.realForMixCommitment
        self.network.sendToNH(Message(Callback.REAL_FOR_POSTPROCESS, (False, self.decryptionShareFor)))
        return Status.OK
