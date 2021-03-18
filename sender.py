import sys
import asyncio
from aio_pika import connect, Message, DeliveryMode, ExchangeType


async def main(loop):
    connection = await connect(
        "amqp://guest:guest@localhost/", loop=loop
    )
    print("Communication Terminal")
    print("type exit to quit")

    while True:
        # Creating a channel
        channel = await connection.channel()

        my_input = input("Enter operations <exchange> <data>: ")
        exchange = my_input.split()[0]
        if exchange == 'exit':
            break

        logs_exchange = await channel.declare_exchange(
            exchange, ExchangeType.FANOUT
        )

        my_input = ' '.join(my_input.split()[1:])

        message_body = b''.join(
            arg.encode() for arg in my_input) or b"Hello World!"

        message = Message(
            message_body,
            delivery_mode=DeliveryMode.PERSISTENT
        )

        # Sending the message
        await logs_exchange.publish(message, routing_key="info")

        print(" [x] Sent %r" % message.body)

    await connection.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
