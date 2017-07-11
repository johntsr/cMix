from Crypto import Random
from Crypto import Util


def shuffle(sequence):
    Random.random.shuffle(sequence)


def power(base, exp, modulo=None):
    if modulo is None:
        return pow(base, exp)
    else:
        return pow(base, exp, modulo)


class ElGamalCipher:

    def __init__(self, sharedKey=None, value=None):
        self.randomComponent = None
        self.messageComponent = None
        if sharedKey is not None and value is not None:
            y = CyclicGroup.randomExp()
            self.randomComponent = CyclicGroup.exp2group(y)
            self.messageComponent = CyclicGroup.multiply(value, CyclicGroup.exp(sharedKey, y))

    def multiply(self, elGamalCipher):
        result = ElGamalCipher()
        result.randomComponent = CyclicGroup.multiply(self.randomComponent, elGamalCipher.randomComponent)
        result.messageComponent = CyclicGroup.multiply(self.messageComponent, elGamalCipher.messageComponent)
        return result


class CyclicGroup:

    g =     19167066187022047436478413372880824313438678797887170030948364708695623454002582820938932961803261022277829853214287063757589819807116677650566996585535208649540448432196806454948132946013329765141883558367653598679571199251774119976449205171262636938096065535299103638890429717713646407483320109071252653916730386204380996827449178389044942428078669947938163252615751345293014449317883432900504074626873215717661648356281447274508124643639202368368971023489627632546277201661921395442643626191532112873763159722062406562807440086883536046720111922074921528340803081581395273135050422967787911879683841394288935013751
    order = 9968108389283139384500126851590910765388862256943492148736139047638818228043845477934450154869436209608798158762945749064212036697920030256947481168799132161279027615283393134357251369006458334758956359930154909543130908546999523713052822914048781317956011883544205342076807844957026467849313731346886391754340903453226366576558059611090955640495198876364264568947354655829865223811545250229670077826984304447786213073394010704828751390199575312681385536506430568502567177652698918604152960901576654034795592432088438139775481415636626281932952252619581888967324362795163037790197356322486462953657408538495400234553
    modulo =19936216778566278769000253703181821530777724513886984297472278095277636456087690955868900309738872419217596317525891498128424073395840060513894962337598264322558055230566786268714502738012916669517912719860309819086261817093999047426105645828097562635912023767088410684153615689914052935698627462693772783508681806906452733153116119222181911280990397752728529137894709311659730447623090500459340155653968608895572426146788021409657502780399150625362771073012861137005134355305397837208305921803153308069591184864176876279550962831273252563865904505239163777934648725590326075580394712644972925907314817076990800469107

    @staticmethod
    def test():
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
        assert s_A == s_B

        m_A = CyclicGroup.multiply(c2, CyclicGroup.inverse(s_A))
        assert m_A == m_B


    @staticmethod
    def multiply(r1, r2):
        return (r1 * r2) % CyclicGroup.modulo

    @staticmethod
    def exp(r, e):
        return power(r, e, CyclicGroup.modulo)

    @staticmethod
    def randomExp():
        return Util.number.getRandomRange(1, CyclicGroup.order)

    @staticmethod
    def exp2group(e):
        return CyclicGroup.exp(CyclicGroup.g, e)

    # @staticmethod
    # def exp2inverse(exp):
    #     return CyclicGroup.exp2group(CyclicGroup.order % exp)

    @staticmethod
    def inverse(a):
        t = 0
        newt = 1
        r = CyclicGroup.modulo
        newr = a
        while newr != 0:
            quotient = r // newr
            (t, newt) = (newt, t - quotient * newt)
            (r, newr) = (newr, r - quotient * newr)

        if r > 1:
            assert 1 == 2
        if t < 0:
            t += CyclicGroup.modulo
        return t

    @staticmethod
    def randomPair():
        exp = CyclicGroup.randomExp()
        return exp, CyclicGroup.exp2group(exp)

    @staticmethod
    def random():
        return CyclicGroup.randomPair()[1]
