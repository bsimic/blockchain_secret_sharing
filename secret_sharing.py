#used libraries
import time
from web3 import Web3, HTTPProvider
import contract_abi
from encrypt_string import *
import datetime
from secretsharing import PlaintextToHexSecretSharer

#addresses
contract_address = '####'
wallet_private_key = '####'
wallet_private_key2 = '####'
wallet_private_key3 = '####'
wallet_address = '####'
encryptedKey = "random_key"

#connect to Ropsten network using Infura
w3 = Web3 (HTTPProvider('https://ropsten.infura.io/v3/27d470ee6c064f139543579bf55894d7'))
w3.eth.enable_unaudited_features()

contract = w3.eth.contract(address = contract_address, abi = contract_abi.abi)

#send ether to the smart contract address to add the account address to the approved list
def sendEtherToContract(amount_in_ether):
    amount_in_wei = w3.toWei(amount_in_ether,'ether');
    nonce = w3.eth.getTransactionCount(wallet_address)
    txn_dict = {
            'to': contract_address,
            'value': amount_in_wei,
            'gas': 4000000,
            'gasPrice': w3.toWei('200', 'gwei'),
            'nonce': nonce,
            'chainId': 3
    }
    signed_txn = w3.eth.account.signTransaction(txn_dict, wallet_private_key)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    txn_receipt = None
    count = 0
    while txn_receipt is None and (count < 30):
        txn_receipt = w3.eth.getTransactionReceipt(txn_hash)
        print(txn_receipt)
        time.sleep(10)

    if txn_receipt is None:
        return {'status': 'failed', 'error': 'timeout'}
    return {'status': 'added', 'txn_receipt': txn_receipt}

#register the encrypted value to the blockchain
def sendEventToContract(vrijeme):
    nonce = w3.eth.getTransactionCount(wallet_address)
    txn_dict = contract.functions.addEvent(vrijeme).buildTransaction({
        'chainId': 3,
        'gas': 800000,
        'gasPrice': w3.toWei('400', 'gwei'),
        'nonce': nonce,
    })

    signed_txn = w3.eth.account.signTransaction(txn_dict, private_key=wallet_private_key)
    result = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    tx_receipt = w3.eth.getTransactionReceipt(result)

    count = 0
    while tx_receipt is None and (count < 30):
        time.sleep(10)
        tx_receipt = w3.eth.getTransactionReceipt(result)
        print(tx_receipt)

    if tx_receipt is None:
        return {'status': 'failed', 'error': 'timeout'}

    processed_receipt = contract.events.broadcastEvent().processReceipt(tx_receipt)
    print(processed_receipt)

    output = "Address {} noted an event: {}"\
        .format(processed_receipt[0].args._address, processed_receipt[0].args._timestamp)
    print(output)
    return {'status': 'added', 'processed_receipt': processed_receipt}

#return the value from blockchain
def returnString():
	blockchainTimestamp = contract.functions.getEvent().call()
	return blockchainTimestamp

#get the currect timestamp
timestamp = datetime.datetime.now().strftime("%d.%b %Y %I:%M%p")

#main menu
while True:
    choice = input ("What do you want to do?\n1. Write a new timestamp\n2. Fetch and decrypt last recorded timestamp\n3. Record address on the list of approved addresses (Ether needed)\n")
    if choice in ['1', '2', '3']:
        break

#First choice - after fetching the current timestamp, separate the given string into 3 parts using secret sharing. The parts are then encrypted using the 3 private keys and are afterwards combined into one string. 
if choice == "1":
    #separate the secret into 3 parts
    shares = PlaintextToHexSecretSharer.split_secret(timestamp, 2, 3)
    #ecrypting the parts
    key1 = encryptString(wallet_private_key, shares[0])
    key2 = encryptString(wallet_private_key2, shares[1])
    key3 = encryptString(wallet_private_key3, shares[2])
    #combine the keys in a string, simultaneously inserting a delimiter so we can separate the string later on
    encryptionChain = key1 + "__" + key2 + "__" + key3
    #write the value on the blockchain
    sendEventToContract(encryptionChain)

#Second choice - returning the value written on the blockchain, separate it and save it as a list. Enter 2/3 keys for the value to be decrypted
elif choice == "2":
    #return value
    returnedValue = returnString()
    splitString = returnedValue.split("__") 
    #Enter the first key - check if the key is valid
    first_key = input("Insert first private key:\n")
    if(first_key == "####"):
        first_returned_share = decryptString(first_key, splitString[0])
    elif(first_key == "####"):
        first_returned_share = decryptString(first_key, splitString[1])
    elif(first_key == "####"):
        first_returned_share = decryptString(first_key, splitString[2])
    #Enter the second key - check if the key is valid
    second_key = input("Insert second private key:\n")
    if(second_key == "####"):
        second_returned_share = decryptString(first_key, splitString[0])
    elif(second_key == "####"):
        second_returned_share = decryptString(first_key, splitString[1])
    elif(second_key == "####"):
        second_returned_share = decryptString(first_key, splitString[2])
    #merge the decrypted keys in a list to start a function that will rebuild the secret
    share_list = []
    share_list.append(first_returned_share)
    share_list.append(second_returned_share)
    print(PlaintextToHexSecretSharer.recover_secret(share_list[0:2]))

#Third choice - send a small amounth of Ether to the contact address to get approved
elif choice == "3":
    sendEtherToContract(1)
