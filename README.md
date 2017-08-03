# cMix

This project implements the [cMix mixnet specifications](https://eprint.iacr.org/2016/008.pdf).
The cyclic group that is mentioned in the paper is implemented with modular multiplications. The crypto operations needed are supported by the [pyCrypto](https://pypi.python.org/pypi/pycrypto/2.6.1) project.
A mock network is introduced; so, no real communication over sockets takes place. In this environment, the messages that exchanges between the mixnet parties (the network handler and the mixnodes) include a message code, that indicates the callback function to be executed upon delivery, and a message payload, the actual data that are meant to be delivered. 
In the test.py file, the usage of the mixnet by its users is demonstrated.

## Notes
- No real key exchange mechanism is implemented (such as Diffie-Hellman). For simplicity, whenever a user asks for a key from a mix node, the mix node decides the key and then sends it back to the user.
- The commitment values of the last mix node (that guarantee that no tagging takes place) are not processed in any way from the rest of the system.
