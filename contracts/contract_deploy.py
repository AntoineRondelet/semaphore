'''
    copyright 2018 to the Semaphore Authors

    This file is part of Semaphore.

    Semaphore is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Semaphore is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Semaphore.  If not, see <https://www.gnu.org/licenses/>.
'''

import json
import web3

from web3 import Web3, HTTPProvider, TestRPCProvider
from solc import compile_source, compile_standard, compile_files
from solc import compile_source, compile_files, link_code
from web3.contract import ConciseContract


w3 = Web3(HTTPProvider("http://localhost:8545"));


def hex2int(elements):
    ints = []
    for el in elements:
        ints.append(int(el, 16))
    return(ints)

def compile(tree_depth):
    miximus = "../contracts/Miximus.sol"
    Pairing =  "../contracts/Pairing.sol"
    Verifier = "../contracts/Verifier.sol"

    compiled_sol =  compile_files([Pairing, Verifier, miximus], allow_paths="./contracts")

    miximus_interface = compiled_sol[miximus + ':Miximus']
    verifier_interface = compiled_sol[Verifier + ':Verifier']

    return(miximus_interface, verifier_interface)
   

def contract_deploy(tree_depth, vk_dir, merkle_root):
    miximus_interface , verifier_interface  = compile(tree_depth)
    with open(vk_dir) as json_data:
        vk = json.load(json_data)


    vk  = [hex2int(vk["a"][0]),
           hex2int(vk["a"][1]),
           hex2int(vk["b"]),
           hex2int(vk["c"][0]),
           hex2int(vk["c"][1]),
           hex2int(vk["g"][0]),
           hex2int(vk["g"][1]),
           hex2int(vk["gb1"]),
           hex2int(vk["gb2"][0]),
           hex2int(vk["gb2"][1]),
           hex2int(vk["z"][0]),
           hex2int(vk["z"][1]),
           hex2int(sum(vk["IC"], []))
    ]

     # Instantiate and deploy contract
    miximus = w3.eth.contract(abi=miximus_interface['abi'], bytecode=miximus_interface['bin'])
    verifier = w3.eth.contract(abi=verifier_interface['abi'], bytecode=verifier_interface['bin'])

    # Get transaction hash from deployed contract
    tx_hash = verifier.deploy(args=vk, transaction={'from': w3.eth.accounts[0], 'gas': 4000000})
    # Get tx receipt to get contract address

    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash, 10000)
    verifier_address = tx_receipt['contractAddress']


    tx_hash = miximus.deploy(transaction={'from': w3.eth.accounts[0], 'gas': 4000000}, args=[verifier_address, merkle_root])

    # Get tx receipt to get contract address
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash, 10000)
    miximus_address = tx_receipt['contractAddress']

    # Contract instance in concise mode
    abi = miximus_interface['abi']
    miximus = w3.eth.contract(address=miximus_address, abi=abi,ContractFactoryClass=ConciseContract)
    return(miximus)

def verify(contract, pk):

    tx_hash = contract.isTrue(pk["a"] , pk["a_p"], pk["b"], pk["b_p"] , pk["c"], pk["c_p"] , pk["h"] , pk["k"], pk["input"] , transact={'from': w3.eth.accounts[0], 'gas': 4000000})
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash, 10000)

    print(tx_receipt)
