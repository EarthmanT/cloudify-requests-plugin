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

from requests import Request, Session
from requests import RequestException, ConnectionError, HTTPError
from requests.auth import HTTPBasicAuth

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError


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
    """
    execute requests for cloudify-request-plugin operations

    The following parameters are used to build the prepared request object.

    :param method:
    :param url:
    :param headers:
    :param files:
    :param data:
    :param json:
    :param params:
    :param auth:
    :param cookies:
    :param hooks:
    :param _:
    :return:
    """

    # If a URL was passed to the function it will override the endpoint.
    if not url:
        url = build_url_from_endpoint(ctx.node.properties.get('endpoint', {}))

    ctx.logger.debug('url: {0}'.format(url))

    ctx.logger.debug('headers: {0}'.format(headers))

    # transform the list of files into a dictionary of files as required.
    files_dictionary = \
        None if not files else create_files_dictionary_from_files_list(files)

    ctx.logger.debug('files: {0}'.format(files_dictionary))

    # configuration is translated as data
    data = data if data else ctx.node.properties.get('configuration')

    ctx.logger.debug('data: {0}'.format(data))

    json = json if json else None

    ctx.logger.debug('json: {0}'.format(json))

    ctx.logger.debug('params: {0}'.format(params))

    # transform the cloudify.datatypes.auth structure
    # to a requests auth object
    auth_object = None if not auth else create_auth_object_from_data_type(auth)

    ctx.logger.debug('auth (keys): {0}'.format(auth.keys()))

    ctx.logger.debug('cookies: {0}'.format(cookies))

    ctx.logger.debug('hooks: {0}'.format(hooks))

    req = Request(method,
                  url,
                  headers=headers,
                  files=files_dictionary,
                  data=data,
                  json=json,
                  params=params,
                  auth=auth_object,
                  cookies=cookies,
                  hooks=hooks)

    prepped = req.prepare()
    session = Session()

    try:
        response = session.send(prepped)
    except (RequestException, ConnectionError, HTTPError) as e:
        raise NonRecoverableError('Exception raised: {0}'.format(str(e)))

    result = {
        'status_code': response.status_code,
        'body': response.request.body,
        'content': response.content
    }

    if not response.ok:
        raise NonRecoverableError('Request failed: {0}'.format(result))

    ctx.logger.info('Request OK: {0}'.format(result))


def build_url_from_endpoint(endpoint):
    """
    create the url from the cloudify.datatypes.uri structure.

    :param endpoint:
    :return:
    """

    ctx.logger.debug('Building url from endpoint.')

    protocol = endpoint.get('protocol')
    domain = endpoint.get('domain')
    path = endpoint.get('path')
    _url = '{0}://{1}'.format(protocol,
                              domain)
    for path_item in path:
        _url = '{0}/{1}'.format(_url,
                                path_item)
    return _url


def create_files_dictionary_from_files_list(_files):
    """
    Transform the list of files into a dict of files.

    :param _files: list of cloudify.datatypes.file data structures.
    :return:
    """

    _file_dictionary = {}

    for _file in _files:

        _filename = _file.get('filename')
        if not _filename:
            raise NonRecoverableError(
                'Improperly formatted file in list of cloudify.datatypes.file')

        if _file.get('path'):
            _fileobject = ctx.download_resource(_file.get('path'))
        elif _file.get('url'):
            raise NonRecoverableError(
                'No implementation for downloading a file.')
        else:
            raise NonRecoverableError(
                'Neither an url, nor a path was provided.')

        _file_dictionary.update({_filename: _fileobject})

    return _file_dictionary


def create_auth_object_from_data_type(_auth):
    """
    Build an auth object.
    Right now only requests.auth.HTTPBasicAuth object is supported.

    :param _auth: a dict containing username and password.
    :return: HTTPBasicAuth object.
    """
    username = _auth.get('username')
    password = _auth.get('password')
    if not username or not password:
        raise NonRecoverableError(
            'Improperly formatted cloudify.datatypes.auth data.')
    return HTTPBasicAuth(username, password)
