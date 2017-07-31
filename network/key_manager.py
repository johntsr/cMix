import random
from crypto_utils import CyclicGroup

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

    def getCombinedKey(self, type, inverse=False):
        return self.keyStorages[type].getCombinedKey(inverse)

class KeyStorage:

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

    def getCombinedKey(self, inverse):
        product = 1
        for id, generator in self.generators:
            product = CyclicGroup.multiply(product, generator.random())

        if inverse:
            return CyclicGroup.inverse(product)
        else:
            return product
