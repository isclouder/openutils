
import os
import commands
from openutils import config

dbopt = {
         "keystone":  [{"sysuser": "keystone",  "dbname": "keystone",  "dbpasswd": config.KEYSTONE_DBPASS,  "dbsync": "keystone-manage db_sync"}],
         "glance":    [{"sysuser": "glance",    "dbname": "glance",    "dbpasswd": config.GLANCE_DBPASS,    "dbsync": "glance-manage db_sync"}],
         "nova":      [
                       {"sysuser": "nova",      "dbname": "nova_api",  "dbpasswd": config.NOVAAPI_DBPASS,   "dbsync": "nova-manage api_db sync"},
                       {"sysuser": "nova",      "dbname": "nova",      "dbpasswd": config.NOVA_DBPASS,      "dbsync": "nova-manage db sync"}
                      ],
         "neutron":   [{"sysuser": "neutron",   "dbname": "neutron",   "dbpasswd": config.NEUTRON_DBPASS,   "dbsync": "neutron-db-manage --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head"}],
         "cinder":    [{"sysuser": "cinder",    "dbname": "cinder",    "dbpasswd": config.CINDER_DBPASS,    "dbsync": "cinder-manage db sync"}]
        }

serviceopt ={
              "glance": [{"name":"glance",   "type":"image",    "description":"OpenStack Image",         "http":"http://%s:9292" % config.CONTROLLER_HOSTNAME}],
              "nova":   [{"name":"nova",     "type":"compute",  "description":"OpenStack Compute",       "http":"http://%s:8774/v2.1/%%\(tenant_id\)s" % config.CONTROLLER_HOSTNAME}],
              "neutron":[{"name":"neutron",  "type":"network",  "description":"OpenStack Networking",    "http":"http://%s:9696" % config.CONTROLLER_HOSTNAME}],
              "cinder": [
                         {"name":"cinder",   "type":"volume",   "description":"OpenStack Block Storage", "http":"http://%s:8776/v1/%%\(tenant_id\)s" % config.CONTROLLER_HOSTNAME},
                         {"name":"cinderv2", "type":"volumev2", "description":"OpenStack Block Storage", "http":"http://%s:8776/v2/%%\(tenant_id\)s" % config.CONTROLLER_HOSTNAME}
                        ]
             }

admin_env ={
             "OS_USERNAME": "admin",
             "OS_PASSWORD": config.ADMIN_PASS,
             "OS_PROJECT_NAME": "admin",
             "OS_USER_DOMAIN_NAME": "Default",
             "OS_PROJECT_DOMAIN_NAME": "Default",
             "OS_AUTH_URL": "http://%s:35357/v3" % config.CONTROLLER_HOSTNAME,
             "OS_IDENTITY_API_VERSION": "3",
             "OS_IMAGE_API_VERSION": "2"
           }

def exec_cmd(cmd):
    print "==>: " + cmd
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        raise Exception("[%s] \nCommand exec error: %s" % (cmd, output))

def create_db(dbs):
    for db in dbs:
        try:
            sql = "DROP DATABASE %s; " % db['dbname']
            cmd = "mysql -uroot -p%s -e \"%s\"" % (config.MYSQL_PASS, sql)
            exec_cmd(cmd)
        except Exception as e:
            pass

        sql = "CREATE DATABASE %s; " % db['dbname'] + \
              "GRANT ALL PRIVILEGES ON %s.* TO '%s'@'localhost' IDENTIFIED BY '%s'; " % (db['dbname'], db['sysuser'], db['dbpasswd']) + \
              "GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%%' IDENTIFIED BY '%s'" % (db['dbname'], db['sysuser'], db['dbpasswd'])
        cmd = "mysql -uroot -p%s -e \"%s\"" % (config.MYSQL_PASS, sql)
        exec_cmd(cmd)

        cmd = "su -s /bin/sh -c \"%s\" %s" % (db['dbsync'], db['sysuser'])
        exec_cmd(cmd)


def keystone_init():
    cmd = "keystone-manage fernet_setup --keystone-user keystone --keystone-group keystone; " + \
          "keystone-manage credential_setup --keystone-user keystone --keystone-group keystone; " + \
          "keystone-manage bootstrap --bootstrap-password %s " % config.ADMIN_PASS + \
          "--bootstrap-admin-url http://%s:35357/v3/ " % config.CONTROLLER_HOSTNAME + \
          "--bootstrap-internal-url http://%s:35357/v3/ " % config.CONTROLLER_HOSTNAME + \
          "--bootstrap-public-url http://%s:5000/v3/ " % config.CONTROLLER_HOSTNAME + \
          "--bootstrap-region-id RegionOne"
    exec_cmd(cmd)

def create_project_service():
    cmd = "openstack project create --domain default --description \"Service Project\" service"
    exec_cmd(cmd)

def create_user_and_service(user,passwd):
    def __create_service(services):
        for service in services:
            cmd = "openstack service create --name %s --description \"%s\" %s; " %(service['name'], service['description'],service['type']) + \
                  "openstack endpoint create --region RegionOne %s public %s; " %(service['type'], service['http']) + \
                  "openstack endpoint create --region RegionOne %s internal %s; " %(service['type'], service['http']) + \
                  "openstack endpoint create --region RegionOne %s admin %s " %(service['type'], service['http'])
            exec_cmd(cmd)
        
    cmd = "openstack user create --domain default --password %s %s" % (passwd, user)
    exec_cmd(cmd)
    cmd = "openstack role add --project service --user %s admin" % user
    exec_cmd(cmd)
    __create_service(serviceopt[user])


def print_result():
    os.environ.update(admin_env)
    cmd = "openstack token issue ; " + \
          "openstack project list; " + \
          "openstack service list; " + \
          "openstack endpoint list "
    os.system(cmd)

def deploy(name):
    if name == 'all':
        create_db(dbopt['keystone'])
        keystone_init()
        os.environ.update(admin_env)
        create_project_service()
        create_user_and_service('glance', config.GLANCE_PASS)
        create_user_and_service('nova', config.NOVA_PASS)
        create_user_and_service('neutron', config.NEUTRON_PASS)
        create_user_and_service('cinder', config.CINDER_PASS)

    os.environ.update(admin_env)
    if name == 'all' or name == 'glance':
        create_db(dbopt['glance'])
    if name == 'all' or name == 'nova':
        create_db(dbopt['nova'])
    if name == 'all' or name == 'neutron':
        create_db(dbopt['neutron'])
    if name == 'all' or name == 'cinder':
        create_db(dbopt['cinder'])

    print_result()

