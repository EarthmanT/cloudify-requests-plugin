# cloudify-requests-plugin
==========================

A Cloudify plugin that is useful both for interacting with generic APIs and as an example for writing custom plugins.

## Plugin directory structure

Like all Cloudify plugins, this plugin is a Python project.

Therefore it must comprise a _setup.py_ file and a python package.

Additionally, you should provide a plugin.yaml, so that the plugin can be imported in Cloudify blueprints.

```shell
.
├── README.md # A readme that describes usage.
├── cloudify_requests # the python package
│   ├── __init__.py # __init__.py file, a fundamental requirement of a python package.
├── plugin.yaml # A plugin yaml for Cloudify DSL import validation.
└── setup.py # a python project setup.py.
```

## Contents of plugin.yaml

The _plugin.yaml_ is the interaction between the Cloudify DSL and the plugin Python code.

#### plugins definition

The essential feature of the plugin.yaml file is the plugins definition.

```yaml
plugins:
  req:
    executor: central_deployment_agent
```

#### node_types

A _node type_ is used to define resource types, which are then used in blueprints as _node templates_. The node type maps to plugin operations in the Python code. The node type also defines the which properties might be expected.

```yaml
  cloudify.nodes.requests.Object:
    derived_from: cloudify.nodes.Root
    properties:
      endpoint:
        description: The API object endpoint.
        type: cloudify.datatypes.URI
        required: true
      configuration:
        description: >
          The configuration of the API Resource that you are managing.
          No validation is provided for the cloudify.nodes.requests.Object type.
        default: {}
    interfaces:
      cloudify.lifecycle.interfaces:
        create:
          implementation: req.cloudify_requests.post
          inputs:
            data:
              default: {}
        delete:
          implementation: req.cloudify_requests.delete
```

In this _cloudify.nodes.requests.Object_, we say that the code for the create and delete operations is in the cloudify_requests package under the post and delete operations. We also add an expected input _data_ for the post operation.

We also give the _cloudify.nodes.requests.Object node type two expected properties: _endpoint_ and _configuration_. The _endpoint_ property has a data type validation, while the _configuration property has no validation other than that its default value is an empty dictionary.

#### Operation Mapping

Like we said, the _cloudify.nodes.requests.Object_ node type points to the post and delete operations in the cloudify_requests package. These functions are found in the _cloudify_requests/__init__.py_ file.

```python
import requests

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

@operation
def post(data, **_):

    endpoint = ctx.node.properties.get('endpoint')
    data = data or ctx.node.properties.get('configuration')
    response = requests.post(endpoint, data=data)

    if not response.ok:
        raise NonRecoverableError('Failed: {0}'.format(response.content))

    create_result = {
        'status_code': response.status_code,
        'content': response.content
    }

    ctx.instance.runtime_properties['create'] = create_result

    ctx.logger.info('OK: {0}'.format(response.content))
```

In this Python code, we see all the basics of Cloudify plugin development.

First we imported Cloudify's developer context. We also imported an operation decorator, which injects the developer context into our python function. We also imported a special Exception class that we can use to tell Cloudify that a workflow has failed.

Then comes the Python function. We access the node properties from the Cloudify CTX using _ctx.node.properties_. We take endpoint from there. We first check the data from the arguments to the function. If that's not available, we will take it from the node properties.
