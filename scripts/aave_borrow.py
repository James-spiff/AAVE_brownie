from scripts.helpful_scripts import get_account
from brownie import config, network, interface
from scripts.get_weth import get_weth
from web3 import Web3

#default amount = 0.1
amount = Web3.toWei(0.1, "ether")

def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    
    if network.show_active() in ["mainnet-fork"]:
        get_weth()

    #ABI #Address
    lending_pool = get_lending_pool()
    #To deposit our WETH we need to approve our ERC20 token 1st
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    
    #Now we deposit our WETH to AAVE
    print('Depositing...')
    tx = lending_pool.deposit(erc20_address, amount, account.address, 0, {"from": account}) #0 stands for the referal code they don't work anymore but it still needs to be passed so we just put dummy data
    tx.wait(1) #wait for 1 block confirmation
    print('Deposited!')
    #Retrieving User data
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    
    #Borrowing Dai. To borrow Dai we need to get Dai in terms of ETH
    print("Borrow Dai")
    dai_eth_price_feed = config["networks"][network.show_active()]["dai_eth_price_feed"]
    dai_eth_price = get_asset_price(dai_eth_price_feed)
    #below we are converting borrowable_eth -> borrowable_dai and multiplying it by 95% 
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95) #we multiply it by 0.95(95%) as a buffer to ensure our health factor is better and avoid liquidation
    print(f"We are borrowing {amount_dai_to_borrow} DAI")

    #Borrowing
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address, 
        Web3.toWei(amount_dai_to_borrow, 'ether'),
        1, #this reps intresetRateMode their are 2 modes 1 for Stable and 2 for Variable
        0, #reps referal code
        account.address,
        {"from": account}, 
    )
    borrow_tx.wait(1)
    print("DAI borrowed successfully!")
    get_borrowable_data(lending_pool, account) #To display our current account information

    #Repay borrowed asset
    #repay_all(amount, lending_pool, account)
    print("Successfully deposited, borrowed and repayed")


#Function to approve our ERC20 token
def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return tx


#The lending pool contract is the main contract of the AAVE protocol that contains all the services the protocol offers
def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool() #returns the address of the associated lendingPool
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


#This function get's data for the user associated with the user's capacity to borrow or use the financial services on AAVE it returns data like user's collateral, debt etc
def get_borrowable_data(lending_pool, account):
    #getUserAccountData pulls all the user data for us
    (
        total_collateral_eth, 
        total_debt_eth, 
        available_borrow_eth, 
        current_liquidation_threshold, 
        ltv, #loan to value
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    #convert the above returned data from Wei to ETH
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))

    
#Get's the price of Dai in ETH
def get_asset_price(price_feed_address):
    #ABI
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]  #the price is returned as the 1st index
    converted_latest_price = Web3.fromWei(latest_price, 'ether')
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)


#Function to repay borrowed asset
def repay_all(amount, lending_pool, account):
    #1st we approve the token
    approve_erc20(
        Web3.toWei(amount, 'ether'), 
        lending_pool, 
        config["networks"][network.show_active()]["dai_token"], 
        account
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,  #reps rateMode which is the type of borrow debt. 1 reps Stable and 2 reps Variable
        account.address,
        {"from": account},
        )
    repay_tx.wait(1)
    print("Asset Repaid!")