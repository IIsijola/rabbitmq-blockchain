## Installation
* First install Rabbitmq since that is the backbone of our system
---
To do this we need to ensure that docker is installed and updated
Then, we run the following command.

```
docker pull rabbitmq:3-management
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
## Demo
That's all that needs to be done regarding the rabbitmq installation.
To guarantee that it's working, visit the [RabbitMQ Management Page](http://localhost:15672/) 
and login using the default credentials ```guest:guest```.
---
* Secondly, we must install all the auxiliary packages used in this demo. 
---  
This can be done easily with the following command ran inside this folder
  
```python3.9 -m pip install requirements.txt```

***Ensure that you are using python3.9 since this demo is reliant on async python***

---
* Thirdly, run ```python3.9 blockchain.py 0``` to get the ball rolling
---
***Ensure that you wait for a genesis hash to be generated for this blockchain before you run anything else***

Though a new blockchain instance can request for the history of the previous, but the implementation of 
that goes beyond the scope of this project.

This is the blockchain itself and can be ran on multiple different machines provided that
the rabbitmq address is available to all of them. This serves 
as the register of the new and previous hashes in our chain.

* After which run ```python3.9 node.py``` in as many terminal windows as you would like
however we've only tested a max of 3 nodes, but best performance will be achieved with 2 concurrent
  nodes running at the same time. These nodes represent the Hospitals/Pharmacies that will be tracking the medical/prescription
  history of patients in their jurisdiction 
  
* Finally, run ```python3.9 sender.py``` which will be used to issue transactions to the blockchain 

The following commands are available 
```
    transactions register <owner> <data>
    transactions fetch <owner>
    transactions add_owner <owner>
    transactions history 

```

* 'register' registers a transaction for an existing <owner> and <data> is what should be store i.e encrypted prescriptions
* 'fetch' fetches all transactions record in all nodes for that owner, this allows us to cross verify validity
* 'add_owner' adds a new owner if the owner does not exist on the node, we do not track their transactions
* 'history' returns the entire transaction history in the blockchain

The suggested flow in the Communication Terminal(```sender.py```) is:
since the owner 'testowner' is an owner that exists in all nodes for testing we can just
run

```
transactions register testowner <test_data>
transactions register testowner <test_data>
transactions register testowner <test_data>

transactions fetch testowner
```

To see everything that is occurring in the blockchain look at the ```blockchain.py``` window since
it prints out everything.

Expected output is 

```
register testowner <data>
register testowner <data>
register testowner <data>

fetch testowner

client_history ["fake", "fake", "fake", "fake"]
client_history ["fake", "fake", "fake", "fake"]


```

the two client_history responses signify the two separate nodes publishing what
they have; We can also dump the entire blockchain history.

We recommend using the abovementioned rabbitmq management console to watch the network
and see all transactions that are taking place


to test the code run
```python3.9 test.py```