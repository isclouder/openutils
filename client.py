'''
'''
import json
import urllib2

class Opthttp(object):
    def __init__(self, controller=None, username=None, passwd=None, timeout=10):
        self.token = None
        self.tenant = None
        self.timeout = timeout
        if username and passwd:
            self.token, self.tenant = self.__get_token(controller, username, passwd)

    def __get_token(self, controller, username, passwd):
        url = 'http://%s:5000/v2.0/tokens' %controller
        values = {"auth": {"tenantName": "admin", "passwordCredentials": {"username": username, "password": passwd}}}
        data = self.http_post(url, values)
        token = data['access']['token']['id']
        tenant = data['access']['token']['tenant']['id']
        return token, tenant

    def http_get(self, url, version=None):
        req = urllib2.Request(url)
        if version:
            req.add_header('X-OpenStack-Nova-API-Version', version)
        if self.token:
            req.add_header('X-Auth-Token', self.token)
        if self.timeout:
            response = urllib2.urlopen(req, timeout=self.timeout)
        else:
            response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        data = json.loads(data)
        return data

    def _do_http_post(self, method, url, body, version=None):
        if body:
            jdata = json.dumps(body)
            req = urllib2.Request(url, jdata)
        else:
            req = urllib2.Request(url, None)
        if version:
            req.add_header('X-OpenStack-Nova-API-Version', version)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Accept', 'application/json')
        if self.token:
            req.add_header('X-Auth-Token', self.token)
        req.get_method = lambda: method
        if self.timeout:
            response = urllib2.urlopen(req, timeout=self.timeout)
        else:
            response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        if data != '':
            data = json.loads(data)
        return data

    def http_post(self, url, body):
        return self._do_http_post('POST', url, body)

    def http_put(self, url, body):
        return self._do_http_post('PUT', url, body)

    def http_delete(self, url, body):
        return self._do_http_post('DELETE', url, body)

class Neutron(Opthttp):
    def __init__(self, controller=None, username=None, passwd=None, timeout=None):
        self.baseurl = 'http://%s:9696/v2.0' %controller
        super(Neutron, self).__init__(controller, username, passwd, timeout)

    def find_resource_id_by_name(self, resource, name):
        url = '%s/%s.json?fields=id&name=%s' %(self.baseurl, resource, name)
        id = self.http_get(url)
        return id

    def router_list(self):
        url = '%s/routers.json' %(self.baseurl)
        list = self.http_get(url)
        return list

    def router_show(self, id):
        url = '%s/routers/%s.json' %(self.baseurl, id)
        info = self.http_get(url)
        return info

    def router_port_list(self, id):
        url = '%s/ports.json?device_id=%s' %(self.baseurl, id)
        list = self.http_get(url)
        return list

    def router_create(self, name):
        url = '%s/routers.json' %(self.baseurl)
        body = {'router': {'name': name, 'admin_state_up': True}}
        ret = self.http_post(url, body)
        return ret

    def router_delete(self, id):
        url = '%s/routers/%s.json' %(self.baseurl, id)
        body = None
        ret = self.http_delete(url, body)
        return ret

    def router_gateway_set(self, id, extnet_info):
        url = '%s/routers/%s.json' %(self.baseurl, id)
        body = {'router': {'external_gateway_info': extnet_info}}
        ret = self.http_put(url, body)
        return ret

    def router_gateway_clear(self, id):
        url = '%s/routers/%s.json' %(self.baseurl, id)
        body = {'router': {'external_gateway_info': {}}}
        ret = self.http_put(url, body)
        return ret

    def router_interface_add(self, id, subnet_id):
        url = '%s/routers/%s/add_router_interface.json' %(self.baseurl, id)
        body = {'subnet_id': subnet_id}
        ret = self.http_put(url, body)
        return ret

    def router_interface_delete(self, id, subnet_id):
        url = '%s/routers/%s/remove_router_interface.json' %(self.baseurl, id)
        body = {'subnet_id': subnet_id}
        ret = self.http_put(url, body)
        return ret

    def port_list(self):
        url = '%s/ports.json' %(self.baseurl)
        list = self.http_get(url)
        return list

    def port_show(self, id):
        url = '%s/ports/%s.json' %(self.baseurl, id)
        info = self.http_get(url)
        return info

    def port_delete(self, id):
        url = '%s/ports/%s.json' %(self.baseurl, id)
        body = None
        ret = self.http_delete(url, body)
        return ret

    def agent_list(self):
        url = '%s/agents.json' %(self.baseurl)
        list = self.http_get(url)
        return list

    def agent_delete(self, id):
        url = '%s/agents/%s.json' %(self.baseurl, id)
        body = None
        ret = self.http_delete(url, body)
        return ret

class Nova(Opthttp):
    def __init__(self, controller=None, username=None, passwd=None, timeout=None):
        super(Nova, self).__init__(controller, username, passwd, timeout)
        self.baseurl = 'http://%s:8774/v2.1/%s' %(controller,self.tenant)

    def get_server_list(self):
        url = '%s/servers/detail' %(self.baseurl)
        list = self.http_get(url)
        return list
