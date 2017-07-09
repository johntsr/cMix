from network.network_part import NetworkPart
from network.mix_node import MixNode

def setUpNetwork():
    b = 6
    nh = NetworkPart()
    node1 = MixNode(b)
    # node2 = MixNode(b)
    # node3 = MixNode(b)
    # node4 = MixNode(b)
    #
    # network = CommNetwork()
    # network.setNetworkHandler(nh)
    # network.addMixNode(node1)
    # network.addMixNode(node2)
    # network.addMixNode(node3)
    # network.addMixNode(node4)
    #
    # node1.broadcast("Hello all from node1!")
    # node4.send(node2.id, "Hello node 4!")


if __name__ == "__main__":
    setUpNetwork()
