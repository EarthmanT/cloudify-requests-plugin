########
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# Built-in Imports
from requests.auth import HTTPBasicAuth
import testtools
from cloudify.state import current_ctx

# Third Party Imports
import mock
from cloudify.mocks import MockCloudifyContext
from cloudify.exceptions import NonRecoverableError

from cloudify.test_utils import workflow_test


class TestCloudifyRequests(testtools.TestCase):

    def get_mock_ctx(self,
                     test_name,
                     test_properties):
        """ Creates a mock context for the base
            tests
        """
        test_node_id = test_name
        test_properties = test_properties

        ctx = MockCloudifyContext(
            node_id=test_node_id,
            deployment_id=test_name,
            properties=test_properties
        )

        ctx.node.type_hierarchy = ['cloudify.nodes.Root']

        return ctx

    def test_create_auth_object_from_data_type(self):
        from .. import create_auth_object_from_data_type
        auth_no_username = {
            'user name': 'username',
            'password': 'password'
        }
        self.assertRaises(NonRecoverableError,
                          create_auth_object_from_data_type,
                          auth_no_username)
        auth_no_password = {
            'username': 'username',
            'pass word': 'password'
        }
        self.assertRaises(NonRecoverableError,
                          create_auth_object_from_data_type,
                          auth_no_password)
        auth_dict = {
            'username': 'username',
            'password': 'password'
        }
        auth = HTTPBasicAuth(**auth_dict)
        output = create_auth_object_from_data_type(auth_dict)
        self.assertEqual(auth, output)

    def test_create_files_dictionary_from_files_list(self):
        from .. import create_files_dictionary_from_files_list
        test_name = 'test_create_files_dictionary_from_files_list'
        test_properties = {
            'endpoint': {},
            'configuration': ''
        }
        _ctx = self.get_mock_ctx(test_name,
                                 test_properties)
        current_ctx.set(_ctx)

        test_files_none = [{
            'filename': 'test_file'
        }]
        error = self.assertRaises(NonRecoverableError,
                                  create_files_dictionary_from_files_list,
                                  test_files_none)
        self.assertIn('Neither an url, nor a path was provided.',
                      error.message)

        test_files_filename = [{}]
        error = self.assertRaises(NonRecoverableError,
                                  create_files_dictionary_from_files_list,
                                  test_files_filename)
        self.assertIn('Improperly formatted file in ',
                      error.message)

        test_files_url = [{
            'filename': 'test_file',
            'url': 'http://www.example.com/images/image.png'
        }]
        error = self.assertRaises(NonRecoverableError,
                                  create_files_dictionary_from_files_list,
                                  test_files_url)
        self.assertIn('No implementation for downloading a file',
                      error.message)

        test_files_path = [{
            'filename': 'test_file',
            'path': 'resources/image.png'
        }]
        error = self.assertRaises(RuntimeError,
                                  create_files_dictionary_from_files_list,
                                  test_files_path)
        self.assertIn('Available resources: []', error.message)

        test_files_path2 = [{
            'filename': 'test_file',
            'path': 'resources/image.png'
        }]
        test_files_path2_expected = {'test_file': True}
        with mock.patch('cloudify.ctx.download_resource') as \
                download_resource:
            download_resource.return_value = True
            output = \
                create_files_dictionary_from_files_list(test_files_path2)
        self.assertEqual(test_files_path2_expected, output)

    def test_build_url_from_endpoint(self):
        from .. import build_url_from_endpoint
        test_name = 'test_build_url_from_endpoint'
        test_properties = {
            'endpoint': {},
            'configuration': ''
        }
        _ctx = self.get_mock_ctx(test_name,
                                 test_properties)
        current_ctx.set(_ctx)
        endpoint_test1 = {
            'protocol': 'https',
            'domain': 'www.example.com',
            'path': ['api', 'v2', 'users', 'username']
        }
        url = build_url_from_endpoint(endpoint_test1)
        url_expected_test1 = \
            'https://www.example.com/api/v2/users/username'
        self.assertEquals(url_expected_test1, url)

        endpoint_test1 = {
            'protocol': 'https',
            'domain': 'www.example.com',
            'path': ['api', 'v2', 'users', 'username/accounts/personal']
        }
        url = build_url_from_endpoint(endpoint_test1)
        url_expected_test2 = \
            'https://www.example.com/api/v2/users/username/accounts/personal'
        self.assertEquals(url_expected_test2, url)

    @workflow_test('blueprints/test.yaml',
                   copy_plugin_yaml=True)
    def test_my_task(self, cfy_local):
        error = self.assertRaises(
            RuntimeError,
            cfy_local.execute,
            'install',
            task_retries=0
        )
        self.assertIn('404 - Not Found', error.message)

        with mock.patch('requests.Session.send') as session_send:
            session_send_mock = mock.MagicMock
            session_send_mock_request = mock.MagicMock
            setattr(session_send_mock, 'status_code', 'ok')
            setattr(session_send_mock, 'ok', 1)
            setattr(session_send_mock_request, 'body', {})
            setattr(session_send_mock_request, 'content', {})
            setattr(session_send_mock, 'request', session_send_mock_request)
            session_send.return_value = session_send_mock
            cfy_local.execute('install',
                              task_retries=0)
