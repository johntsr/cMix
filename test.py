import unittest
from crypto_utils import CyclicGroup


class TestcMix(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

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
