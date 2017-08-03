import random
from crypto_utils import CyclicGroup, CyclicGroupVector


# class that facilitates the user of "KeyStorage" class
# in brief, 2 "KeyStorage" objects are needed: 1 for the forward path and 1 for the return path
class KeyManager:

    MESSAGE = 0
    RESPONSE = 1

    def __init__(self):
        self.keyStorages = {KeyManager.MESSAGE: KeyStorage(),
                            KeyManager.RESPONSE: KeyStorage()}

    def addSeeds(self, id, seeds=None):
        if seeds is None:
            seeds = CyclicGroup.random(), CyclicGroup.random()

        self.keyStorages[KeyManager.MESSAGE].addSeed(id, seeds[0])
        self.keyStorages[KeyManager.RESPONSE].addSeed(id, seeds[0])

    def getSeed(self, id, type):
        return self.keyStorages[type].getSeed(id)

    def getCombinedKey(self, type, inverse):
        return self.keyStorages[type].getCombinedKey(inverse)

    def getNextKey(self, id, type, inverse):
        return self.keyStorages[type].getNextKey(id, inverse)

    def getNextKeys(self, ids, type, inverse):
        return CyclicGroupVector(vector=[self.getNextKey(id, type, inverse) for id in ids])


# class that stores the CSPRNGs needed for the key derivation
class KeyStorage:

    # the seeds will not be stores once proper key-exchange is established
    # for simplicity, the server decides the key and sends it to the user

    # one generator is needed for every communication party (CP, either mix node or user)
    def __init__(self):
        self.seeds = {}
        self.generators = {}

    def addSeed(self, id, seed):
        generator = random.Random()
        generator.seed(seed)
        self.seeds[id] = seed
        self.generators[id] = generator

    def getSeed(self, id):
        return self.seeds[id]

    # derives the keys of all CPs and multiplies them
    def getCombinedKey(self, inverse):
        product = 1
        for id in self.generators:
            product = CyclicGroup.multiply(product, self.getNextKey(id, inverse=False))

        if inverse:
            return CyclicGroup.inverse(product)
        else:
            return product

    # derive the next key for a given CP id
    def getNextKey(self, id, inverse):
        nextKey = CyclicGroup.exp2group(CyclicGroup.randomExp(generator=self.generators[id]))
        if inverse:
            return CyclicGroup.inverse(nextKey)
        else:
            return nextKey
