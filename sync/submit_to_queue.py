import sys
from os.path import basename
import datetime
from uuid import uuid4

from pymongo import MongoClient

from task_queue.tasks import SyncTask, SpoolTask
from celery import chain

from sync import find_scene_deps
from sync import submit_cmds

def db_insert_task(op, task_id, task_owner, host='lic', port=27017, status='pending'):
    client = MongoClient('mongodb://{0}:{1}/'.format(host, port))
    task_collection = client.queue.tasks

    print >>sys.stderr, "++++++++++++++++++++++++++++++++++++++++"
    print >>sys.stderr, "++Inserting the task into the database++"
    print >>sys.stderr, "++++++++++++++++++++++++++++++++++++++++"

    task_doc = task_collection.find_one({'task_id' : task_id})
    if not task_doc:
        task_doc = {}
        task_doc['task_id'] = task_id

    task_doc['sync_init'] = datetime.datetime.now()

    if op == 'SYNC' or op == 'SYNC_RENDER':
        task_doc['sync_status'] = status
    else:
        task_doc['spool_status'] = status

    task_doc['task_owner'] = task_owner
    task_collection.save(task_doc)

def submit(**kwargs):
    operation = kwargs.get('launch_type')
    dep_file = kwargs.get('dep_file')
    ascp_cmd = submit_cmds.get_ascp_cmd(kwargs.get('sync_list'))
    task_uuid = kwargs.get('task_uuid')
    task_owner = kwargs.get('task_owner')

    #spool_cmd = submit_cmds.get_tractor_spool_cmd(kwargs.get('alf_script'), kwargs.get('spool_dry_run'))
    engine='fox:1503'
    priority=50
    alf_script=kwargs.get('alf_script')

    print >>sys.stderr, "dep file path:  ", dep_file
    print >>sys.stderr, "ascp cmd:  ", ascp_cmd
    #print >>sys.stderr, "spool cmd: ", spool_cmd

    #new_uuid = uuid4()
    file_base_name = basename(dep_file).split('.')[0]
    task_id = ("{0}__{1}").format(file_base_name, task_uuid)
    sync_task_uuid = ("upload__{0}__{1}").format(file_base_name, task_uuid)    
    spool_task_uuid = ("spool__{0}__{1}").format(file_base_name, task_uuid)    

    # Prepare the `SyncTask`
    sync_task = SyncTask.subtask(args=(task_owner, dep_file, ascp_cmd, str(task_id)), task_id=sync_task_uuid)
    # Prepare the `RenderTask`
    spool_task = SpoolTask.subtask(args=(task_owner, engine, priority, alf_script, str(task_id)), task_id=spool_task_uuid, immutable=True)

    print >>sys.stderr, "operation: ", operation

    # Submit a `CHAIN` to the queue
    if operation == 'SYNC_RENDER':
        db_insert_task('SYNC_RENDER', task_id, task_owner)
        # with both - sync and spool tasks
        chain(sync_task, spool_task)()
        return task_id
    elif operation == 'SYNC':
        db_insert_task('SYNC', task_id, task_owner)
        # with just the sync task
        chain(sync_task)()
        return task_id
    elif operation == 'RENDER':
        db_insert_task('RENDER', task_id, task_owner)
        # with just the spool task
        chain(spool_task)()
        return task_id
    
