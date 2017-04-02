
from requests import Request, Session

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError


@operation
def request(method, data=None, **_):

    last_result = ctx.instance.runtime_properties.get('last_result')

    s = Session()

    endpoint = ctx.node.properties.get('endpoint')

    protocol = endpoint.get('protocol')
    domain = endpoint.get('domain')
    path = endpoint.get('path')

    url = '{0}://{1}'.format(protocol,
                             domain)
    for path_item in path:
        url = '{0}/{1}'.format(url,
                               path_item)

    data = data or last_result or ctx.node.properties.get('configuration')

    ctx.logger.info('URL: {0}'.format(url))
    ctx.logger.info('DATA: {0}'.format(data))

    req = Request(method,
                  url,
                  data=data)

    prepped = req.prepare()

    response = s.send(prepped)

    result = {
        'status_code': response.status_code,
        'body': response.request.body,
        'content': response.content
    }

    if not response.ok:
        raise NonRecoverableError('Failed: {0}'.format(result))

    ctx.instance.runtime_properties['last_result'] = result

    ctx.logger.info('OK: {0}'.format(result))
