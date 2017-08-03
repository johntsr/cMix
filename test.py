import unittest, operator
from crypto_utils import *
from network.mix_node import MixNode
from network.network import Network
from network.network_handler import NetworkHandler
from network.user import User, randomResponse


class TestUtils(unittest.TestCase):

    def test_permute(self):
        size = 3
        perm = [2, 0, 1]

        key = CyclicGroup.random()
        elGamalVector = CyclicGroupVector(size).encrypt(key)
        elGamalVectorPerm = elGamalVector.permute(perm)

        self.assertEqual(elGamalVector.vector[0], elGamalVectorPerm.vector[1])
        self.assertEqual(elGamalVector.vector[1], elGamalVectorPerm.vector[2])
        self.assertEqual(elGamalVector.vector[2], elGamalVectorPerm.vector[0])

    def test_permute_inverse(self):
        size = 100
        key = CyclicGroup.random()
        elGamalVector = CyclicGroupVector(size).encrypt(key)

        perm = range(0, size)
        shuffle(perm)
        permInverse = inversePermute(perm)

        elGamalVector2 = elGamalVector.permute(perm).permute(permInverse)

        self.assertEqual(elGamalVector, elGamalVector2)

    def test_group_inverse(self):
        size = 10

        dualVector = CyclicGroupDualArray(size)
        prod = CyclicGroupVector.multiply(dualVector.array, dualVector.inverse)
        allOnes = [1] * size

        self.assertEqual(prod.vector, allOnes)

    def test_bob_alice(self):
        # https://en.wikipedia.org/wiki/ElGamal_encryption

        # Alice
        x = CyclicGroup.randomExp()
        h = CyclicGroup.exp2group(x)

        # Bob
        y = CyclicGroup.randomExp()
        c1 = CyclicGroup.exp2group(y)
        s_B = CyclicGroup.exp(h, y)
        m_B = CyclicGroup.random()
        c2 = CyclicGroup.multiply(m_B, s_B)
        # cipher = c1, c2

        # Alice
        s_A = CyclicGroup.exp(c1, x)
        self.assertEqual(s_A, s_B)

        m_A = CyclicGroup.multiply(c2, CyclicGroup.inverse(s_A))
        self.assertEqual(m_A, m_B)


class TestcMix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.b = 5
        cls.usersNum = 10

        cls.network = Network()
        cls.network.setNetworkHandler(NetworkHandler(cls.b))
        cls.network.addMixNode(MixNode(cls.b))
        cls.network.addMixNode(MixNode(cls.b))

        cls.network.init()

        cls.users = [User() for _ in range(0, cls.usersNum)]
        for user in cls.users:
            cls.network.addUser(user)

    def tearDown(self):
        self.network.networkHandler.reset()
        for user in self.users:
            user.setResponseGenerator(randomResponse)

    def __neighbourPairs(self, start, end):
        return [(i % self.usersNum, (i + 1) % self.usersNum) for i in range(start, end)]

    def __sendGarbage(self, pairs):
        for pair in pairs:
            sender = self.users[pair[0]]
            receiver = self.users[pair[1]]
            sender.sendMessage(receiver.id, CyclicGroupVector.random())

    def test_message_and_respond(self):

        pairs = self.__neighbourPairs(0, self.b)
        self.__sendGarbage(pairs)

        for pair in pairs:
            sender = self.users[pair[0]]
            receiver = self.users[pair[1]]
            self.assertNotEqual(sender.messageSent, None)
            self.assertNotEqual(sender.responseGot, None)
            self.assertNotEqual(receiver.messageGot, None)
            self.assertNotEqual(receiver.responseSent, None)
            self.assertEqual(sender.messageSent, receiver.messageGot)
            self.assertEqual(sender.responseGot, receiver.responseSent)

    def test_math_exchange(self):
        ops = {"+": operator.add, "-": operator.sub, "*": operator.mul, "\\": operator.div}
        mathToCyclic = {op: CyclicGroup.getUniqueId() for op in ops.keys()}
        for i in range(0, 100):
            mathToCyclic[long(i)] = CyclicGroup.getUniqueId()

        cyclicToMath = {v: k for k, v in mathToCyclic.iteritems()}

        def doBasicMath(cyclicVector):

            n = cyclicToMath[cyclicVector.at(0)]
            op = cyclicToMath[cyclicVector.at(1)]
            m = cyclicToMath[cyclicVector.at(2)]

            result = ops[op](n, m)
            return CyclicGroupVector(vector=[mathToCyclic[result]])

        alice = self.users[0]
        bob = self.users[1]
        bob.setResponseGenerator(doBasicMath)
        alice.sendMessage(bob.id, CyclicGroupVector(vector=[mathToCyclic[3L], mathToCyclic['+'], mathToCyclic[9L]]))
        self.__sendGarbage(self.__neighbourPairs(1, self.b))

        result = cyclicToMath[alice.responseGot[0]]
        self.assertEqual(result, 12L)

if __name__ == "__main__":
    unittest.main()
