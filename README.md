# cloudify-requests-plugin
==========================

A Cloudify plugin that is useful both for interacting with generic APIs and as an example for writing custom plugins.

## Plugin directory structure

Like all Cloudify plugins, this plugin is a Python project.

Therefore it must comprise a _setup.py_ file and a python package. Additionally, you should provide a plugin.yaml so that the plugin can be imported in Cloudify blueprints.

```shell
.
├── README.md # A readme that describes usage.
├── cloudify_requests # the python package
│   ├── __init__.py # __init__.py file, a fundamental requirement of a python package.
├── plugin.yaml # A plugin yaml for Cloudify DSL import validation.
└── setup.py # a python project setup.py.
```

