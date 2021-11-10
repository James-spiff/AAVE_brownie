from scripts.helpful_scripts import get_account
from brownie import interface, network, config

#This let's us swap ETH for WETH(WETH is an ERC 20 version of ETH)
def get_weth():
    #Mint WETH by depositing ETH\
    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": 0.1 * 10 ** 18})
    tx.wait(1)
    print("Received 0.1 WETH")
    return tx 

def main():
    get_weth()