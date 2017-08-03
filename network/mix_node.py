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
        s = CyclicGroupDualArray(self.b)
        s1 = CyclicGroupDualArray(self.b)
        self.S = {'FOR': s, 'RET': s1}

        perm = range(0, b)
        shuffle(perm)
        permInverse = inversePermute(perm)
        self.permutation = {'FOR': perm, 'RET': permInverse}

        self.e = CyclicGroup.randomPair()

        self.mixMessageComponents = {'FOR': None, 'RET': None}
        self.preMixCallback = {'FOR': Callback.PRE_FOR_MIX, 'RET': Callback.PRE_RET_MIX}
        self.realMixCallback = {'FOR': Callback.REAL_FOR_MIX, 'RET': Callback.REAL_RET_MIX}
        self.mixCommitCallback = {'FOR': Callback.REAL_FOR_MIX_COMMIT, 'RET': Callback.REAL_RET_MIX_COMMIT}
        self.prePostProcessCallback = {'FOR': Callback.PRE_FOR_POSTPROCESS, 'RET': Callback.PRE_RET_POSTPROCESS}
        self.realPostProcessCallback = {'FOR': Callback.REAL_FOR_POSTPROCESS, 'RET': Callback.REAL_RET_POSTPROCESS}

        self.decryptionShare = {'FOR': None, 'RET': None}
        self.realMixCommitment = {'FOR': None, 'RET': None}
        self.senders = None

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
        self.associateCallback(Callback.REAL_RET_MIX, self.realRetMix)
        self.associateCallback(Callback.REAL_RET_MIX_COMMIT, self.realRetMixCommit)

    def computeSecretShare(self):
        self.network.sendToNH(Message(Callback.KEY_SHARE, self.e[1]))

    def storeSharedKey(self, message):
        self.sharedKey = message.payload
        return Status.OK

    def precompute(self):
        self.network.sendToNH(Message(Callback.PRE_FOR_PREPROCESS, self.r.inverse.encrypt(self.sharedKey)))

    def preForwardMix(self, message):
        status = self.__preMix(message=message, path='FOR')
        if self.__finalNode('FOR'):
            self.network.sendToPreviousNode(self.id, Message(Callback.PRE_RET_MIX,
                                                             self.S['RET'].inverse.encrypt(self.sharedKey)))
        return status

    def preForwardPostProcess(self, message):
        return self.__prePostProcess(message=message, path='FOR')

    def preReturnMix(self, message):
        return self.__preMix(message=message, path='RET')

    def preReturnPostProcess(self, message):
        return self.__prePostProcess(message=message, path='RET')

    def sendUserKey(self, message):
        userId = message.payload
        self.keyManager.addSeeds(userId)
        payload = self.id, self.keyManager.getSeed(userId, KeyManager.MESSAGE), self.keyManager.getSeed(userId, KeyManager.RESPONSE)
        self.network.sendToUser(userId, Message(Callback.KEY_USER, payload))
        return Status.OK

    def realForPreProcess(self, message):
        self.senders = message.payload
        cyclicVector = self.keyManager.getNextKeys(ids=self.senders, type=KeyManager.MESSAGE, inverse=False)
        product = CyclicGroupVector.multiply(cyclicVector, self.r.array)
        self.network.sendToNH(Message(Callback.REAL_FOR_PREPROCESS, product))
        return Status.OK

    def realForMix(self, message):
        return self.__realMix(message=message, path='FOR')

    def realRetMix(self, message):
        def tempProcess(temp):
            return self.__returnPathKeyBlinding(temp)
        return self.__realMix(message=message, path='RET', tempProcess=tempProcess)

    def realForMixCommit(self, message):
        def resultProcess(decrShare):
            return decrShare
        return self.__realMixCommit(message=message, path='FOR', resultProcess=resultProcess)

    def realRetMixCommit(self, message):
        def resultProcess(decrShare):
            return self.__returnPathKeyBlinding(decrShare)
        return self.__realMixCommit(message=message, path='RET', resultProcess=resultProcess)

    def __preMix(self, message, path):
        result = ElGamalVector.multiply(
            message.payload.permute(self.permutation[path]),
            self.S[path].inverse.encrypt(self.sharedKey)
        )
        if not self.__finalNode(path):
            self.__nextToNode(path, Message(self.preMixCallback[path], result))
        else:
            self.mixMessageComponents[path] = result.messageComponents()
            message = Message(self.prePostProcessCallback[path], result.randomComponents())
            self.network.broadcastToNodes(self.id, message)
            self.receive(message)
        return Status.OK

    def __prePostProcess(self, message, path):
        randomComponents = message.payload
        self.decryptionShare[path] = randomComponents.exp(self.e[0]).inverse()
        return Status.OK

    def __returnPathKeyBlinding(self, temp):
        return CyclicGroupVector.multiply(temp,
                                          self.keyManager.getNextKeys(ids=self.senders, type=KeyManager.RESPONSE,
                                                                      inverse=False))

    def __realMixCommit(self, message, path, resultProcess):
        self.realMixCommitment[path] = message.payload
        result = resultProcess(self.decryptionShare[path])
        self.network.sendToNH(Message(self.realPostProcessCallback[path], (False, result)))
        return Status.OK

    def __realMix(self, message, path, tempProcess=None):
        temp = message.payload.permute(self.permutation[path])
        result = Vector(
            [CyclicGroupVector.scalarMultiply(temp.at(i), self.S[path].array.at(i)) for i in range(0, self.b)])
        if not self.__finalNode(path):
            self.__nextToNode(path, Message(self.realMixCallback[path], result))
        else:
            self.network.broadcastToNodes(self.id, Message(self.mixCommitCallback[path], result))
            temp = CyclicGroupVector.multiply(self.decryptionShare[path], self.mixMessageComponents[path])
            if tempProcess is not None:
                temp = tempProcess(temp)

            result = Vector(
                [CyclicGroupVector.scalarMultiply(result.at(i), temp.at(i)) for i in range(0, self.b)])
            self.network.sendToNH(Message(self.realPostProcessCallback[path], (True, result)))
        return Status.OK

    def __nextToNode(self, path, message):
        if path == 'FOR':
            return self.network.sendToNextNode(self.id, message)
        elif path == 'RET':
            return self.network.sendToPreviousNode(self.id, message)
        else:
            raise Exception("Wrong path!")

    def __finalNode(self, path):
        if path == 'FOR':
            return self.network.isLastNode(self.id)
        elif path == 'RET':
            return self.network.isFirstNode(self.id)
        else:
            raise Exception("Wrong path!")
