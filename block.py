from hashlib import sha256
import typing
import asyncio

import random


class Block:

    def __init__(self, previous_block_hash: str, data: typing.Optional[str] = None) -> None:
        self.data = data
        self.hash = None
        self.previous_block_hash = previous_block_hash

    def set_data(self, data: str):
        self.data = data

    def set_hash(self, block_hash):
        self.hash = block_hash

    def set_previous_block_hash(self, previous_block_hash):
        self.previous_block_hash = previous_block_hash

    @staticmethod
    def is_valid_hash(calculated_hash: str) -> bool:
        # return calculated_hash.startswith('0000')
        return '777' in calculated_hash

    async def calculate_valid_hash(self) -> None:
        calculated_hash = ''
        nonce = 0

        while not self.is_valid_hash(calculated_hash):
            if not self.data:
                await asyncio.sleep(20)
                continue
            print("hash", calculated_hash)
            temp = self.to_string() + str(nonce)
            calculated_hash = sha256(temp.encode()).hexdigest()
            nonce += 1
            await asyncio.sleep(random.random())

        print("found valid hash", calculated_hash)
        self.hash = calculated_hash

    def to_string(self) -> str:
        return F"{self.data}\t{self.previous_block_hash}"
