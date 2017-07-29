from network_part import NetworkPart
from crypto_utils import CyclicGroup, shuffle
from network_utils import Status, Callback, Message


class NetworkHandler (NetworkPart):

    def __init__(self):
        NetworkPart.__init__(self)
        self.associateCallback(Callback.KEY_SHARE, self.appendKeyShare)
        self.associateCallback(Callback.PRE_FOR_PREPROCESS, self.prePreProcess)
        self.nodesNum = 0
        self.d = 1
        self.R_inverseEG = []

    def includeNode(self):
        self.nodesNum += 1
        self.timesMax[Callback.KEY_SHARE] = self.nodesNum
        self.timesMax[Callback.PRE_FOR_PREPROCESS] = self.nodesNum

    def appendKeyShare(self, message):
        share = message.payload
        code = message.callback
        self.d = CyclicGroup.multiply(self.d, share)
        if self.isLastCall(code):
            self.broadcast(Message(Callback.KEY_SHARE, self.d))

        return Status.OK

    def prePreProcess(self, message):
        r_inverseEG = message.payload
        code = message.callback

        if not self.R_inverseEG:
            self.R_inverseEG = r_inverseEG
        else:
            self.R_inverseEG = [r1.multiply(r2) for r1, r2 in zip(self.R_inverseEG, r_inverseEG)]
            if self.isLastCall(code):
                self.network.sendToFirstNode(Message(Callback.PRE_FOR_MIX, self.R_inverseEG))
        return Status.OK
