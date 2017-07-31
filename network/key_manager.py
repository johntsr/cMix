import random

from crypto_utils import CyclicGroup


class KeyManager:

    def __init__(self):
        self.userSeeds = {}
        self.userKeyGens = {}

    def addKey(self, id, seed=None):
        if seed is None:
            seed = CyclicGroup.random()
        generator = random.Random()
        generator.seed(seed)
        self.userSeeds[id] = seed
        self.userKeyGens[id] = generator

    def getSeed(self, id):
        return self.userSeeds[id]

    def getNextKey(self, id):
        return self.userKeyGens[id].random()
