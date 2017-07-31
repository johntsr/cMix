from network.network import Network
from network.network_handler import NetworkHandler
from network.mix_node import MixNode
import random

def setUpNetwork():
    b = 6
    nh = NetworkHandler()
    node1 = MixNode(b)
    node2 = MixNode(b)
    node3 = MixNode(b)

    network = Network()
    network.setNetworkHandler(nh)
    network.addMixNode(node1)
    network.addMixNode(node2)
    network.addMixNode(node3)

    network.init()


if __name__ == "__main__":
    # setUpNetwork()
    g1 = random.Random()
    g2 = random.Random()
    g1.seed(3)
    g2.seed(5)
    print g1.random()
    print g2.random()