# cloudify-requests-plugin
==========================

A Cloudify plugin for making HTTP requests.

**Please read this README completely for instructions on writing your own plugin.**

_This plugin is intended as an example._
It also works! Like this plugin, most plugins are wrappers around some Python library (or libraries). Most frequently, a plugin will be based on the Python bindings for a particular API, such as AWS (boto), Openstack (novaclient-python), Docker (docker-py), etc. Also a plugin is frequently based on a generic library such as fabric, subprocess or requests. Since this plugin is primarily an example, it's kept as generic as possible. However, other plugins, including those based on the ```requests``` library are usually less generic in their implementation in order to provide a better UX for the technology they are trying to support.


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
├── plugin.yaml # A plugin yaml for Cloudify DSL import validation.
└── setup.py # a python project setup.py.
```

### The setup.py file

The ```setup.py``` contains the setup method from setuptools. It should at the very least provide:

* The ```name``` of the plugin. This should follow the convention cloudify-[project-name]-plugin.
* The ```author```. This should be either your name or your team's name.
* The ```author_email```. This is where users can turn for information about support, legal, etc.
* The ```version```. This should be kept up to date.
* The ```description```. Something short.
* A list of ```packages``` in the plugin. More about this (below)[#plugin-packages].
* A list of required libraries in ```install_requires```. Anything that is not shipped with Python.


**Example:**

```python

from setuptools import setup

setup(
    name='cloudify-requests-plugin',
    author='Cloudify by Gigaspaces',
    author_email='hello@getcloudify.com',
    version='0.0.1.dev0',
    description='Cloudify plugin for HTTP Requests.',
    packages=['cloudify_requests'],
    install_requires=['cloudify-plugins-common>=4.0', 'requests>=2.13.0']
)

```

### plugin packages

The plugin Python code is contained in Python packages. These should be named according to the convention cloudify_[project-name]. Sometimes your plugin might have several packages. In such advanced scenarios, you should take into consideration that the Python package will be stored in a library with other Python packages and referenced by name. Do your best to avoid naming conflicts.


### plugin.yaml

The _plugin.yaml_ is the interaction between the Cloudify DSL and the plugin Python code.

The most critical section is the ```plugins``` definition. Other frequently used sections are ```node_types```, ```relationships```, ```data_types```, and ```workflows```.


#### plugins definition

The essential feature of the _plugin.yaml_ file is the plugins definition.

It has the following format:

```yaml
plugins:
  requests:
    executor: central_deployment_agent
```

> Here, ```requests``` is the project-name. The ```executor``` specifies which Cloudify agent will execute the plugin. The _central_deployment_agent_ indicates that the if the plugin is executed by a Cloudify Manager, then the worker agent on the manager will execute. If we use ```host_agent``` instead, then the agent worker on a managed host would execute the code.

**Note:** The ```host_agent``` executor is not recognized in _cfy local_.


#### node_types

A _node type_ is used to define resource types, which are then _derived_by_ other ```node_types```, or they may be used in blueprints by ```node_templates```.

The _node type_ also defines the which properties might be expected.

A _node type_ has the following keys:

* ```derived_from```: This is another base _node type_.
* ```properties```: These are properties that we expect this _node type_ to make use of. These can be ```required``` or not (if the _node type_ doesn't say that it's required, then it's not.
* ```interfaces```: This is how we map to plugin operations in the Python code.

> **Explanation:**
> This is how we bridge the markup language of the YAML Cloudify DSL and the Python functional programming of Cloudify plugins.


**Example:**

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
      cloudify.interfaces.lifecycle:
        create:
          implementation: requests.cloudify_requests.request
          inputs:
            method:
              default: POST
            data:
              default: {}
        delete:
          implementation: requests.cloudify_requests.request
          inputs:
            method:
              default: DELETE
```

> **Explanation:**
> Two properties are defined for the _cloudify.nodes.requests.Object_ node type:
>
> * ```endpoint```: Endpoint is validated by the _cloudify.datatypes.URI_ data type. (More about this later.)
> * ```configuration``` has no type validation, but has a default value - an empty dictionary.
>
> Two _cloudify.interfaces.lifecycle_ operations are defined as well, which are both mapped to the same Python function ```request```.
>
> * ```create``` expects two inputs, _method_ and _data_, which have default values provided.
> * ```delete``` expects only one input _method_.

_It was a design decision to use the same underlying method for the ```create``` and ```delete``` operations. Usually plugins use different functions. The reason for this diversion from the standard behavior is that both functions are instantiating a ```Request``` object with the contents of the operation inputs._


#### data_types

Data types are used to provide Cloudify DSL validation to complex data structures (basically, meaning not an int or a string).

This is useful for a number of scenarios:

* The property expects a property with specific keys.
* Extra documention about the property.
* Providing input for data that when instantiated by a Python object, are not JSON serializable.

In the example above, the _cloudify.nodes.requests.Object_ node type ```endpoint``` property is validated by the _cloudify.datatypes.UI_ data types. This data type defines the anatomy of a URI:


```yaml
  cloudify.datatypes.URI:
    properties:
      protocol:
        description: >
          The protocol.
        type: string
        default: 'http'
      domain:
        description: >
          The domain.
        type: string
        required: true
      path:
        description: >
          Additional paths.
      default: []
```

> **Explanation:**
> Three properties are defined for the _cloudify.datatypes.URI_ data type:
>
> * ```protocol```: This is generally going to be _http_ or _https_.
> * ```domain```: This is the domain such as _api.github.com_.
> * ```path```: For example, ```[user, repo]```.



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
