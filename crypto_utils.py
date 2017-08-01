from Crypto import Random, Util

def shuffle(sequence):
    Random.random.shuffle(sequence)


def inversePermute(perm):
    permInverse = []
    b = len(perm)
    for p in range(0, b):
        for i in range(0, b):
            if perm[i] == p:
                permInverse.append(i)
                break
    return permInverse


def power(base, exp, modulo=None):
    if modulo is None:
        return pow(base, exp)
    else:
        return pow(base, exp, modulo)


class ElGamal:

    def __init__(self, sharedKey=None, value=None):
        self.randomComponent = None
        self.messageComponent = None
        if sharedKey is not None and value is not None:
            y = CyclicGroup.randomExp()
            self.randomComponent = CyclicGroup.exp2group(y)
            self.messageComponent = CyclicGroup.multiply(value, CyclicGroup.exp(sharedKey, y))

    def __eq__(self, other):
        return self.randomComponent == other.randomComponent and self.messageComponent == other.messageComponent

    @staticmethod
    def multiply(c1, c2):
        result = ElGamal()
        result.randomComponent = CyclicGroup.multiply(c1.randomComponent, c2.randomComponent)
        result.messageComponent = CyclicGroup.multiply(c1.messageComponent, c2.messageComponent)
        return result


class Vector:

    def __init__(self, vector):
        self.vector = vector
        self.multiplyFun = None
        self.scalarMultiplyFun = None

    def __eq__(self, other):
        return self.vector == other.vector

    def size(self):
        return len(self.vector)

    def at(self, i):
        return self.vector[i]

    def append(self, element):
        self.vector.append(element)

    def permute(self, perm):
        return Vector([self.vector[p] for p in perm])

    @staticmethod
    def multiply__(vector1, vector2, multiplyFunction):
        return [multiplyFunction(v1, v2) for v1, v2 in zip(vector1.vector, vector2.vector)]


class ElGamalVector(Vector):

    def __init__(self, vector, key=None):
        Vector.__init__(self, vector)
        if key is not None:
            self.vector = [ElGamal(key, v) for v in vector]

    def permute(self, perm):
        return ElGamalVector(vector=Vector.permute(self, perm).vector)

    def messageComponents(self):
        return CyclicGroupVector(vector=[r.messageComponent for r in self.vector])

    def randomComponents(self):
        return CyclicGroupVector(vector=[r.randomComponent for r in self.vector])

    @staticmethod
    def multiply(vector1, vector2):
        return ElGamalVector(vector=Vector.multiply__(vector1, vector2, ElGamal.multiply))


class CyclicGroupVector(Vector):

    def __init__(self, size=None, vector=None):
        Vector.__init__(self, vector)
        if vector is None:
            self.vector = []
            for i in range(0, size):
                self.vector.append(CyclicGroup.random())

    def permute(self, perm):
        return CyclicGroupVector(vector=Vector.permute(self, perm).vector)

    def inverse(self):
        return CyclicGroupVector(vector=[CyclicGroup.inverse(v) for v in self.vector])

    def pop(self):
        result = self.vector[-1]
        del self.vector[-1]
        return result

    def encrypt(self, key):
        return ElGamalVector(self.vector, key)

    def exp(self, e):
        return CyclicGroupVector(vector=[CyclicGroup.exp(v, e) for v in self.vector])

    @staticmethod
    def scalarMultiply(vector, cyclicNumber):
        return CyclicGroupVector(vector=[CyclicGroup.multiply(v, cyclicNumber) for v in vector.vector])

    @staticmethod
    def multiply(vector1, vector2):
        return CyclicGroupVector(vector=Vector.multiply__(vector1, vector2, CyclicGroup.multiply))


class CyclicGroupDualArray:

    def __init__(self, b):
        self.array = CyclicGroupVector(size=b)
        self.inverse = CyclicGroupVector(vector=[CyclicGroup.inverse(a) for a in self.array.vector])


class CyclicGroup:

    g =     19167066187022047436478413372880824313438678797887170030948364708695623454002582820938932961803261022277829853214287063757589819807116677650566996585535208649540448432196806454948132946013329765141883558367653598679571199251774119976449205171262636938096065535299103638890429717713646407483320109071252653916730386204380996827449178389044942428078669947938163252615751345293014449317883432900504074626873215717661648356281447274508124643639202368368971023489627632546277201661921395442643626191532112873763159722062406562807440086883536046720111922074921528340803081581395273135050422967787911879683841394288935013751
    order = 9968108389283139384500126851590910765388862256943492148736139047638818228043845477934450154869436209608798158762945749064212036697920030256947481168799132161279027615283393134357251369006458334758956359930154909543130908546999523713052822914048781317956011883544205342076807844957026467849313731346886391754340903453226366576558059611090955640495198876364264568947354655829865223811545250229670077826984304447786213073394010704828751390199575312681385536506430568502567177652698918604152960901576654034795592432088438139775481415636626281932952252619581888967324362795163037790197356322486462953657408538495400234553
    modulo =19936216778566278769000253703181821530777724513886984297472278095277636456087690955868900309738872419217596317525891498128424073395840060513894962337598264322558055230566786268714502738012916669517912719860309819086261817093999047426105645828097562635912023767088410684153615689914052935698627462693772783508681806906452733153116119222181911280990397752728529137894709311659730447623090500459340155653968608895572426146788021409657502780399150625362771073012861137005134355305397837208305921803153308069591184864176876279550962831273252563865904505239163777934648725590326075580394712644972925907314817076990800469107

    uniqueIDs = set()

    @staticmethod
    def multiply(r1, r2):
        return (r1 * r2) % CyclicGroup.modulo

    @staticmethod
    def exp(r, e):
        return power(r, e, CyclicGroup.modulo)

    @staticmethod
    def randomExp(generator=None):
        if generator is None:
            return Util.number.getRandomRange(1, CyclicGroup.order)
        else:
            return generator.randint(1, CyclicGroup.order)

    @staticmethod
    def exp2group(e):
        return CyclicGroup.exp(CyclicGroup.g, e)

    @staticmethod
    def exp2inverse(e):
        r = CyclicGroup.exp2group(e)
        return CyclicGroup.inverse(r)

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

    @staticmethod
    def getUniqueId():
        uniqueId = CyclicGroup.random()
        while uniqueId in CyclicGroup.uniqueIDs:
            uniqueId = CyclicGroup.random()
        CyclicGroup.uniqueIDs.add(uniqueId)
        return uniqueId