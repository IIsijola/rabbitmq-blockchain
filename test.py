from blockchain import Blockchain
from node import Node

import aio_pika
import asyncio
import colored


class Tester(object):

    def __init__(self, loop):
        self.blockchain = Blockchain(join=False)
        self.number_of_nodes = 2
        self.connection = None
        self.exchange = None
        self.channel = None
        self.loop = loop

        self.blockchain_task = self.loop.create_task(self.blockchain.run())

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
        self.node_tasks = [ self.loop.create_task(node.run()) for node in self.nodes ]

    def reset_network(self):
        print(F"{colored.attr('bold')}{colored.fg(4)}[+] Resetting network...{colored.attr('reset')}")
        print(F"{colored.attr('bold')}{colored.fg(1)}[!] Cancelling old blockchain{colored.attr('reset')}")
        self.blockchain_task.cancel()
        print(F"{colored.attr('bold')}{colored.fg(1)}[!] Cancelling old nodes{colored.attr('reset')}")
        for task in self.node_tasks: task.cancel()
        self.blockchain = Blockchain(join=False)
        self.blockchain_task = self.loop.create_task(self.blockchain.run())
        print(F"{colored.attr('bold')}{colored.fg(4)}[+] Instantiated new instance of blockchain{colored.attr('reset')}")
        self.nodes = [ Node() for i in range(self.number_of_nodes) ]
        print(F"{colored.attr('bold')}{colored.fg(4)}[+] Instantiated {self.number_of_nodes} nodes for testing{colored.attr('reset')}")
        self.node_tasks = [ self.loop.create_task(node.run()) for node in self.nodes ]

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
        print(F"{colored.attr('bold')}{colored.fg(2)}[+] Successfully connected to RabbitMQ{colored.attr('reset')}")
        try:
            self.connection = await aio_pika.connect("amqp://guest:guest@localhost/", loop=self.loop)
            self.channel = await self.connection.channel()
        except aio_pika.AMQPException as e:
            print(F"{colored.attr('bold')}{colored.fg(1)}[!] Failed to connect to RabbitMQ{colored.attr('reset')}")

    async def run(self):
        await self.connect()
        await asyncio.sleep(10)
        self.reset_network()

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
    print(F"{colored.attr('bold')}{colored.fg(4)}[?] Tests are running{colored.attr('reset')}")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print(F"{colored.attr('bold')}{colored.fg(1)}[!] Received keyboard interrupt{colored.attr('reset')}")
        print(F"{colored.attr('bold')}{colored.fg(2)}[+] Cleaning up{colored.attr('reset')}")
        del test

