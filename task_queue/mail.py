#!/usr/bin/env python

import sys
import smtplib

Q_BIN='/nas/projects/development/productionTools/py_queue/bin/submit_to_queue.py'

class Mail(object):
    def __init__(self, **kwargs):
        self.user = 'abhishek'
        self.passwd = 'qwerty'
        self.mail_host = '172.16.10.40'
        self.port = 25
        self.to = 'renderstat@barajoun.com'
        self.from_ = 'a.pareek@barajoun.com'
        self.server = smtplib.SMTP(self.mail_host, self.port)
        # task owner
        self.task_owner = kwargs.get('task_owner')
        # UPLOAD
        if kwargs.get('mail_type') == 'UPLOAD_FAIL':
            self.mail_type = 'UPLOAD_FAIL'
            self.exc = kwargs.get('exc')
            self.task_id = kwargs.get('task_id')
            self.task_id = kwargs.get('task_id')
            self.task_uuid = kwargs.get('task_uuid')
            self.einfo = kwargs.get('einfo') 
        elif kwargs.get('mail_type') == 'UPLOAD_COMPLETE':
            self.mail_type = 'UPLOAD_COMPLETE'
            self.task_id = kwargs.get('task_id')
            self.task_uuid = kwargs.get('task_uuid')
            self.retval = kwargs.get('retval')
        elif kwargs.get('mail_type') == 'UPLOAD_START':
            self.mail_type = 'UPLOAD_START'
            self.task_id = kwargs.get('task_id')
            self.task_uuid = kwargs.get('task_uuid')
            self.cmd = kwargs.get('cmd')
            self.dep_file_path = kwargs.get('dep_file_path')
        elif kwargs.get('mail_type') == 'UPLOAD_SUBMIT':
            self.mail_type = 'UPLOAD_SUBMIT'
            self.task_id = kwargs.get('task_id')
            self.unique_id = kwargs.get('unique_id')
            self.operation = kwargs.get('operation')
            self.alf_script = kwargs.get('alf_script')
            self.dep_file_path = kwargs.get('dep_file_path')
            self.task_owner = kwargs.get('task_owner')
            self.sync_id = kwargs.get('sync_id')
            self.cmd = "{0} {1} {2} {3} {4} {5}".format(Q_BIN, self.operation, self.dep_file_path, self.task_owner, self.alf_script, self.unique_id)
        # SPOOL
        elif kwargs.get('mail_type') == 'SPOOL_COMPLETE':
            self.mail_type = 'SPOOL_COMPLETE'
            self.task_id = kwargs.get('task_id') 
            self.task_uuid = kwargs.get('task_uuid')
            self.retval = kwargs.get('retval')
        elif kwargs.get('mail_type') == 'SPOOL_FAIL':
            self.mail_type = 'SPOOL_FAIL'
            self.exc = kwargs.get('exc')
            self.task_id = kwargs.get('task_id')
            self.task_uuid = kwargs.get('task_uuid')
            self.einfo = kwargs.get('einfo')
        elif kwargs.get('mail_type') == 'SPOOL_SUBMIT':
            self.mail_type = 'SPOOL_SUBMIT'
            self.task_id = kwargs.get('task_id')
            self.unique_id = kwargs.get('unique_id')
            self.operation = kwargs.get('operation')
            self.alf_script = kwargs.get('alf_script')
            self.dep_file_path = kwargs.get('dep_file_path')
            self.task_owner = kwargs.get('task_owner')
            self.spool_id = kwargs.get('spool_id')
            self.cmd = "{0} {1} {2} {3} {4} {5}".format(Q_BIN, self.operation, self.dep_file_path, self.task_owner, self.alf_script, self.unique_id)
        # DOWNLOAD
        elif kwargs.get('mail_type') == 'DOWNLOAD_FAIL':
            self.mail_type = 'DOWNLOAD_FAIL'
            self.exc = kwargs.get('exc')
            self.task_id = kwargs.get('task_id')
            self.task_uuid = kwargs.get('task_uuid')
            self.einfo = kwargs.get('einfo')
        elif kwargs.get('mail_type') == 'DOWNLOAD_COMPLETE':
            self.mail_type = 'DOWNLOAD_COMPLETE'
            self.task_id = kwargs.get('task_id')
            self.task_uuid = kwargs.get('task_uuid')
            self.retval = kwargs.get('retval')
        elif kwargs.get('mail_type') == 'DOWNLOAD_START':
            self.mail_type = 'DOWNLOAD_START'
            self.task_id = kwargs.get('task_id')
            self.task_uuid = kwargs.get('task_uuid')
        elif kwargs.get('mail_type') == 'DOWNLOAD_SUBMIT':
            self.mail_type = 'DOWNLOAD_SUBMIT'
            self.task_id = kwargs.get('task_id')


    def send(self): 
        self.server.ehlo()
        self.server.starttls()
        self.server.ehlo()
        self.server.login(self.user, self.passwd)

        msg = self.header() + self.body()
        #print msg

        self.server.sendmail(self.from_, self.to, msg)
        
        self.server.close()
        #print >>sys.stderr, "Done!"
                
    def header(self):
        return 'To:' + self.to + '\n' + 'From: ' + self.from_ + '\n' #+ '\n' + 'Subject: {0} notification\n'.format(type)
        
    def body(self):
        # UPLOAD
        if self.mail_type == 'UPLOAD_START':
            body = 'Subject: NOTICE: {0} Init Mail\n'.format(self.task_id) 
            body += '\nDear reader,\n\nTask: {0} has started to upload assets to remote tractor queue.\n'.format(self.task_uuid)
            body += '\nDependency file: {0}.\nCommand to be run: {1} .\n'.format(self.dep_file_path, self.cmd)
        elif self.mail_type == 'UPLOAD_COMPLETE':
            body = 'Subject: SUCCESS: {0} Completion Mail\n'.format(self.task_id) 
            body += '\nDear reader,\n\nTask: {0} has uploaded assets to the remote tractor queue successfully.\n\nHere is the return value from the task: {1}\n'.format(self.task_uuid, self.retval) 
        elif self.mail_type == 'UPLOAD_FAIL':
            body = 'Subject: ERROR: {0} Fail Mail\n'.format(self.task_id) 
            body += '\nDear reader,\n\nTask: {0} has failed to upload assets to the remote tractor queue.\n\nHere are the log details:\nException: {1}\nBacktrace: {2}\n'.format(self.task_uuid, self.exc, self.einfo)
        elif self.mail_type == 'UPLOAD_SUBMIT':
            body = 'Subject: NOTICE: {0} Submission Mail\n'.format(self.sync_id)
            body += '\nDear reader,\n\nTask: {0} has been submitted to upload assets to remote tractor queue.\n'.format(self.task_id)
            body += '\n\nTask Owner is : {0}\n'.format(self.task_owner.title())
            body += '\nDependency file: {0}.\n\nCommand to be run: {1}\n'.format(self.dep_file_path, self.cmd)
        # SPOOL
        elif self.mail_type == 'SPOOL_COMPLETE':
            body = 'Subject: SUCCESS: {0} Submission Mail\n'.format(self.task_id)
            body += '\nDear reader,\n\nTask: {0} has successfully spooled your task in the remote tractor queue with jid: {1}.\n\n'.format(self.task_uuid, self.retval)        
        elif self.mail_type == 'SPOOL_FAIL':
            body = 'Subject: ERROR: {0} Fail Mail\n'.format(self.task_id)
            body += '\nDear reader,\n\nTask: {0} has failed to submit to the remote tractor render queue.\n\nHere are the log details:\nException: {1}\nBacktrace: {2}\n'.format(self.task_uuid, self.exc, self.einfo)
        elif self.mail_type == 'SPOOL_SUBMIT':
            body = 'Subject: NOTICE: {0} Submission Mail\n'.format(self.spool_id)
            body += '\nDear reader,\n\nTask: {0} has been submitted to upload assets to remote tractor queue.\n'.format(self.task_id)
            body += '\n\nTask Owner is : {0}\n'.format(self.task_owner.title())
            body += '\nDependency file: {0}.\n\nCommand to be run: {1}\n'.format(self.dep_file_path, self.cmd)
        # DOWNLOAD
        elif self.mail_type == 'DOWNLOAD_START':
            body = 'Subject: NOTICE: {0} Init Mail\n'.format(self.task_id)
            body += '\nDear reader,\n\nTask: {0} has started to download assets from the remote tractor queue.\n'.format(self.task_uuid)
        elif self.mail_type == 'DOWNLOAD_COMPLETE':
            body = 'Subject: SUCCESS: {0} Completion Mail\n'.format(self.task_id)
            body += '\nDear reader,\n\nTask: {0} has downloaded assets from the remote tractor queue successfully.\n\nHere is the return value from the task: {1}\n'.format(self.task_uuid, self.retval)
        elif self.mail_type == 'DOWNLOAD_FAIL':
            body = 'Subject: ERROR: {0} Fail Mail\n'.format(self.task_id)
            body += '\nDear reader,\n\nTask: {0} has failed to download assets from the remote tractor render queue.\n\nHere are the log details:\nException: {1}\nBacktrace: {2}\n'.format(self.task_uuid, self.exc, self.einfo)

        body += '\nIn case of an emergency, please contact Pipeline/I.T.\n'
        body += '\nFrom,\nThe Queue'

        return body

