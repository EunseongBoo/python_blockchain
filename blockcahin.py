import hashlib
import datetime as date
import json
import matplotlib.pyplot as plt
from time import time
from threading import Thread
from threading import Lock
from time import sleep

class Blockchain():
    def __init__(self, miner_name):
      self.chain = []
      self.balance = dict()
      self.lock = Lock() # for multithreading
      
      #Create the genesis block
      block,tx_num = self.new_block(0, miner_name)
      self.insert_block(block,tx_num)
      print('miner {} generate the genesis block'.format(miner_name))
      
    def new_block(self,index, miner_name = None):
          #새로운 block 생성
          #block 구조: block hash + block header + transactions + nonce
          tx_list = self.generate_coinbase_transaction(miner_name) + self.current_transactions 
          tx_num = len(tx_list)
          
          blockheader = {
            'index': index,
            'timestamp': time(),
            'previous_hash': self.get_previous_hash(),
            'transactions_hash': self.transactions_hash(tx_list)
          }

          #find nonce
          nonce = self.proof_of_work(blockheader);
          
          block = {
            'block_hash': self.calculate_block_hash(nonce,blockheader),
            'header': blockheader,
            'transactions': tx_list,
            'nonce': nonce
          } 
           
          return block,tx_num 
     
    def get_previous_hash(self):
        if(len(self.chain) == 0):
            return 0
        else:
            return self.chain[-1]['block_hash']
        
    def generate_coinbase_transaction(self, miner_name):
        #채굴자는 항상 자신이 생성하는 블록의 첫번째 거래에 coinbase transaction을 생성해서 넣음
        #coinbase transaction을 통해 새로운 코인이 생성되고, 이는 채굴자에게 보상으로 돌아감
        amount = 250 # 보상 금액
        return [{'miner': miner_name, 'amount': amount}]
    
    def new_transaction(self, sender, receiver, amount, data):
          #새로운 거래 발생 시 현재 거래리스트에 추가
          #등록될 블록 인덱스 반환
          self.current_transactions.append({
            'sender': sender,
            'receiver':receiver,
            'amount': amount,
            'data': data
          })
          return len(self.chain)+1
        
    def transactions_hash(self,tx_list):
        if len(tx_list) == 0:
            return 0
        tx_hash_list = []

        for tx in tx_list:
            tx_hash_list.append(self.calculate_tx_hash(tx))
        
        sha = hashlib.sha256()
        tx_hash_all = tx_hash_list[0]
        for tx_hash in tx_hash_list[1:]:
            tx_hash_all += tx_hash
        sha.update(tx_hash_all.encode('utf-8'))
        return sha.hexdigest()
    
    def calculate_tx_hash(self,tx):
        tx_string = json.dumps(tx, sort_keys=True).encode()
        return hashlib.sha256(tx_string).hexdigest()

    def calculate_block_hash(self,nonce,bh):
        sha = hashlib.sha256()                
        sha.update(str(nonce).encode('utf-8')+str(bh['index']).encode('utf-8')+str(bh['timestamp']).encode('utf-8')
               +str(bh['previous_hash']).encode('utf-8')+str(bh['transactions_hash']).encode('utf-8'))
        return sha.hexdigest()
        
    def proof_of_work(self,bh):
        # 앞자리수 5개가 0이 되는 hash 값을 찾을 때까지 nonce값을 증가시키면서 해쉬값 계산
        nonce = 0   
        while (1):
            hash_value = self.calculate_block_hash(nonce,bh);
            if hash_value[0:5] == '00000':
              print ("find hash value " + hash_value)
              break
            nonce += 1
        return nonce
    
    def insert_block(self,block,tx_num):
        #생성한 블락을 블록체인에 연결
        #블락이 유효하지 않을 시 블락을 버림
        #멀티 쓰레딩을 위한 lock 사용
        self.lock.acquire()
        
        if self.validate_block(block) == False:
            self.lock.release()
            return False
        
        self.current_transactions = self.current_transactions[tx_num:] #block에 포함된 tx들은 현재 tx에서 삭제
        self.chain.append(block) # 블록체인에 block 연결
        self.balance_update(block) #잔고 업데이트
        
        self.lock.release()
        return True
    
    def validate_block(self,block):
        #계산한 블락이 유효한지 검사
        if block['block_hash'][0:5] != '00000':
            print ('throwing out the block, validate_block error 1')
            return False
        if block['header']['index'] == 0:
            return True
        if block['header']['index'] != len(self.chain):
            print ('throwing out the block, block #{} is already created'.format(block['header']['index']))
            return False
        if block['header']['previous_hash'] != self.chain[-1]['block_hash']:
            print ('throwing out the block, validate_block error 3')
            return False
        return True
    
    def balance_update(self,block):
        # coinbase 트랜잭션을 위한 balance update
        miner = block['transactions'][0]['miner']
        amount = block['transactions'][0]['amount']
        if miner in self.balance:
            self.balance[miner] += amount
        else:
            self.balance.update({miner:amount})
            
        # 나머지 트랜잭션들을 위한 balance update    
        for tx in block['transactions'][1:]:
            sender = tx['sender']
            receiver = tx['receiver']
            amount = tx['amount']
        return 


class miner():
    def __init__(self,miner_name, Blockchain = None):
        self.name = miner_name
        self.blockchain = Blockchain
            
    def mining(self):
        index = len(self.blockchain.chain)
        block,tx_num = self.blockchain.new_block(index,self.name)
        if self.blockchain.insert_block(block,tx_num) == True:
            print ("miner {} generate the #{} block!".format(self.name,index))
            print (self.blockchain.balance)
            
def miner_thread(name,blockchain):
    m = miner(name,blockchain)
    while(1):
        m.mining()

def show_balance(balance):
    
    plt.bar(range(len(balance)), list(balance.values()), align='center')
    plt.xticks(range(len(balance)),list(balance.keys()))
    plt.pause(0.5)
    plt.draw()

def show_balance_first(balance):
    
    plt.bar(range(len(balance)), list(balance.values()), align='center')
    plt.xticks(range(len(balance)),list(balance.keys()))
    plt.pause(0.5)
    plt.show(block=False)
    
def main():
    threads = []
    miner_num = 0;
    miner_list = ['A','B','C','D','E']
    blockchain = Blockchain(miner_name = 'A') #블록체인의 genesis block 생성, 생성자는 miner 'A'
    
    for i in range(5):
        t = Thread(target=miner_thread, args=(miner_list[i],blockchain))
        threads.append(t)
        
    for t in threads:
        t.start()
   
    #Balance 정보가 담겨있는 장부를 그래프로 보여줌
    show_balance_first(blockchain.balance)  
    while(1):
        show_balance(blockchain.balance)
        sleep(5)

if __name__ == '__main__':
    main()

 

    
