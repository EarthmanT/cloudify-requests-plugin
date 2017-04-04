# cloudify-requests-plugin
==========================

A Cloudify plugin for making HTTP requests.

**Note:**
_This plugin is intended as an example._
It also works! Like this plugin, most plugins are wrappers around some technology. Most frequently, a plugin will be based on the Python bindings for a particular API, such as AWS (boto), Openstack (novaclient-python), Docker (docker-py), etc. Also a plugin is frequently based on a generic library such as fabric, subprocess or requests. This plugin is kept generic, although another plugin based on requests might make design decisions to better support a specific target API.
**Please read this README completely for instructions on writing your own plugin.**


## Plugin directory structure

Like all Cloudify plugins, this plugin is a Python project.

Therefore it must comprise a _setup.py_ file and a python package.

Additionally, you should provide a plugin.yaml, so that the plugin can be imported in Cloudify blueprints.

Below is the minimum required directory structure for a Cloudify plugin:

```shell
.
├── README.md # A readme that describes usage.
├── cloudify_requests # the python package
│   ├── __init__.py # __init__.py file, a fundamental requirement of a python package.
├── (plugin.yaml)[#Contents of plugin.yaml] # A plugin yaml for Cloudify DSL import validation.
└── setup.py # a python project setup.py.
```

Over time your directory structure will naturally become more complex, but this is the basis.



### Contents of plugin.yaml

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

## Python Code Operation Mapping

Like we said, the _cloudify.nodes.requests.Object_ node type points to the post and delete operations in the cloudify_requests package. These functions are found in the _cloudify_requests/__init__.py_ file.

```python
# cloudify_requests/__init__.py

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

## Blueprint Examples

It is a good idea to publish in the plugin repository any blueprints that you use to test the functionality of your plugin.

These go in the resources folder.

```yaml
# resources/test-blueprint.yaml
tosca_definitions_version: cloudify_dsl_1_3

imports:
  - http://www.getcloudify.org/spec/cloudify/4.0/types.yaml
  - ../plugin.yaml

inputs:

  protocol:
    default: http

  domain:
    default: requestb.in

  path:
    default:
      - # Place the API code that you received from requestb.in after the dash (-) #

  resource_configuration:
    default:
      plugin: cloudify-requests-plugin
      version: 0.0.1.dev2
      blueprint: test-blueprint.yaml

node_templates:

  cloudify:
    type: cloudify.nodes.requests.Object
    properties:
      endpoint:
        protocol: { get_input: protocol }
        domain: { get_input: domain }
        path: { get_input: path }
      configuration: { get_input: resource_configuration }
```
