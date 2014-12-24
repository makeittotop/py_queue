#!/usr/bin/env python

import sys
import os

# Save the original stdout
SYS_STDOUT_ORIG = sys.stdout
SYS_STDERR_ORIG = sys.stderr
# Don't write anything to stdout
DEV_NULL = open(os.devnull, 'w')

import datetime
import glob
from uuid import uuid4

# Adding the py_queue module path to the script
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not module_path in sys.path:
    sys.path.insert(1, module_path)
del module_path

from pymongo import MongoClient
from celery import chain

from task_queue.tasks import SyncTask, UploadTestTask, SpoolTask, SpoolTestTask
from task_queue.mail import Mail
from sync import submit_cmds

def db_insert_task(op, task_id, task_owner, host='lic', port=27017, status='pending'):
    # Restore original sys.stdout
    global DEV_NULL, SYS_STDERR_ORIG
    sys.stderr = DEV_NULL

    client = MongoClient('mongodb://{0}:{1}/'.format(host, port))
    task_db = client.queue 
    task_collection = client.queue.tasks

    print >>sys.stderr, "++++++++++++++++++++++++++++++++++++++++"
    print >>sys.stderr, "++Inserting the task into the database++"
    print >>sys.stderr, "++++++++++++++++++++++++++++++++++++++++"

    task_doc = task_collection.find_one({'task_id' : task_id})
    if not task_doc:
        task_doc = {}
        task_doc['task_id'] = task_id

        # Calling a javascript function stored through db.system.js.save({...})
        counter = int(task_db.eval('getNextSequenceValue("task_counter")'))
        task_doc['_counter'] = counter


    task_doc['task_init'] = datetime.datetime.now()

    if op == 'SYNC':
        task_doc['upload_id'] = "UP-{0}".format(task_doc['_counter'])
        task_doc['sync_status'] = status
    elif op == 'SYNC_RENDER':
       task_doc['upload_id'] = "UP-{0}".format(task_doc['_counter'])
       task_doc['spool_id'] = "SPOOL-{0}".format(task_doc['_counter'])
       task_doc['sync_status'] = status
       task_doc['spool_status'] = status
    elif op == 'RENDER':
        task_doc['spool_id'] = "SPOOL-{0}".format(task_doc['_counter'])
        task_doc['spool_status'] = status

    task_doc['task_owner'] = task_owner

    print >>sys.stderr, task_doc

    task_collection.save(task_doc)

    sys.stderr = SYS_STDERR_ORIG
    return task_doc

def submit(**kwargs):
    operation = kwargs.get('launch_type')
    dep_file = kwargs.get('dep_file')
    #ascp_cmd = submit_cmds.get_ascp_cmd(kwargs.get('sync_list'))
    ascp_cmd = submit_cmds.get_proxy_ascp_cmd(kwargs.get('sync_list'))
    task_uuid = kwargs.get('task_uuid')
    task_owner = kwargs.get('task_owner')
    alf_script=kwargs.get('alf_script')

    #spool_cmd = submit_cmds.get_tractor_spool_cmd(kwargs.get('alf_script'), kwargs.get('spool_dry_run'))
    engine='54.169.63.110:1503'
    priority=50

    #new_uuid = uuid4()
    file_base_name = os.path.basename(dep_file).split('.')[0]
    task_id = ("{0}__{1}").format(file_base_name, task_uuid)
    #print >>sys.stdout, "Task ID:  ", task_id

    '''
    # SEND SUBMIT MAIL
    mail_obj = Mail(task_owner=self.task_owner, mail_type='UPLOAD_START', task_id=task_id, task_uuid=self.task_uuid, dep_file_path=dep_file_path, cmd=cmd)
    mail_obj.send_()
    '''
   
    count = 0
    # Submit a `CHAIN` to the queue
    if operation == 'SYNC_RENDER':
        task_doc = db_insert_task('SYNC_RENDER', task_id, task_owner)
        counter = task_doc['_counter']

        sync_task_uuid = ("UP-{0}").format(counter)    
        spool_task_uuid = ("SPOOL-{0}").format(counter)    
        #sync_task_uuid = ("upload__{0}__{1}").format(file_base_name, task_uuid)    
        #spool_task_uuid = ("spool__{0}__{1}").format(file_base_name, task_uuid)    

        # Prepare the `SyncTask`
        #sync_task = SyncTask.subtask(args=(task_owner, dep_file, ascp_cmd, str(task_id), str(task_uuid), alf_script, operation), task_id=sync_task_uuid)
        sync_task = UploadTestTask.subtask(args=(task_owner, dep_file, ascp_cmd, str(task_id), str(task_uuid), alf_script, operation, count), task_id=sync_task_uuid)

        # Prepare the `RenderTask`
        #spool_task = SpoolTask.subtask(args=(task_owner, engine, priority, alf_script, str(task_id), str(task_uuid), dep_file, operation), task_id=spool_task_uuid, immutable=True)
        spool_task = SpoolTestTask.subtask(args=(task_owner, engine, priority, alf_script, str(task_id), str(task_uuid), dep_file, operation, count), task_id=spool_task_uuid, immutable=True)

        # with both - sync and spool tasks
        chain(sync_task, spool_task)()

        # Send mail
        mail_obj = Mail(task_owner=task_owner, mail_type='UPLOAD_SUBMIT', unique_id=task_uuid, task_id=task_id, dep_file_path=dep_file, operation=operation, alf_script=alf_script, upload_id=sync_task_uuid)
        mail_obj.send_()

        #return (sync_task_uuid, task_id)
        print >>sys.stdout, sync_task_uuid, ':', task_id

    elif operation == 'SYNC':
        task_doc = db_insert_task('SYNC', task_id, task_owner)
        counter = task_doc['_counter']

        sync_task_uuid = ("UP-{0}").format(counter)    
        #sync_task_uuid = ("upload__{0}__{1}").format(file_base_name, task_uuid)    

        # Prepare the `SyncTask`
        #sync_task = SyncTask.subtask(args=(task_owner, dep_file, ascp_cmd, str(task_id), str(task_uuid), alf_script, operation), task_id=sync_task_uuid)
        sync_task = UploadTestTask.subtask(args=(task_owner, dep_file, ascp_cmd, str(task_id), str(task_uuid), alf_script, operation, count), task_id=sync_task_uuid)

        # with just the sync task
        chain(sync_task)()

        # Send mail
        mail_obj = Mail(task_owner=task_owner, mail_type='UPLOAD_SUBMIT', unique_id=task_uuid, task_id=task_id, dep_file_path=dep_file, operation=operation, alf_script=alf_script, upload_id=sync_task_uuid)
        mail_obj.send_()

        #return (sync_task_uuid, task_id)
        print >>sys.stdout, sync_task_uuid, ':', task_id

    elif operation == 'RENDER':
        task_doc = db_insert_task('RENDER', task_id, task_owner)
        counter = task_doc['_counter']

        spool_task_uuid = ("SPOOL-{0}").format(counter)    
        #spool_task_uuid = ("spool__{0}__{1}").format(file_base_name, task_uuid)    

        # Prepare the `RenderTask`
        #spool_task = SpoolTask.subtask(args=(task_owner, engine, priority, alf_script, str(task_id), str(task_uuid), dep_file, operation), task_id=spool_task_uuid, immutable=True)
        spool_task = SpoolTestTask.subtask(args=(task_owner, engine, priority, alf_script, str(task_id), str(task_uuid), dep_file, operation, count), task_id=spool_task_uuid, immutable=True)

        # with just the spool task
        chain(spool_task)()

        # Send mail
        mail_obj = Mail(task_owner=task_owner, mail_type='SPOOL_SUBMIT', unique_id=task_uuid, task_id=task_id, dep_file_path=dep_file, operation=operation, alf_script=alf_script, spool_id=spool_task_uuid)
        mail_obj.send_()

        #return (spool_task_uuid, task_id
        print >>sys.stdout, spool_task_uuid, ':', task_id

def main():
    if len(sys.argv) != 6:
        print >>sys.stdout, "Usage: <script> <operation> <dep_file> <task_owner> <alf_script> <task_uuid>"
        sys.exit(0)

    launch_type = sys.argv[1]
    dep_file = sys.argv[2]
    task_owner = sys.argv[3]
    alf_script = sys.argv[4]
    task_uuid = sys.argv[5]

    dep_file_handle = open(dep_file, "r")
    dep_list = dep_file_handle.readlines()

    deps = []
    for dep in dep_list:
        items = glob.glob(dep.strip())
        deps.extend(items)

    sync_list=''
    for dep in deps:
        sync_list = sync_list + dep + ' '

    # Save the original stdout
    global DEV_NULL
    sys.stdout = DEV_NULL

    print >>sys.stdout, "Launch Type:  ", launch_type
    print >>sys.stdout, "Dep File:  ", dep_file
    print >>sys.stdout, "Task UUID:  ", task_uuid
    print >>sys.stdout, "Task Owner:  ", task_owner
    print >>sys.stdout, "Alf Script:  ", alf_script
    print >>sys.stdout, "Sync List:  ", sync_list

    # Restore original sys.stdout
    global SYS_STDOUT_ORIG, SYS_STDERR_ORIG
    sys.stdout = SYS_STDOUT_ORIG
    sys.stderr = SYS_STDERR_ORIG

    submit(launch_type=launch_type, dep_file=dep_file, sync_list=sync_list, task_uuid=task_uuid, task_owner=task_owner, alf_script=alf_script)

if __name__ == '__main__':
    main()


