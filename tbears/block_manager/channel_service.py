# Copyright 2017-2018 theloop Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from typing import Tuple, TYPE_CHECKING, Optional

from iconcommons import IconConfig
from iconcommons.logger import Logger
from earlgrey import MessageQueueService, message_queue_task

from tbears.block_manager import message_code
from tbears.util import create_hash

if TYPE_CHECKING:
    from earlgrey import RobustConnection
    from tbears.block_manager.block_manager import BlockManager


class ChannelInnerTask(object):
    """Message queue

    """

    def __init__(self, conf: 'IconConfig', block_manager: 'BlockManager'):
        self._conf = conf
        self._block_manager = block_manager
        self.confirmed_tx_list = list()

    @message_queue_task
    async def create_icx_tx(self, kwargs: dict) -> Tuple[int, Optional[str]]:
        Logger.debug(f'Get create_tcx_tx message!! {kwargs}', "create_icx_tx")
        block_manager = self._block_manager

        # generate tx hash
        tx_hash = create_hash(json.dumps(kwargs).encode())

        # check duplication
        duplicated_tx = False
        for tx_tuple in block_manager.get_tx():
            if tx_hash == tx_tuple[0]:
                duplicated_tx = True
        if duplicated_tx is False and block_manager._block.get_transaction(tx_hash=tx_hash):
            duplicated_tx = True

        if duplicated_tx:
            return message_code.Response.fail_tx_invalid_duplicated_hash, None

        # append to transaction queue
        block_manager.add_tx(tx_hash=tx_hash, tx=kwargs)

        Logger.debug(f'Resposne create_icx_tx!!', "create_icx_tx")
        return message_code.Response.success, f"0x{tx_hash}"

    @message_queue_task
    async def get_invoke_result(self, tx_hash: str) -> Tuple[int, str]:
        Logger.debug(f'Get getTransactionResult tx_hash: {tx_hash}')
        block = self._block_manager._block

        tx_data_json = block.get_txresult(tx_hash=tx_hash)
        if tx_data_json is None:
            return message_code.Response.fail_tx_not_invoked, {}

        return message_code.Response.success, tx_data_json

    @message_queue_task
    async def get_tx_info(self, tx_hash: str) -> Tuple[int, dict]:
        Logger.debug(f'Get getTransactionByHash tx_hash: {tx_hash}')
        block = self._block_manager._block

        tx_data_json = block.get_transaction(tx_hash=tx_hash)
        if tx_data_json is None:
            return message_code.Response.fail_tx_invalid_hash_not_match, {}

        return message_code.Response.success, tx_data_json

    @message_queue_task
    async def get_block(self, block_height: int, block_hash: str, block_data_filter: str, tx_data_filter: str)\
            -> Tuple[int, str, str, list]:
        Logger.debug(f'Get get_block message block_height: {block_height}, block_hash: {block_hash}', "block")
        block = self._block_manager._block

        fail_response_code: int = None

        if block_hash == "" and block_height == -1:
            # getLastBlock
            block_data_json = block.get_last_block()
            if block_data_json is None:
                fail_response_code = message_code.Response.fail_wrong_block_hash
        elif block_hash:
            # getBlockByHash
            block_data_json = block.get_block_by_hash(block_hash=block_hash)
            if block_data_json is None:
                fail_response_code = message_code.Response.fail_wrong_block_hash
        else:
            # getBlockByHeight
            block_data_json = block.get_block_by_height(block_height=block_height)
            if block_data_json is None:
                fail_response_code = message_code.Response.fail_wrong_block_height

        if fail_response_code:
            return fail_response_code, block_hash, "", []

        block_hash: str = block_data_json['block_hash']
        block_data_json_str: str = json.dumps(block_data_json)

        # tbears block_manager does not support filters

        Logger.debug(f'Response block!!', "block")
        return message_code.Response.success, block_hash, block_data_json_str, []


class ChannelService(MessageQueueService[ChannelInnerTask]):
    TaskType = ChannelInnerTask

    def _callback_connection_lost_callback(self, connection: 'RobustConnection'):
        # FIXME
        exit(1)
