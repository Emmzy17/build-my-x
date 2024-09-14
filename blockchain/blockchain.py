import hashlib
from time import time
import json
from uuid import uuid4
from urllib.parse import urlparse
from textwrap import dedent
from flask import Flask, jsonify, request

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create Genesis Block
        self.new_block(previous_hash=1, proof=100)
        self.nodes = set()
    def new_block(self, proof, previous_hash=None):
        
        block = {
            'index' : len(self.chain) + 1,
            'timestamp' : time(),
            'transaction' : self.current_transactions,
            'proof' : proof,
            'previous_hash': previous_hash or self.hash[-1],
        }

        # Reset the current list of transaction
        self.current_transactions = []

        self.chain.append(block)
        return block
    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """

        self.current_transactions.append({
            'sender' : sender,
            'recipient' : recipient,
            'amount' : amount
        })

      
        return self.last_block['index'] + 1
    def register_node(self, address):
        """
        Add a new node to the list of nodes 
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """
        parse_url = urlparse(address)
        self.nodes.add(parse_url.netlocs)
        return None
    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        lastblock = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f"{lastblock}")
            print(f"{block}")
            print(f"\n--------\n")
            
            #Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(lastblock):
                return False
            
            # Check that the proof of work is correct
            if not self.validate_proof(lastblock['proof'], block['proof']):
                return False
            
            lastblock = block
            current_index += 1

        return True
    
    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        max_chain = None

        # We are looking for chains longer than ours
        max_length = len(self.chain)

        #Grab and verify the chains from all nodes
        for node in neighbours:
            response = request.get(f"http:/{node}/chain")

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if length is longer and chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
            # Replace our chain if we found a new chain valid and longer than ours
            if new_chain:
                self.chain = new_chain
                return True
            return False

    @staticmethod
    def hash(block):
        """
         Creates a SHA-256 hash of a Block
         :param block: <dict> Block
         :return: <str>
         """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashe
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block).hexdigest()
    

    @property
    def last_block(self):
        # Returns the last block in the chain
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while self.validate_proof(last_proof, proof):
            proof += 1
        return proof
    @staticmethod
    def validate_proof(last_proof, proof):
        """
            Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes
            :param last_proof: <int> Previous Proof
            :param proof: <int> Current Proof
            :return: <bool> True if correct, False if not.
        """
        guess = f'{last_proof, proof}'.encode()
        guess_hash =  hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"
#instantiate the app
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '--')

#Instantiate the blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must recieve a reward for finding the proof
    # the sender is "0" to signify that this node has mined a new coin

    blockchain.new_transaction(sender="0", recipient=node_identifier, amount=1)

    #Forge the new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message' : "New block forged",
        'index' : block['index'],
        'transactions': block['transactions'],
        'proof' : block['proof'],
        'previous_hash' : block['previous_hash']
    }



@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    #Ensure the required field are posted on the data
    required = ['sender', 'recipient', 'amount']
    if not all (k in values for k in required):
        return 'Missing values', 400
    # Create a new transaction 
    index  = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message' :f'Transaction would be added to Block{index}'}
    return jsonify(response), 201
@app.route('/chain', methods = ['Get'])
def full_chain():
    response = {
        'chain' : blockchain.chain,
        'length' : len(blockchain),
    }
    return jsonify(response), 200
@app.route('/register/node')
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if node is None:
        return "Error: please return a valid list of node", 400
    for node in nodes:
        blockchain.register_node()

    response = {
        'message' : 'New nodes have been added',
        'total_nodes' : list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

