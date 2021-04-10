from block.blockchain import Blockchain
from block.node import Node

from aio_pika import connect, Message, DeliveryMode, ExchangeType, AMQPException
import asyncio


class Tester(object):

    def __init__(self, loop):
        self.blockchain = Blockchain(join=False)
        self.number_of_nodes = 2
        self.connection = None
        self.exchange = None
        self.channel = None
        self.loop = loop

        # instantiate nodes that we use to test the network
        self.nodes = [ Node() for i in range(self.number_of_nodes) ]

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

    def reset_network(self):
        print("[+] Resetting network ...")
        self.blockchain = Blockchain(join=False)
        print("[+] Instantiated new instance of blockchain")
        self.nodes = [ Node() for i in range(self.number_of_nodes) ]
        print(F"[+] Instantiated {self.number_of_nodes} nodes for testing")

    async def make_transaction(self, exchange, data):
        logs_exchange = await self.channel.declare_exchange(
            exchange, ExchangeType.FANOUT
        )
        message_body = b''.join(data.encode())
        message = Message(
            message_body,
            delivery_mode=DeliveryMode.PERSISTENT
        )

        await logs_exchange.publish(message, routing_key="info")
        print(F'[+] publishing message:{data} to exchange {exchange}')

    async def connect(self):
        print(F'[+] Successfully connected to RabbitMQ')
        try:
            self.connection = await connect(
                "amqp://guest:guest@localhost/", loop=self.loop
            )

            self.channel = await self.connection.channel()
        except AMQPException as e:
            print("[-] Failed to connect to RabbitMQ")

    async def run(self):
        pass

    def __del__(self):
        if self.connection: self.connection.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    test = Tester(loop)
    loop.create_task(test.run())
    print("Tests are running")
    loop.run_forever()



