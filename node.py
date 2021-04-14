import block
import aio_pika
import asyncio
import time
import random
import json


class Node:

    def __init__(self, rmq: str = "amqp://guest:guest@localhost/"):
        self.rmq = rmq
        self.transactions = {'testowner': []}
        self.hashes = []
        self.block = None
        self.consumers = {
            'transactions': self.__on_transaction,
            'blocks': self.__on_block,
        }

        self.block_operations = {
            'last_hash': self.__on_last_hash,
            'add_block': self.__on_new_block,
        }

        self.transaction_operations = {
            'register': self.__register_transaction,
            'fetch': self.__fetch_transactions,
            'add_owner': self.__on_add_owner,
        }

        self.__waiting_last_hash = True
        self.loop = asyncio.get_event_loop()
        self.calculate_next = None

    def update_block_data(self):
        self.block.set_data(json.dumps(self.transactions))

    async def __publish(self, exchange, data):
        connection = await aio_pika.connect(
            self.rmq, loop=self.loop
        )
        channel = await connection.channel()
        publish_exchange = await channel.declare_exchange(exchange, aio_pika.ExchangeType.FANOUT)
        message = aio_pika.Message(
            data.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await publish_exchange.publish(message, routing_key="info")
        return connection

    async def __fetch_transactions(self, data):
        owner = data.split()[1]
        print(owner)
        print(self.transactions)
        if self.transactions.get(owner, False):
            connection = await self.__publish(
                'transactions',
                F"client_history {json.dumps(self.transactions.get(owner))}"
            )
            await connection.close()

    async def __on_add_owner(self, owner):
        print("owner data is equal too", owner)
        if not self.transactions.get(owner, False):
            self.transactions[owner.split()[1]] = []
        print(F"added owner {owner.split()[1]}")

    async def __register_transaction(self, data):
        owner, message = data.split()[1:]

        if self.transactions.get(owner, False):
            self.transactions[owner].append(message)
        else:
            self.transactions[owner] = [message]
        self.update_block_data()
        print(F"registered transaction for {owner}")

    async def get_last_hash(self):
        print("Getting hash")
        connection = await self.__publish('blocks', 'last_hash')
        await connection.close()

    async def __on_block(self, message: aio_pika.IncomingMessage):
        print(F"Received block operation {message.body.decode()}")
        async with message.process():
            if self.block_operations.get(message.body.decode().split()[0], False):
                await self.block_operations[message.body.decode().split()[0]](message.body.decode())

    async def __on_new_block(self, message: str):
        print("Adding new node and killing current operation")
        self.calculate_next.cancel()
        self.hashes.append(message.split()[1])
        self.block.set_previous_block_hash(self.hashes[-1])
        self.block.set_data('')
        # done, self.pending = await asyncio.wait(
        #     [self.calculate_next],
        #     return_when=asyncio.FIRST_COMPLETED
        # )
        # calculate_next = asyncio.ensure_future(self.block.calculate_valid_hash())
        # done, pending = await asyncio.wait(
        #     [calculate_next],
        #     return_when=asyncio.FIRST_COMPLETED
        # )

    async def mine(self):
        while True:
            if self.calculate_next and self.calculate_next.done():
                if self.block.hash: await self.pub()
                self.calculate_next = asyncio.create_task(self.block.calculate_valid_hash())
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(0.5)

    async def pub(self):
        new_hash = self.block.hash
        if new_hash in self.hashes: return
        await self.__on_new_block(F"add_block {new_hash}")
        await self.__publish("blocks", F"add_block {new_hash}")

    async def __on_last_hash(self, message: str):
        if self.__waiting_last_hash and len(message.split()) == 2:
            self.__waiting_last_hash = False
            self.hashes.append(message.split()[1])
            self.block = block.Block(previous_block_hash=self.hashes[-1])
            print("calculating new hash for next block")
            # await self.block.calculate_valid_hash()
            # asyncio.ensure_future(self.block.calculate_valid_hash())
            # print("code is executed underneath")
            # self.calculate_next = asyncio.ensure_future(self.block.calculate_valid_hash())
            self.calculate_next = asyncio.create_task(self.block.calculate_valid_hash())
            # while True:
            # await self.calculate_next
            # done, self.pending = await asyncio.wait(
            #     [self.calculate_next],
            #     return_when=asyncio.FIRST_COMPLETED
            # )

            # if not self.calculate_next.cancelled():
            #     new_hash = self.block.hash
            #     await self.__on_new_block(F"add_block {new_hash}")
            #     await self.__publish("blocks", F"add_block {new_hash}")
            # await asyncio.sleep(random.random() * 5)
            # self.calculate_next = asyncio.ensure_future(self.block.calculate_valid_hash())

    async def __on_transaction(self, message: aio_pika.IncomingMessage):
        async with message.process():
            if self.transaction_operations.get(message.body.decode().split()[0], False):
                await self.transaction_operations[message.body.decode().split()[0]](message.body.decode())

    async def __listen_exchange(self, channel: aio_pika.Channel, exchange_name: str):
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.FANOUT)
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange)
        await queue.consume(self.consumers[exchange_name])

    async def __subscriber(self):
        connection = await aio_pika.connect(
            self.rmq, loop=self.loop
        )

        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        await self.__listen_exchange(channel, "transactions")
        await self.__listen_exchange(channel, "blocks")

    async def run(self):
        await self.__subscriber()
        await self.get_last_hash()
        print("waiting for last hash")


if __name__ == "__main__":
    node = Node()
    loop = asyncio.get_event_loop()
    loop.create_task(node.run())
    loop.create_task(node.mine())
    print("Node is running")
    loop.run_forever()
