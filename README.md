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

_It was a design decision to use the same underlying method for the ```create``` and ```delete``` operations. Usually plugins use different functions. The reason for this diversion from the standard behavior is that both functions are instantiating a "prepared" ```Request``` object with the contents of the operation inputs._


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

Like we said, the _cloudify.nodes.requests.Object_ node type points to the request function in the cloudify_requests package. This function is found in the _cloudify_requests/__init__.py_ file, though it could be found in any module in that package.

**Example**

```python
# cloudify_requests/__init__.py

# cut

@operation
def request(method,
            url=None,
            headers=None,
            files=None,
            data=None,
            json=None,
            params=None,
            auth=None,
            cookies=None,
            hooks=None,
            **_):

    if not url:
        url = build_url_from_endpoint(ctx.node.properties.get('endpoint', {}))

    ctx.logger.debug('url: {0}'.format(url))

    # cut

    try:
        response = session.send(prepped)
    except (RequestException, ConnectionError, HTTPError) as e:
        raise NonRecoverableError('Exception raised: {0}'.format(str(e)))

    # cut

```

> **Explanation**
> In this Python code, we see all the basics of Cloudify plugin development.
> First we imported Cloudify's developer context as ```ctx```. We also imported an operation decorator, which injects the ```ctx``` into our python function. We also imported a special Exception class, ```NonRecoverableError``` that we can use to tell Cloudify that a workflow has failed.
> Then comes the request function. I've cut out most of the logic for brevity, but the following steps are included to understand some Cloudify development features.
> * ```ctx.node.properties.get('endpoint', {})```: We use the ```ctx``` here to access the properties that we defined in our node type.
> * ```ctx.logger.debug('url: {0}'.format(url))```: Sometimes it is useful to include some logging so that users can see what the plugin has done with their input. Available levels are ```info```, ```debug```, ```warning```, and ```error```.
> * ```raise NonRecoverableError('Exception raised: {0}'.format(str(e)))```: If the request failed, we want to exit the workflow, so we raise the ```NonRecoverableError```.

If you are curious the plugin code has further comments.


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
      version: 0.0.1.dev3
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

Run the install workflow:

```shell

$ cfy install ~/Environments/Examples/cloudify-requests-plugin/resources/test-blueprint.yaml -i "{'path': ['hdw743hd73h']}"
Processing inputs source: {'path': ['hdw743hd73h']}
2017-04-04 14:58:41 CFY <local> Starting 'install' workflow execution
2017-04-04 14:58:42 CFY <local> [cloudify_7hgqbt] Creating node
2017-04-04 14:58:42 CFY <local> [cloudify_7hgqbt.create] Sending task 'cloudify_requests.request'
2017-04-04 14:58:42 CFY <local> [cloudify_7hgqbt.create] Task started 'cloudify_requests.request'
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: Building url from endpoint.
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: url: http://requestb.in/hdw743hd73h
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: headers: {}
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: files: None
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: data: {u'blueprint': u'test-blueprint.yaml', u'version': u'0.0.1.dev3', u'plugin': u'cloudify-requests-plugin'}
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: json: None
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: params: {}
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: auth (keys): []
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: cookies: {}
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] DEBUG: hooks: {}
2017-04-04 14:58:42 LOG <local> [cloudify_7hgqbt.create] INFO: Request OK: {'body': 'blueprint=test-blueprint.yaml&version=0.0.1.dev3&plugin=cloudify-requests-plugin', 'status_code': 200, 'content': 'ok'}
2017-04-04 14:58:42 CFY <local> [cloudify_7hgqbt.create] Task succeeded 'cloudify_requests.request'
2017-04-04 14:58:42 CFY <local> [cloudify_7hgqbt] Configuring node
2017-04-04 14:58:43 CFY <local> [cloudify_7hgqbt] Starting node
2017-04-04 14:58:43 CFY <local> 'install' workflow execution succeeded
```

Run the uninstall workflow:

```shell
$ cfy local execute -w uninstall -vv
2017-04-04 14:58:46 CFY <local> Starting 'uninstall' workflow execution
2017-04-04 14:58:46 CFY <local> [cloudify_7hgqbt] Stopping node
2017-04-04 14:58:47 CFY <local> [cloudify_7hgqbt] Deleting node
2017-04-04 14:58:47 CFY <local> [cloudify_7hgqbt.delete] Sending task 'cloudify_requests.request'
2017-04-04 14:58:47 CFY <local> [cloudify_7hgqbt.delete] Task started 'cloudify_requests.request'
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: Building url from endpoint.
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: url: http://requestb.in/hdw743hd73h
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: headers: {}
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: files: None
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: data: {u'blueprint': u'test-blueprint.yaml', u'version': u'0.0.1.dev3', u'plugin': u'cloudify-requests-plugin'}
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: json: None
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: params: {}
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: auth (keys): []
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: cookies: {}
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] DEBUG: hooks: {}
2017-04-04 14:58:47 LOG <local> [cloudify_7hgqbt.delete] INFO: Request OK: {'body': 'blueprint=test-blueprint.yaml&version=0.0.1.dev3&plugin=cloudify-requests-plugin', 'status_code': 200, 'content': 'ok'}
2017-04-04 14:58:47 CFY <local> [cloudify_7hgqbt.delete] Task succeeded 'cloudify_requests.request'
2017-04-04 14:58:47 CFY <local> 'uninstall' workflow execution succeeded
```


## Executing the Github Issue Blueprint Example

Run the install workflow:

```shell

$ cfy install ~/Environments/Examples/cloudify-requests-plugin/resources/test-github-blueprint.yaml -i "
auth: { 'username': 'myusername', 'password': 'mypassword' }
'issue_title': 'We want more features'
'issue_body': 'Some examples: Intelligently decide between passing configuration to data, json, or params.'
"
2017-04-04 14:48:37 CFY <local> Starting 'install' workflow execution
2017-04-04 14:48:37 CFY <local> [github_issue_r1x1iu] Creating node
2017-04-04 14:48:37 CFY <local> [github_issue_r1x1iu.create] Sending task 'cloudify_requests.request'
2017-04-04 14:48:38 CFY <local> [github_issue_r1x1iu.create] Task started 'cloudify_requests.request'
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: Building url from endpoint.
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: url: https://api.github.com/repos/earthmant/cloudify-requests-plugin/issues
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: headers: {u'User-Agent': u'cloudify-requests-plugin'}
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: files: None
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: data: None
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: json: {u'body': u'Some examples: Intelligently decide between passing configuration to data, json, or params.', u'title': u'We want more features'}
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: params: {}
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: auth (keys): [u'username', u'password']
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: cookies: {}
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] DEBUG: hooks: {}
2017-04-04 14:48:38 LOG <local> [github_issue_r1x1iu.create] INFO: Request OK: {'body': '{"body": "Some examples: Intelligently decide between passing configuration to data, json, or params.", "title": "We want more features"}', 'status_code': 201, 'content': '{"url":"https://api.github.com/repos/EarthmanT/cloudify-requests-plugin/issues/3","repository_url":"https://api.github.com/repos/EarthmanT/cloudify-requests-plugin","labels_url":"https://api.github.com/repos/EarthmanT/cloudify-requests-plugin/issues/3/labels{/name}","comments_url":"https://api.github.com/repos/EarthmanT/cloudify-requests-plugin/issues/3/comments","events_url":"https://api.github.com/repos/EarthmanT/cloudify-requests-plugin/issues/3/events","html_url":"https://github.com/EarthmanT/cloudify-requests-plugin/issues/3","id":219224312,"number":3,"title":"We want more features","user":{"login":"EarthmanT","id":9653571,"avatar_url":"https://avatars1.githubusercontent.com/u/9653571?v=3","gravatar_id":"","url":"https://api.github.com/users/EarthmanT","html_url":"https://github.com/EarthmanT","followers_url":"https://api.github.com/users/EarthmanT/followers","following_url":"https://api.github.com/users/EarthmanT/following{/other_user}","gists_url":"https://api.github.com/users/EarthmanT/gists{/gist_id}","starred_url":"https://api.github.com/users/EarthmanT/starred{/owner}{/repo}","subscriptions_url":"https://api.github.com/users/EarthmanT/subscriptions","organizations_url":"https://api.github.com/users/EarthmanT/orgs","repos_url":"https://api.github.com/users/EarthmanT/repos","events_url":"https://api.github.com/users/EarthmanT/events{/privacy}","received_events_url":"https://api.github.com/users/EarthmanT/received_events","type":"User","site_admin":false},"labels":[],"state":"open","locked":false,"assignee":null,"assignees":[],"milestone":null,"comments":0,"created_at":"2017-04-04T11:48:38Z","updated_at":"2017-04-04T11:48:38Z","closed_at":null,"body":"Some examples: Intelligently decide between passing configuration to data, json, or params.","closed_by":null}'}
2017-04-04 14:48:38 CFY <local> [github_issue_r1x1iu.create] Task succeeded 'cloudify_requests.request'
2017-04-04 14:48:39 CFY <local> [github_issue_r1x1iu] Configuring node
2017-04-04 14:48:39 CFY <local> [github_issue_r1x1iu] Starting node
2017-04-04 14:48:40 CFY <local> 'install' workflow execution succeeded
```

**No uninstall workflow is defined in the github example.**


## Testing Plugins

There are two kinds of tests in plugins:

* unit tests: test particular functions
* workflow tests: test workflows

Together these tests should cover over 90% of the Python plugin code.

We also require that the plugin Python code passes ```flake8``` validation.
