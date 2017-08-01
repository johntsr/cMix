from crypto_utils import CyclicGroupVector
from network.network import Network
from network.network_handler import NetworkHandler
from network.mix_node import MixNode
from network.user import User

b = 5

def setUpNetwork():
    nh = NetworkHandler(b)
    node1 = MixNode(b)
    node2 = MixNode(b)
    node3 = MixNode(b)

    network = Network()
    network.setNetworkHandler(nh)
    network.addMixNode(node1)
    network.addMixNode(node2)
    # network.addMixNode(node3)

    network.init()
    return network

if __name__ == "__main__":
    network = setUpNetwork()
    for i in range(0, b):
        user = User()
        network.addUser(user)
        user.sendMessage(user.id, CyclicGroupVector(size=1))
