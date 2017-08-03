import unittest, operator
from crypto_utils import *
from network.mix_node import MixNode
from network.network import Network
from network.network_handler import NetworkHandler
from network.user import User, randomResponse


# class that tests the proper functionality of crypto_utils primitives
class TestUtils(unittest.TestCase):

    # test the permutation of an array
    def test_permute(self):
        # e.g.
        # [a, b, c] x [2, 0, 1] -> [c, a, b]
        size = 3
        perm = [2, 0, 1]

        vector = CyclicGroupVector(size)
        vectorPerm = vector.permute(perm)

        self.assertEqual(vector.vector[0], vectorPerm.vector[1])
        self.assertEqual(vector.vector[1], vectorPerm.vector[2])
        self.assertEqual(vector.vector[2], vectorPerm.vector[0])

    # test the inverse permutation
    def test_permute_inverse(self):
        # pick a random array
        # permute it
        # and permute it again with the inverse permutation
        # then, the resulted array must be equal to the original one
        size = 100
        vector = CyclicGroupVector(size)

        perm = range(0, size)
        shuffle(perm)
        permInverse = inversePermute(perm)

        vector2 = vector.permute(perm).permute(permInverse)

        self.assertEqual(vector, vector2)

    # test the inverse operation in a cyclic group
    def test_group_inverse(self):
        # pick a random vector
        # compute it's inverse vector (inverse every element of the vector)
        # multiply the 2 arrays, the result must be an array of 1s
        size = 10

        dualVector = CyclicGroupDualArray(size)
        prod = CyclicGroupVector.multiply(dualVector.array, dualVector.inverse)
        allOnes = [1] * size
        self.assertEqual(prod.vector, allOnes)

    # test a basic ElGamal encrypted conversation
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


# class that tests the proper functionality of the cMix network
class TestcMix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # create a cMix mixnet of 3 mix-nodes and 10 users
        cls.b = 5
        cls.usersNum = 10

        cls.network = Network()
        cls.network.setNetworkHandler(NetworkHandler(cls.b))
        cls.network.addMixNode(MixNode(cls.b))
        cls.network.addMixNode(MixNode(cls.b))
        cls.network.addMixNode(MixNode(cls.b))

        cls.network.init()

        cls.users = [User() for _ in range(0, cls.usersNum)]
        for user in cls.users:
            cls.network.addUser(user)

    def tearDown(self):
        # after every test
        self.network.networkHandler.reset()             # reset the NH (needed if a test fails)
        for user in self.users:                         # reset the response handler of the users
            user.setResponseHandler(randomResponse)

    # create pairs (sender, receiver) (for simplicity, neighbouring pairs)
    def __neighbourPairs(self, start, end):
        return [(i % self.usersNum, (i + 1) % self.usersNum) for i in range(start, end)]

    # send garbage-messages to the mixnet to trigger a cMix real-time phase
    def __sendGarbage(self, pairs):
        for pair in pairs:
            sender = self.users[pair[0]]
            receiver = self.users[pair[1]]
            sender.sendMessage(receiver.id, CyclicGroupVector.random())

    # test basic messaging
    def test_message_and_respond(self):

        # create some pairs
        # send garbage-messages
        # and check if the messages and the responses match

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

    # test messaging under a more complex protocol
    # messages of the form: (3 + 9), (12 * 5)
    # responses compute the result: 12, 60
    def test_math_exchange(self):
        # first, map the messaging symbols uniquely to cyclic group members and backwards
        # then, define a response handler (a function that reads a cMic message and outputs a cMix response)
        # finally, check if the response is the expected result (3 + 9 == 12)

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
        bob.setResponseHandler(doBasicMath)
        alice.sendMessage(bob.id, CyclicGroupVector(vector=[mathToCyclic[3L], mathToCyclic['+'], mathToCyclic[9L]]))
        self.__sendGarbage(self.__neighbourPairs(1, self.b))

        result = cyclicToMath[alice.responseGot[0]]
        self.assertEqual(result, 12L)


if __name__ == "__main__":
    unittest.main()
