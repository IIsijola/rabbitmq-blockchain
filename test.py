from blockchain import Blockchain
from node import Node

import aio_pika
import asyncio


class Tester(object):

    def __init__(self, loop):
        self.blockchain = Blockchain(join=False)
        self.number_of_nodes = 2
        self.connection = None
        self.exchange = None
        self.channel = None
        self.loop = loop

        self.loop.create_task(self.blockchain.run())

        self.consumers = [
            'transactions',
            'history',
            'block'
        ]

        self.transaction_operations = [
            'register',
            'history',
            'fetch'
        ]

        self.block_operations = [
            'last_block',
            'add_block'
        ]

        # instantiate nodes that we use to test the network
        print("Instantiating the nodes for the blockchain")
        self.nodes = [ Node() for i in range(self.number_of_nodes) ]
        [ self.loop.create_task(node.run()) for node in self.nodes ]

    def reset_network(self):
        print("[+] Resetting network ...")
        self.blockchain = Blockchain(join=False)
        print("[+] Instantiated new instance of blockchain")
        self.nodes = [ Node() for i in range(self.number_of_nodes) ]
        print(F"[+] Instantiated {self.number_of_nodes} nodes for testing")
        [ self.loop.create_task(node.run()) for node in self.nodes ]

    async def make_transaction(self, exchange, data):
        logs_exchange = await self.channel.declare_exchange(
            exchange, aio_pika.ExchangeType.FANOUT
        )
        message_body = b''.join(data.encode())
        message = aio_pika.Message(
            message_body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        await logs_exchange.publish(message, routing_key="info")
        print(F'[+] publishing message:{data} to exchange {exchange}')

    async def __listen_exchange(self, channel: aio_pika.Channel, exchange_name: str):
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.FANOUT)
        queue = await channel.declare_queue(exclusive=True)
        if exchange_name in self.consumers:
            await queue.bind(exchange)
            await queue.consume(self.consumers[exchange_name])

    async def __consumer(self, message: aio_pika.IncomingMessage):
        pass

    async def connect(self):
        print(F'[+] Successfully connected to RabbitMQ')
        try:
            self.connection = await aio_pika.connect("amqp://guest:guest@localhost/", loop=self.loop)
            self.channel = await self.connection.channel()
        except aio_pika.AMQPException as e:
            print("[-] Failed to connect to RabbitMQ")

    async def run(self):
        await self.connect()

        # register consumers
        # make transactions
        # track transactions with consumers

        # if all succeed, tests are passed.

        # four tests :
        #  - test the network connectivity
        #  - test the creation of a blockchain
        #  - test the successful generation of a new hash
        #  - test for success sending of recording of data
        pass

    def __del__(self):
        if self.connection: self.connection.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    test = Tester(loop)
    loop.create_task(test.run())
    print("Tests are running")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("[+] Cleaning up")
        del test

