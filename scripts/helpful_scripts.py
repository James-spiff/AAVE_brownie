from brownie import accounts, network, config #, MockV3Aggregator, VRFCoordinatorMock, LinkToken, Contract, interface

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]    #a forked environment is a copy of a live blockchain on a mainnet that runs locally and can be interacted with the same way as a live mainnet blockchain
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local", "mainnet-fork"]


def get_account():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS or network.show_active() in FORKED_LOCAL_ENVIRONMENTS:
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])