from block.blockchain import Blockchain
from block.node import Node

from aio_pika import connect, Message, DeliveryMode, ExchangeType, AMQPException
import asyncio

class Tester(object):
    number_of_nodes = 2
    exchange = None
    connection = None
    channel = None
    loop = None

    def __init__(self, loop):
        self.blockchain = Blockchain()
        self.nodes = []
        self.loop = loop

        for i in range(self.number_of_nodes):
            self.nodes.append(Node())

    def make_transaction(self, exchange, data):
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

    def connect(self):
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



