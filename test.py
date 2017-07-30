import unittest
from crypto_utils import *


class TestUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

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


if __name__ == "__main__":
    unittest.main()
