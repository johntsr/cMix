from crypto_utils import CyclicGroupVector
from network.network import Network
from network.network_handler import NetworkHandler
from network.mix_node import MixNode
from network.user import User


def setUpNetwork():
    b = 1
    nh = NetworkHandler(b)
    node1 = MixNode(b)
    node2 = MixNode(b)

    network = Network()
    network.setNetworkHandler(nh)
    network.addMixNode(node1)
    network.addMixNode(node2)

    network.init()
    return network

if __name__ == "__main__":
    network = setUpNetwork()
    user = User()
    network.addUser(user)
    user.sendMessage(user.id, CyclicGroupVector(size=1))
