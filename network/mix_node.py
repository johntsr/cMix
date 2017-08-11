from key_manager import KeyManager
from crypto_utils import shuffle, inversePermute, CyclicGroup, ElGamalVector, CyclicGroupDualArray, \
    CyclicGroupVector, \
    Vector
from network_part import NetworkPart
from network_utils import Status, Callback, Message


# class that represents a mix node in the mixnet
class MixNode (NetworkPart):

    """
    The class mainly consists of:
    - the key manager, whose keys are used to blind and un-blind messages/responses
    - 3 cyclic group dual arrays (array + inverse) used to blind and un-blind messages
    - the permutation array (self.perm) and its inverse (self.permInverse)
    - the tuple (key share in cyclic group, exponent of key share): self.e
    - the message components that the last node stores (forward and return): self.mixMessageComponents
    - the decryption shares that every node computes (forward and return): self.decryptionShare
    - the commitments (forward and return) of the last node stored by the other nodes: self.realMixCommitment
    """

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

    # called in network.init() before the precomputation phase, when the public key is collectively constructed
    def computeSecretShare(self):
        self.network.sendToNH(Message(Callback.KEY_SHARE, self.e[1]))

    # store the above shared key (that the NH broadcasts)
    def storeSharedKey(self, message):
        self.sharedKey = message.payload
        return Status.OK

    # callback that performs dummy key exchange with a user
    def sendUserKey(self, message):
        userId = message.payload
        self.keyManager.addSeeds(userId)
        payload = [self.id, self.keyManager.getSeed(userId, KeyManager.MESSAGE), self.keyManager.getSeed(userId, KeyManager.RESPONSE)]
        self.network.sendToUser(userId, Message(Callback.KEY_USER, payload))
        return Status.OK

    # called in network.init(), initiates the precomputation process
    def precompute(self):
        self.network.sendToNH(Message(Callback.PRE_FOR_PREPROCESS, self.r.inverse.encrypt(self.sharedKey).vector))

    # callback that performs the mixing process in the the forward path of precomputation phase
    def preForwardMix(self, message):
        status = self.__preMix(message=ElGamalVector(vector=message.payload), path='FOR')

        # the last node initiates the matching return path
        if self.__finalNode('FOR'):
            self.network.sendToPreviousNode(self.id, Message(Callback.PRE_RET_MIX,
                                                             self.S['RET'].inverse.encrypt(self.sharedKey).vector))
        return status

    # callback that computes the decryption share of the forward path
    def preForwardPostProcess(self, message):
        return self.__prePostProcess(randomComponents=CyclicGroupVector(vector=message.payload), path='FOR')

    # callback that performs mixing process in the the return path of precomputation phase
    def preReturnMix(self, message):
        return self.__preMix(message=ElGamalVector(vector=message.payload), path='RET')

    # callback that computes the decryption share of the return path
    def preReturnPostProcess(self, message):
        return self.__prePostProcess(randomComponents=CyclicGroupVector(vector=message.payload), path='RET')

    # callback that computes the value that gradually replaces "keys" with "r" values in blind "messages"
    def realForPreProcess(self, message):
        self.senders = message.payload
        cyclicVector = self.keyManager.getNextKeys(ids=self.senders, type=KeyManager.MESSAGE, inverse=False)
        product = CyclicGroupVector.multiply(cyclicVector, self.r.array)
        self.network.sendToNH(Message(Callback.REAL_FOR_PREPROCESS, product.vector))
        return Status.OK

    # callback that performs the mixing process in the the forward path of real-time phase
    def realForMix(self, message):
        return self.__realMix(message=Vector(vector=[CyclicGroupVector(vector=v) for v in message.payload]), path='FOR')

    # callback that performs the mixing process in the the return path of real-time phase
    def realRetMix(self, message):
        def tempProcess(temp):
            return self.__returnPathKeyBlinding(temp)
        return self.__realMix(message=Vector(vector=[CyclicGroupVector(vector=v) for v in message.payload]), path='RET',
                              tempProcess=tempProcess)

    # callback that stores the commitment of the last node regarding
    # the mixing process in the the forward path of real-time phase
    def realForMixCommit(self, message):
        def resultProcess(decrShare):
            return decrShare
        return self.__realMixCommit(message=Vector(vector=[CyclicGroupVector(vector=v) for v in message.payload]),
                                    path='FOR', resultProcess=resultProcess)

    # callback that stores the commitment of the last node regarding
    # the mixing process in the the return path of real-time phase
    def realRetMixCommit(self, message):
        def resultProcess(decrShare):
            return self.__returnPathKeyBlinding(decrShare)
        return self.__realMixCommit(message=Vector(vector=[CyclicGroupVector(vector=v) for v in message.payload]),
                                    path='RET', resultProcess=resultProcess)

    # performs the mixing process of the precomputation phase
    def __preMix(self, message, path):
        result = ElGamalVector.multiply(
            message.permute(self.permutation[path]),
            self.S[path].inverse.encrypt(self.sharedKey)
        )
        if not self.__finalNode(path):
            self.__toNextNode(path, Message(self.preMixCallback[path], result.vector))
        else:
            self.mixMessageComponents[path] = result.messageComponents()
            message = Message(self.prePostProcessCallback[path], result.randomComponents().vector)
            self.network.broadcastToNodes(self.id, message)
            self.receive(message.toJSON())
        return Status.OK

    # performs the mixing process of the real-time phase
    def __realMix(self, message, path, tempProcess=None):
        temp = message.permute(self.permutation[path])
        result = Vector(
            [CyclicGroupVector.scalarMultiply(temp.at(i), self.S[path].array.at(i)) for i in range(0, self.b)])
        if not self.__finalNode(path):
            self.__toNextNode(path, Message(self.realMixCallback[path], [v.vector for v in result.vector]))
        else:
            self.network.broadcastToNodes(self.id,
                                          Message(self.mixCommitCallback[path], [v.vector for v in result.vector]))
            temp = CyclicGroupVector.multiply(self.decryptionShare[path], self.mixMessageComponents[path])
            if tempProcess is not None:
                temp = tempProcess(temp)

            result = Vector(
                [CyclicGroupVector.scalarMultiply(result.at(i), temp.at(i)) for i in range(0, self.b)])
            self.network.sendToNH(
                Message(self.realPostProcessCallback[path], [True, [v.vector for v in result.vector]]))
        return Status.OK

    # computes the decryption share
    def __prePostProcess(self, randomComponents, path):
        self.decryptionShare[path] = randomComponents.exp(self.e[0]).inverse()
        return Status.OK

    # the blinding proceess that the mix node performs in the return path (that involves user keys)
    def __returnPathKeyBlinding(self, temp):
        return CyclicGroupVector.multiply(temp,
                                          self.keyManager.getNextKeys(ids=self.senders, type=KeyManager.RESPONSE,
                                                                      inverse=False))

    # stores the mixing commitment
    def __realMixCommit(self, message, path, resultProcess):
        self.realMixCommitment[path] = message
        result = resultProcess(self.decryptionShare[path])
        self.network.sendToNH(Message(self.realPostProcessCallback[path], [False, result.vector]))
        return Status.OK

    def __toNextNode(self, path, message):
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
