from __future__ import with_statement
import os, sys

#DEV_NULL = open(os.devnull, 'w')
#STDOUT_ORIG = sys.stdout
#STDERR_ORIG = sys.stderr

#sys.stderr = DEV_NULL

# Import Fabric's API module
from fabric.api import *
from fabric.contrib.console import confirm

#sys.stderr = STDERR_ORIG

def hello(name="Abhishek"):
    print >>sys.stdout, "Hello {name}!\n".format(name=name)

# Fabfile to:
#    - update the remote system(s) 
#    - download and install an application

env.skip_bad_hosts = True
env.eagerly_disconnect = True
env.colorize_errors = True
#env.abort_on_prompts = True

env.hosts = [
    '172.16.15.201',
    '172.16.15.202',
    '172.16.15.203',
    '172.16.15.204',
    '172.16.15.205',
    '172.16.15.206',
    '172.16.15.207',
    '172.16.15.208',
    '172.16.15.209',
    '172.16.15.210',
    '172.16.15.211',
    '172.16.15.212',
    '172.16.15.213',
#    '172.16.15.214',
#    '172.16.15.215',
  # 'ip.add.rr.ess
  # 'server2.domain.tld',
]
# Set the username
env.user   = "root"
#env.user   = "abhishek"

# Set the password [NOT RECOMMENDED]
env.password = "centos6"
#env.password = "qwerty"


'''
env.passwords = {
    'root@172.16.15.202': 'centos6',
}
'''
'''
(Pdb) dir(result)
['__add__', '__class__', '__contains__', '__delattr__', '__dict__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__getnewargs__', '__getslice__', '__gt__', '__hash__', '__init__', '__le__', '__len__', '__lt__', '__mod__', '__module__', '__mul__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__rmod__', '__rmul__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '_formatter_field_name_split', '_formatter_parser', 'capitalize', 'center', 'command', 'count', 'decode', 'encode', 'endswith', 'expandtabs', 'failed', 'find', 'format', 'index', 'isalnum', 'isalpha', 'isdigit', 'islower', 'isspace', 'istitle', 'isupper', 'join', 'ljust', 'lower', 'lstrip', 'partition', 'real_command', 'replace', 'return_code', 'rfind', 'rindex', 'rjust', 'rpartition', 'rsplit', 'rstrip', 'split', 'splitlines', 'startswith', 'stderr', 'stdout', 'strip', 'succeeded', 'swapcase', 'title', 'translate', 'upper', 'zfill']
'''

def add_ssh_keys():
    with settings(warn_only=True):
        for host in env.hosts:
            #print >>sys.stderr, local("ssh abhishek@{0}".format(host))
            print >>sys.stderr, local("ssh-copy-id -i /home/abhishek/.ssh/id_rsa.pub abhishek@{0}".format(host))
        '''
        print >>sys.stderr, run("mkdir /home/abhishek/.ssh")
        print >>sys.stderr, put("/home/abhishek/.ssh/id_rsa.pub", "/home/abhishek/.ssh/authorized_keys")
        '''
    
def task_log_777():
    print >>sys.stderr, run("chmod 777 /var/log/task_queue/*").return_code

def stat_epel_repo():
    result = run("ls -l /etc/yum.repos.d/epel.repo", shell=True)
    print >>sys.stdout, "Result: ", result

@hosts('172.16.15.214')
def put_epel_rpm():
    with cd("/home/abhishek/Downloads"):
        result = put("/home/abhishek/Downloads/epel-release-6-8.noarch.rpm", "~/")
    print >>sys.stdout, "Result: ", result

#@hosts('172.16.15.203' )
def root_passwd():
    with settings(warn_only=True):
        result = run("passwd", shell=True)    
    print >>sys.stdout, "Result: ", result

def hostname():
    with settings(warn_only=True):
        result = run("hostname", shell=False, timeout=10)    
    print >>sys.stdout, "Result: ", result

def yum_download_epel():
    with settings(warn_only=True):
        result = run("wget http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm", shell=True)    
    print >>sys.stdout, "Result: ", result
  
def yum_install_epel():    
    with settings(warn_only=True):
        result = run("rpm -Uvh epel-release-6*.rpm", shell=True)    
    print >>sys.stdout, "Result: ", result

def yum_check_pip():
    with settings(warn_only=True):
        result = run("yum info python-pip.noarch | grep -i repo", shell=True)    
    print >>sys.stdout, "Result: ", result
    
#@hosts('172.16.15.201') #'172.16.15.214', '172.16.15.212')
def yum_install_pip():
    with settings(warn_only=True):
        result = run("yum -y install python-pip.noarch", shell=True)    
    print >>sys.stdout, "Result: ", result
    

def yum_update():
    print >>sys.stderr, run("yum -y update").return_code
        
#@hosts('172.16.15.201') #'172.16.15.214', '172.16.15.212')
def pip_install_modules():
    '''
    result = run("pip install celery")
    print >>sys.stdout, result
    result = run("pip install redis")
    print >>sys.stdout, result
    result = run("pip install pymongo")
    print >>sys.stdout, result
    result = run("pip install pexpect")
    print >>sys.stdout, result
    '''
    print >>sys.stderr, run("pip install flask").return_code
#@hosts('172.16.15.239')
def test_submit_q_script():
    result = run("/nas/projects/development/productionTools/py_queue/bin/submit_to_queue.py", shell=True)

def task_queue_log():
    result = run("mkdir /var/log/task_queue && chmod 777 /var/log/task_queue")
    print >>sys.stdout, result

def update_upgrade():
    """
        Update the default OS installation's
        basic default tools.
                                            """
    run("aptitude    update")
    run("aptitude -y upgrade")

def install_memcached():
    """ Download and install memcached. """
    run("aptitude install -y memcached")

def update_install():

    # Update
    update_upgrade()

    # Install
    install_memcached()    

def main():
    hostname()

if __name__ == '__main__':
    import sys
    sys.argv = ['fab'] + sys.argv 
    main()
