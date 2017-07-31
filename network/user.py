from network_part import NetworkPart
from key_manager import KeyManager
from network_utils import Status, Callback, Message


class MixNode (NetworkPart):

    def __init__(self):
        NetworkPart.__init__(self)

        self.keyManager = KeyManager()

        self.associateCallback(Callback.KEY_USER, self.storeKeyUser)

    def setUp(self):
        self.network.broadcastToNodes(self.id, self.id)

    def storeKeyUser(self, message):
        nodeId = message[0]
        nodeKey = message[1]
        self.keyManager.addKey(nodeId, nodeKey)
        return Status.OK
