# -*- coding: utf-8 -*-
# Copyright 2017-2018 theloop Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import asyncio
import shutil
import unittest

from tbears.util import make_install_json_payload
from tbears.util.icon_client import get_deploy_payload
from tbears.util.tbears_mock_server import API_PATH, init_mock_server, fill_json_content

from tbears.command import init_SCORE, run_SCORE, make_SCORE_samples
from tests.common import *
from tests.test_tbears_samples import test_addr

token_score_name = 'sample_token'
token_score_class = 'SampleToken'
crowd_score_name = 'sample_crowd_sale'


class TestDeployScore(unittest.TestCase):

    def tearDown(self):

        try:
            if os.path.exists('sample_token'):
                shutil.rmtree('sample_token')
            if os.path.exists('./.test_tbears_db'):
                shutil.rmtree('./.test_tbears_db')
            if os.path.exists('./.score'):
                shutil.rmtree('./.score')
            if os.path.exists('./.db'):
                shutil.rmtree('./.db')
            os.remove('./tbears.log')
        except:
            pass

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.path = API_PATH
        self.app = init_mock_server()

    def test_call_token_score(self):
        init_SCORE(token_score_name, token_score_class)
        run_payload = make_install_json_payload('sample_token')
        _, response = self.app.test_client.post(self.path, json=run_payload)

        deploy_payload = get_deploy_payload(token_score_name, token_owner_signer)
        payload = fill_json_content(SEND, deploy_payload)
        _, response = self.app.test_client.post(self.path, json=payload)
        res_json = response.json
        tx_hash = res_json['result']

        transaction_result_payload = get_request_of_icx_getTransactionResult(tx_hash=tx_hash)
        payload = fill_json_content(TX_RESULT, transaction_result_payload)

        _, response = self.app.test_client.post(self.path, json=payload)
        score_address = response.json['result']['scoreAddress']
        params = get_request_json_of_token_total_supply(score_address)
        payload = fill_json_content(CALL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']

        self.assertEqual(hex(1000 * 10 ** 18), result)

        params = get_request_json_of_get_token_balance(score_address, deploy_token_owner_address)
        payload = fill_json_content(CALL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']

        self.assertEqual(hex(1000 * 10 ** 18), result)

        params = get_request_json_of_transfer_token(deploy_token_owner_address, score_address, god_address,
                                                     hex(10 * 10 ** 18))
        payload = fill_json_content(SEND, params)
        self.app.test_client.post(self.path, json=payload)

        params = get_request_json_of_get_token_balance(score_address, god_address)
        payload = fill_json_content(CALL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        self.assertEqual(hex(10 * 10 ** 18), result)

    def test_call_score_methods(self):
        make_SCORE_samples()

        deploy_payload = get_deploy_payload(token_score_name, token_owner_signer)
        payload = fill_json_content(SEND, deploy_payload)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        tx_hash = response_json['result']
        transaction_result_payload = get_request_of_icx_getTransactionResult(tx_hash)
        payload = fill_json_content(TX_RESULT, transaction_result_payload)

        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        token_score_address = response_json['result']['scoreAddress']

        crowd_deploy_payload = get_deploy_payload(crowd_score_name, token_owner_signer,
                                                  params={'token_address': token_score_address})
        payload = fill_json_content(SEND, crowd_deploy_payload)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        tx_hash = response_json['result']

        transaction_result_payload = get_request_of_icx_getTransactionResult(tx_hash)
        payload = fill_json_content(TX_RESULT, transaction_result_payload)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        crowd_sale_score_address = response_json['result']['scoreAddress']

        # seq1
        # genesis -> token_owner 10icx
        params = get_request_json_of_send_icx(fr=god_address, to=deploy_token_owner_address, value=hex(10 * 10 ** 18))
        payload = fill_json_content(SEND, params)

        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        tx_hash = response_json['result']
        params = get_request_of_icx_getTransactionResult(tx_hash=tx_hash)
        payload = fill_json_content(TX_RESULT, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        self.assertEqual(result['status'], hex(1))

        # seq2
        # check icx balance of token_owner value : 10*10**18
        params = get_request_json_of_get_icx_balance(address=deploy_token_owner_address)
        payload = fill_json_content(BAL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        self.assertEqual(result, hex(10 * 10 ** 18))

        # seq3
        # check token balance token_owner. value : 1000*10**18
        params = get_request_json_of_get_token_balance(to=token_score_address,
                                                        addr_from=deploy_token_owner_address)
        payload = fill_json_content(CALL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        self.assertEqual(result, hex(1000 * 10 ** 18))

        # seq4
        # transfer token to CrowdSale_address. value: 1000*10**18
        params = get_request_json_of_transfer_token(fr=deploy_token_owner_address,
                                                    to=token_score_address,
                                                    addr_to=crowd_sale_score_address,
                                                    value=hex(1000 * 10 ** 18))
        payload = fill_json_content(SEND, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        params = get_request_of_icx_getTransactionResult(tx_hash=result)
        payload = fill_json_content(TX_RESULT, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        status = result['status']
        self.assertEqual(status, hex(1))

        # seq5
        # check token balance of CrowdSale_address. value : 1000*10**18
        params = get_request_json_of_get_token_balance(to=token_score_address,
                                                       addr_from=crowd_sale_score_address)
        payload = fill_json_content(CALL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        self.assertEqual(result, hex(1000 * 10 ** 18))

        # seq6
        # check token balance of token_owner. value : 0
        params = get_request_json_of_get_token_balance(to=token_score_address, addr_from=deploy_token_owner_address)
        payload = fill_json_content(CALL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        self.assertEqual(result, hex(0))

        # seq7
        # transfer icx to CrowdSale. value : 2*10**18
        params = get_request_json_of_send_icx(fr=deploy_token_owner_address,
                                              to=crowd_sale_score_address, value=hex(2 * 10 ** 18))
        payload = fill_json_content(SEND, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        tx_hash = response_json['result']
        params = get_request_of_icx_getTransactionResult(tx_hash=tx_hash)
        payload = fill_json_content(TX_RESULT, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        status = result['status']
        self.assertEqual(status, hex(1))

        # seq8
        # check icx balance of token_owner. value : 8*10**18
        params = get_request_json_of_get_icx_balance(address=deploy_token_owner_address)
        payload = fill_json_content(BAL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        self.assertEqual(result, hex(8 * 10 ** 18))

        # seq9
        # check token balance of token_owner. value : 0x2
        params = get_request_json_of_get_token_balance(to=token_score_address,
                                                       addr_from=deploy_token_owner_address)
        payload = fill_json_content(CALL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        self.assertEqual(result, hex(2))

        # seq10
        # transfer icx to CrowdSale. value : 8*10**18
        params = get_request_json_of_send_icx(fr=deploy_token_owner_address,
                                              to=crowd_sale_score_address,
                                              value=hex(8 * 10 ** 18))
        payload = fill_json_content(SEND, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        tx_hash = response_json['result']
        params = get_request_of_icx_getTransactionResult(tx_hash=tx_hash)
        payload = fill_json_content(TX_RESULT, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        status = result['status']
        self.assertEqual(status, hex(1))

        # seq11
        # genesis -> test_address. value 90*10**18
        params = get_request_json_of_send_icx(fr=god_address, to=test_addr, value=hex(90 * 10 ** 18))
        payload = fill_json_content(SEND, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        tx_hash = response_json['result']
        params = get_request_of_icx_getTransactionResult(tx_hash=tx_hash)
        payload = fill_json_content(TX_RESULT, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        status = result['status']
        self.assertEqual(status, hex(1))

        # seq12
        # transfer icx to CrowdSale. value : 90*10**18
        params = get_request_json_of_send_icx(fr=test_addr, to=crowd_sale_score_address, value=hex(90 * 10 ** 18))
        payload = fill_json_content(SEND, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        tx_hash = response_json['result']
        params = get_request_of_icx_getTransactionResult(tx_hash=tx_hash)
        payload = fill_json_content(TX_RESULT, params)

        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        status = result['status']
        self.assertEqual(status, hex(1))

        # seq13
        # check CrowdSaleEnd
        params = get_request_json_of_check_crowd_end(fr=deploy_token_owner_address,
                                                      to=crowd_sale_score_address)
        payload = fill_json_content(SEND, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        tx_hash = response_json['result']
        params = get_request_of_icx_getTransactionResult(tx_hash=tx_hash)
        payload = fill_json_content(TX_RESULT, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        status = result['status']
        self.assertEqual(status, hex(1))

        # # seq14
        # safe withrawal
        params = get_request_json_of_crowd_withrawal(fr=deploy_token_owner_address, to=crowd_sale_score_address)
        payload = fill_json_content(SEND, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        tx_hash = response_json['result']
        params = get_request_of_icx_getTransactionResult(tx_hash=tx_hash)
        payload = fill_json_content(TX_RESULT, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        status = result['status']
        self.assertEqual(status, hex(1))

        # seq15
        # check icx balance of token_owner value : 100*10**18
        params = get_request_json_of_get_icx_balance(address=deploy_token_owner_address)
        payload = fill_json_content(BAL, params)
        _, response = self.app.test_client.post(self.path, json=payload)
        response_json = response.json
        result = response_json['result']
        self.assertEqual(result, hex(100 * 10 ** 18))
