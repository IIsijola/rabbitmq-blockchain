from blockchain import Blockchain
from node import Node

import aio_pika
import asyncio
import colored
import json
import sys


class Tester(object):

    def __init__(self, loop):
        self.blockchain = Blockchain(join=False)
        self.number_of_nodes = 1
        self.connection = None
        self.exchange = None
        self.channel = None
        # self.loop = loop
        self.loop = asyncio.get_event_loop()
        self.client = "FakeClient"
        self.client_prescriptions = [ "panadol", "viagra", "fentanyl" ]
        self.node_tasks = []
        self.nodes = []

        try:
            self.blockchain_task = self.loop.create_task(self.blockchain.run())
            print(F"{colored.attr('bold')}{colored.fg(2)}[+] Successfully instantiated blockchain...{colored.attr('reset')}")
        except:
            print(F"{colored.attr('bold')}{colored.fg(2)}[+] Failed to instantiate blockchain...{colored.attr('reset')}")
            sys.exit()

        self.consumers = [
            'transactions',
            # 'history',
            # 'block'
        ]

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

    async def __publish_network(self, exchange, data):
        logs_exchange = await self.channel.declare_exchange(
            exchange, aio_pika.ExchangeType.FANOUT
        )
        message_body = b''.join(x.encode() for x in data)
        message = aio_pika.Message(
            message_body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await logs_exchange.publish(message, routing_key="info")
        print(F"{colored.attr('bold')}{colored.fg(4)}[+] publishing message:{data} to exchange {exchange}{colored.attr('reset')}")

    async def __register_client_and_prescriptions(self):
        print(F"{colored.attr('bold')}{colored.fg(4)}adding prescriptions to blockchain{colored.attr('reset')}")
        await self.__publish_network("transactions", F"add_owner {self.client}")
        for prescription in self.client_prescriptions:
            await self.__publish_network("transactions", F"register {self.client} {prescription}")
        # await self.__publish_network("transactions", )

    async def __listen_exchange(self, channel: aio_pika.Channel, exchange_name: str = "transactions"):
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.FANOUT)
        queue = await channel.declare_queue(exclusive=True)
        if exchange_name in self.consumers:
            await queue.bind(exchange)
            await queue.consume(self.__on_transactions)

    async def __on_transactions(self, message: aio_pika.IncomingMessage):
        async with message.process():
            print("received the following")
            # print(message.body.decode())
            data = ''.join(message.body.decode().split()[1:])
            # print(data)
            try:
                data = json.loads(str(data))
            except json.decoder.JSONDecodeError:
                pass
            print(data)
            if data == self.client_prescriptions:
                print(F"{colored.attr('bold')}{colored.fg(2)}[+] Successfully received prescription{colored.attr('reset')}")
                sys.exit(1)
            else:
                print(F"{colored.attr('bold')}{colored.fg(1)}[!] Failed to received prescriptions{colored.attr('reset')}")
                sys.exit(-1)

    async def __consumer(self, message: aio_pika.IncomingMessage):
        pass

    async def connect(self):
        print(F"{colored.attr('bold')}{colored.fg(2)}[+] Successfully connected to RabbitMQ{colored.attr('reset')}")
        try:
            self.connection = await aio_pika.connect("amqp://guest:guest@localhost/", loop=self.loop)
            self.channel = await self.connection.channel()
        except aio_pika.AMQPException as e:
            print(F"{colored.attr('bold')}{colored.fg(1)}[!] Failed to connect to RabbitMQ{colored.attr('reset')}")
            sys.exit()

    async def run(self):
        await self.connect()
        # await asyncio.sleep(100)

        while not self.blockchain.blocks[-1].hash:
            # print(self.blockchain.blocks[-1].hash)
            await asyncio.sleep(10)

        # print("Exited the while loop")
        # instantiate nodes that we use to test the network
        print(F"{colored.attr('bold')}{colored.fg(4)}[+] Instantiating nodes of blockchain{colored.attr('reset')}")
        self.nodes = [ Node() for i in range(self.number_of_nodes) ]
        self.node_tasks = [ self.loop.create_task(node.run()) for node in self.nodes ]

        # while not all([node.hashes[-1] for node in self.nodes]):
        #     # print(self.nodes[-1].hashes)
        #     print([node.hashes[-1] for node in self.nodes])
        #     print(all([node.hashes[-1] for node in self.nodes]))
        #     await asyncio.sleep(5)

        await asyncio.sleep(10)
        await self.__register_client_and_prescriptions()
        await self.__listen_exchange(self.channel)

        await asyncio.sleep(10)
        await self.__publish_network("transactions", F"fetch {self.client}")

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

    async def cleanup(self):
        await self.connection.close()


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
        loop.create_task(test.cleanup())

