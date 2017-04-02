
import requests

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError


@operation
def post(data, **_):

    endpoint = ctx.node.properties.get('endpoint')
    data = ctx.node.properties.get('configuration') or data

    response = requests.post(endpoint, data=data)

    if not response.ok:
        raise NonRecoverableError('Failed: {0}'.format(response.content))

    create_result = {
        'status_code': response.status_code,
        'content': response.content
    }

    ctx.instance.runtime_properties['create'] = create_result

    ctx.logger.info('OK: {0}'.format(response.content))


@operation
def delete(**_):

    endpoint = ctx.node.properties.get('endpoint')

    response = requests.delete(endpoint)

    if not response.ok:
        raise NonRecoverableError('Failed: {0}'.format(response.content))

    delete_result = {
        'status_code': response.status_code,
        'content': response.content
    }

    ctx.instance.runtime_properties['create'] = delete_result

    ctx.logger.info('OK: {0}'.format(response.content))
