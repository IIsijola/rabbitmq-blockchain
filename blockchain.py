from async_class import AsyncClass
# from block import block
import block
import aio_pika
import asyncio
import json
import pickle # this is dangerous and is only being done for this demo
import time
import sys


class Blockchain:

    def __init__(self, rmq: str = "amqp://guest:guest@localhost/", join: bool = False):
        self.rmq = rmq
        self.blocks = []
        self.hashes = []
        self.current_transactions = []
        self.consumers = {
            'transactions': self.__on_transactions,
            'history': self.__on_history,
            'blocks': self.__on_block,
        }
        self.transaction_operations = {
            'history': self.__publish_history,
            'register': self.__register_transaction,
        }
        self.block_operations = {
            'last_hash': self.__publish_last_hash,
            'add_block': self.__on_new_block,
        }
        self.join = join
        self.__waiting_history = False
        self.loop = asyncio.get_event_loop()

    def in_the_beginning(self) -> None:
        data = "In the beginning God created the heavens and the earth."
        previous_hash = '0'*64
        genesis_block = block.Block(data=data, previous_block_hash=previous_hash)
        self.blocks.append(genesis_block)

    def get_last_hash(self) -> str:
        hash = self.hashes[-1] if self.hashes else self.blocks[-1].hash
        print("last hash is", hash)
        return hash

    def get_blocks(self) -> list[object]:
        return self.blocks

    async def __register_transaction(self, message: str):
        self.current_transactions.append(message)

    async def __on_transactions(self, message: aio_pika.IncomingMessage):
        async with message.process():
            # print(F"transactions {message.body}")
            # print(message)

            print(message.body.decode())
            if self.transaction_operations.get(message.body.decode().split()[0], False):
                await self.transaction_operations[message.body.decode().split()[0]](message.body.decode())

    async def __on_new_block(self, message: str):
        if message.split()[1] in self.hashes: return
        print(F"Added new block with hash {message.split()[1]} to chain")
        self.blocks.append(block.Block(
            data=json.dumps(self.current_transactions),
            previous_block_hash=message.split()[1]
        ))
        self.hashes.append(message.split()[1])
        self.current_transactions = []

    async def __on_block(self, message: aio_pika.IncomingMessage):
        async with message.process():
            print(F"blocks {message.body.decode()}")
            if self.block_operations.get(message.body.decode().split()[0], False):
                await self.block_operations[message.body.decode().split()[0]](message.body.decode())

    async def __on_history(self, message: aio_pika.IncomingMessage):
        print("in history function")
        if self.__waiting_history:
            self.__waiting_history = False
            async with message.process():
                print("Ingesting history")
                self.blocks = json.loads(message.body.decode())
                print(self.blocks)

    async def __fetch_history(self):
        connection = await aio_pika.connect(
            self.rmq, loop=self.loop
        )
        channel = await connection.channel()
        history_exchange = await channel.declare_exchange('transactions', aio_pika.ExchangeType.FANOUT)
        message_body = b'history'
        message = aio_pika.Message(
            message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await history_exchange.publish(message, routing_key='info')
        print("published transaction history request")
        self.__waiting_history = True

    async def __publish_history(self, dummy):
        print("publishing history")
        connection = await aio_pika.connect(
            self.rmq, loop=self.loop
        )
        channel = await connection.channel()
        history_exchange = await channel.declare_exchange('history', aio_pika.ExchangeType.FANOUT)
        message_body = json.dumps([b.to_string() for b in self.blocks])
        message = aio_pika.Message(
            message_body.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        # time.sleep(5)
        await history_exchange.publish(message, routing_key="my_history")

        await connection.close()

    async def __publish_last_hash(self, message: str):
        # await self.__publish_history()
        if len(message.split()) != 1:
            return
        print('publishing last hash')
        time.sleep(5)
        connection = await self.__publish('blocks', F"last_hash {self.get_last_hash()}")
        await connection.close()

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
        await self.__listen_exchange(channel, "history")
        await self.__listen_exchange(channel, "blocks")

    async def run(self):
        if not self.join:
            self.in_the_beginning()
            asyncio.ensure_future(self.blocks[-1].calculate_valid_hash())
        else:
            await self.__fetch_history()
        await self.__subscriber()


if __name__ == "__main__":
    bc = Blockchain(join=int(sys.argv[1]))
    loop = asyncio.get_event_loop()
    loop.create_task(bc.run())
    print("Blockchain is running")
    loop.run_forever()