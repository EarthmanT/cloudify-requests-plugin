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
import testtools
from cloudify.state import current_ctx

# Third Party Imports
import mock
from cloudify.mocks import MockCloudifyContext, MockContext
from cloudify.exceptions import NonRecoverableError, RecoverableError


class TestRequests(testtools.TestCase):

    def get_mock_ctx(self, test_name, retry_number=0):
        """ Creates a mock context for the base
            tests
        """
        test_node_id = test_name
        test_properties = {}

        operation = {
            'retry_number': retry_number
        }

        ctx = MockCloudifyContext(
            node_id=test_node_id,
            deployment_id=test_name,
            properties=test_properties,
            operation=operation,
            provider_context={'resources': {}}
        )

        ctx.node.type_hierarchy = ['cloudify.nodes.Root']

        return ctx

    def mock_relationship_context(self, testname):

        source_context = MockContext({
            'node': MockContext({
                'properties': {}
            }),
            'instance': MockContext({
                'runtime_properties': {}
            })
        })

        target_context = MockContext({
            'node': MockContext({
                'properties': {}
            }),
            'instance': MockContext({
                'runtime_properties': {}
            })
        })

        relationship_context = MockCloudifyContext(
            node_id=testname, source=source_context,
            target=target_context)

        setattr(relationship_context.source.node,
                'type_hierarchy',
                ['cloudify.nodes.Root', 'cloudify.nodes.Root']
                )

        return relationship_context

    def test_base_operation_functions(self):
        ctx = self.get_mock_ctx('test_base_operation_functions')
        current_ctx.set(ctx=ctx)

