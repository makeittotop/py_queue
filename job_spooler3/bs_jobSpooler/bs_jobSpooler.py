#!/usr/bin/env python

import sys
import os
import codecs
from PyQt4 import QtCore, QtGui
import re, glob, getpass

from job_spooler3.bs_jobSpooler.qjobSpooler_UI import Ui_qSpooler
from job_spooler3.bs_jobSpooler.seqInfo import seqInfo

from autoPublishServerClient import runCommands

import rfm.tractor

try:
    from maya import OpenMayaUI as omui
    import maya.cmds as cmds
    from pymel.core import *
    import sip
except:
    pass

from notfDialog import *

__author__ = "Belal Salem <belal@nothing-real.com>"
__version__ = "1.9.5"

# Global Variables Initialization
WINDOW_TITLE = 'Tractor/Alfred Job Spooler'
WINDOW_VERTION = __version__
WINDOW_NAME = 'qSpooler'

Q_SUBMIT_BIN = '/nas/projects/development/productionTools/py_queue/bin/submit_to_queue.py'

REG_EXP = re.compile(r'^\d+[0-9-,]+\d+$')

def mayaMainWindow():
    try:
        mayaWinPtr = omui.MQtUtil.mainWindow()
        mayaWin = sip.wrapinstance(long(mayaWinPtr), QtGui.QWidget)
        return mayaWin
    except:
        return None

def setupSceneGlobals():
    try:
        renderRoot='/nas/projects/Tactic/bilal/render'

        prePubInfo = runCommands.parseSelectedFiles(sceneName())
        if prePubInfo:
            seq = prePubInfo["seqname"]
            scn = prePubInfo["scname"]
            sh = prePubInfo["shname"]
            ver = prePubInfo["version"]
        else:
            err = confirmDialog(title='Warning ...',
                message=("Couldn't get a version number from Tactic, most problaly your scene name didn't follow the barajoun naming convention!!\nThe images from this scene will go to seqXX_scnXX_shXXX until you fix scene name and re-setup the render globals again."),
                button=['Confirm'], defaultButton='Confirm',
                icon='warning')
            return False

        setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')
        setAttr('defaultRenderGlobals.animation', 1)
        mel.eval('setMayaSoftwareFrameExt(3,0)')
        setAttr('defaultRenderGlobals.animationRange', 0)
        setAttr('defaultRenderGlobals.extensionPadding', 4)
        setAttr('defaultRenderGlobals.imageFilePrefix', '%s/%s/%s/%s/cg/%s/<RenderLayer>/<RenderPass>_<Scene>'%(renderRoot, seq, scn, sh, ver), type='string')
        setAttr('defaultArnoldDriver.tiled', 0)
        setAttr('defaultArnoldDriver.autocrop', 1)
        setAttr('defaultArnoldDriver.exrCompression', 3)
        setAttr('defaultArnoldRenderOptions.use_existing_tiled_textures', 1)
        setAttr("defaultArnoldRenderOptions.log_verbosity", 1)
        setAttr("defaultArnoldRenderOptions.abortOnError", 1)
        setAttr("defaultArnoldRenderOptions.abortOnLicenseFail", 1)

        setAttr("defaultArnoldRenderOptions.display_gamma", 1)
        setAttr("defaultViewColorManager.imageColorProfile", 2)

        start = playbackOptions(q=True, minTime=True)
        end = playbackOptions(q=True, maxTime=True)

        setAttr("defaultRenderGlobals.startFrame", start)
        setAttr("defaultRenderGlobals.endFrame", end)
        return True
    except:
        return False


class bs_jobSpooler(QtGui.QDialog):
    def __init__(self, parent=mayaMainWindow(), imgPath=None, tskType=0, tskFile=False, prjPath=False, tskScript='', opt='',
                title='', start=False, end=False, priority=50, taskSize=1, standalone=True):
        #QtGui.QWidget.__init__(self, parent)
        super(bs_jobSpooler, self).__init__(parent)
        self.ui = Ui_qSpooler()
        self.ui.setupUi(self)

        # Initial variables:
        self.checkForSeq = False

        if os.name == 'posix':
            self.slash = '/'
            self.tsr = '&'
        else:
            self.slash = '\\'
            self.tsr = '&'  # Not sure what is equivalent to this under windows

        self.setWindowTitle('{0} {1}'.format(WINDOW_TITLE, str(WINDOW_VERTION)))
        
        engineVar = os.getenv('TRACTOR_ENGINES')
        if engineVar != None:
            engines = []
            enginesParts = engineVar.split(':')
            if len(engines) % 2 == 0:
                for i in xrange(0, len(enginesParts), 2):
                    if enginesParts[i] == 'lic':
                        next
                    eng = '%s:%s'%(enginesParts[i], enginesParts[i+1])
                    engines.append(eng)
                    self.ui.engineTxt.addItem(eng)
                self.engine = '%s:%s'%(enginesParts[0], enginesParts[1])    #set self.engine to first available engine
            else:
                print 'warning: TRACTOR_ENGINES var should be set as engine:port pairs, default engine will be used.'
                self.engine = 'tractor-engine:80'
                self.ui.engineTxt.addItem(self.engine)

        else:
            print 'warning: TRACTOR_ENGINES var was not set, default engine will be used.'
            self.engine = 'tractor-engine:80'
            self.ui.engineTxt.addItem(self.engine)
        
        QtCore.QObject.connect(self.ui.prjPathBtn, QtCore.SIGNAL("clicked()"), self.browsePrj)
        QtCore.QObject.connect(self.ui.browseSeqBtn, QtCore.SIGNAL("clicked()"), self.browseSeq)
        QtCore.QObject.connect(self.ui.browseScriptBtn, QtCore.SIGNAL("clicked()"), self.browseScript)
        QtCore.QObject.connect(self.ui.alfredBtn, QtCore.SIGNAL("clicked()"), self.sendAlfred)
        QtCore.QObject.connect(self.ui.tractorBtn, QtCore.SIGNAL("clicked()"), self.sendToTractor)
        QtCore.QObject.connect(self.ui.genTaskBtn, QtCore.SIGNAL("clicked()"), self.preGen)
        QtCore.QObject.connect(self.ui.renCpBtn, QtCore.SIGNAL("clicked()"), self.renCp)
        QtCore.QObject.connect(self.ui.renMvBtn, QtCore.SIGNAL("clicked()"), self.renMv)
        QtCore.QObject.connect(self.ui.renderBtn, QtCore.SIGNAL("clicked()"), self.render)
        QtCore.QObject.connect(self.ui.qTaskType, QtCore.SIGNAL("currentIndexChanged(QString)"), self.Task)
        QtCore.QObject.connect(self.ui.engineTxt, QtCore.SIGNAL("currentIndexChanged(QString)"), self.engChanged)
        QtCore.QObject.connect(self.ui.engineTxt, QtCore.SIGNAL("currentTextEdited(QString)"), self.engChanged)
        QtCore.QObject.connect(self.ui.qTaskSeq, QtCore.SIGNAL("textChanged(QString)"), self.taskSeq)
        QtCore.QObject.connect(self.ui.qPrjPath, QtCore.SIGNAL("textChanged(QString)"), self.setPrj)
        QtCore.QObject.connect(self.ui.taskTitle, QtCore.SIGNAL("textChanged(QString)"), self.title)
        QtCore.QObject.connect(self.ui.qScriptPath, QtCore.SIGNAL("editingFinished()"), self.scriptHandPath)
        QtCore.QObject.connect(self.ui.autoStart, QtCore.SIGNAL("toggled(bool)"), self.checkToggled)
        QtCore.QObject.connect(self.ui.autoEnd, QtCore.SIGNAL("toggled(bool)"), self.checkToggled)
        QtCore.QObject.connect(self.ui.seqFrom, QtCore.SIGNAL("editingFinished()"), self.unCheckStart)
        QtCore.QObject.connect(self.ui.seqTo, QtCore.SIGNAL("editingFinished()"), self.unCheckEnd)
        QtCore.QObject.connect(self.ui.engineTxt, QtCore.SIGNAL("editingFinished()"), self.engineMod)
        QtCore.QObject.connect(self.ui.periorityTxt, QtCore.SIGNAL("editingFinished()"), self.priorityChange)
        QtCore.QObject.connect(self.ui.perTask, QtCore.SIGNAL("editingFinished()"), self.taskSizeChange)
        QtCore.QObject.connect(self.ui.curLayerBtn, QtCore.SIGNAL("clicked()"), self.onlyCurLayer)
        QtCore.QObject.connect(self.ui.skipSpin, QtCore.SIGNAL("editingFinished()"), self.framesSkip)
        #QtCore.QObject.connect(self.ui.task_size_check_box, QtCore.SIGNAL("stateChanged(int)"), self.task_size_func)
        QtCore.QObject.connect(self.ui.select_frames_text_edit, QtCore.SIGNAL("textChanged()"), self.select_frames_func)
        
        self.ui.syncChk.setHidden(True)
        self.ui.renChk.setHidden(True)

        self.priority = priority
        self.taskSize = 1
        self.standalone = standalone
        self.curDir = os.path.abspath(os.curdir)
        self.prjPathDone = False
        self.scriptAutoNamed = True
        self.jobFile = False
        self.jobScript = tskScript
        self.prjPath = False
        self.curDir = os.path.abspath(os.curdir)
        self.taskDir = False
        self.taskBaseName = False
        self.singleTaskFile = False
        self.job = False
        self.fileSeq = False
        self.seqName = False
        self.taskStart = False
        self.prjPath = self.curDir
        self.genMsgEnabled = True
        self.renderCmd = 'kickMaya -nstdin '
        self.err = False
        self.curLayer = False
        self.imgPath = imgPath
        self.skipFrames = 0

        self.frame_list = []

        # parse arguments
        self.ui.qTaskType.setCurrentIndex(tskType)
        self.Task()
        if tskFile:
            self.ui.qTaskSeq.setText(tskFile)
        if prjPath:
            self.ui.qPrjPath.setText(prjPath)
            self.prjPathDone = True
        if title:
            self.ui.taskTitle.setText(title)
        if opt:
            self.ui.optionalArgs.setText(opt)
        if start > 0:
            self.ui.seqFrom.setValue(start)
            self.taskStart = start
        if end > 0:
            self.ui.seqTo.setValue(end)
            self.taskEnd = end
        if taskSize > 1:
            self.ui.perTask.setValue(taskSize)
            self.taskSize = taskSize
        if priority != 50:
            self.ui.periorityTxt.setValue(priority)
            self.priority = priority

        self.extraArgs = ' ' + opt
        self.jobFullPath = tskScript
        self.task = seqInfo(tskFile, False)
        self.prjPath = prjPath
        self.tskStart = start
        self.taskEnd = end
        self.taskFile = tskFile
    
    def engChanged(self):
        self.engine = self.ui.engineTxt.currentText()
        if 'fox' not in self.engine:
            self.ui.syncChk.setHidden(True)
            self.ui.renChk.setHidden(True)

            #self.ui.tractorBtn.setText("Send to LOCAL Tractor") 
        else:
            self.ui.syncChk.setHidden(False)
            self.ui.renChk.setHidden(False)

            #self.ui.tractorBtn.setText("Send to REMOTE Tractor") 
           
    def Task(self):   # qTaskType index Names
        self.ui.optionalArgs.setPlainText('')
        self.ui.seqFrom.setEnabled(1)
        self.ui.seqTo.setEnabled(1)
        
        self.taskIndex = self.ui.qTaskType.currentIndex()
        if self.taskIndex == 0:   # Arnold Render
            self.taskExt = '.ass'
            self.taskExtGz = '.ass.gz'
            self.renderCmd = 'kickMaya -nstdin '
            self.ui.patchBtn.setText('Patch ASS')
            self.ui.patchBtn.setEnabled(1)
            self.ui.renCpBtn.setEnabled(1)
            self.ui.renMvBtn.setEnabled(1)
            self.ui.renderBtn.setEnabled(1)
            self.ui.curLayerBtn.setEnabled(0)
            self.checkForSeq = True
            return

        if self.taskIndex == 1:   # Renderman Render
            self.taskExt = '.rib'
            self.taskExtGz = '.rib.gz'
            self.renderCmd = 'prman -d it '
            self.ui.patchBtn.setText('Patch RIBs')
            self.ui.patchBtn.setEnabled(1)
            self.ui.renCpBtn.setEnabled(1)
            self.ui.renMvBtn.setEnabled(1)
            self.ui.renderBtn.setEnabled(1)
            self.ui.curLayerBtn.setEnabled(0)
            self.checkForSeq = True
            return

        if self.taskIndex == 2:   # Massive Simulation
            self.taskExt = '.mas'
            self.taskExtGz = ''
            self.ui.patchBtn.setText('Patch Mas')
            self.ui.patchBtn.setEnabled(1)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.ui.curLayerBtn.setEnabled(0)
            self.checkForSeq = False
            return

        if self.taskIndex == 3:   # Katana Render
            self.taskExt = '.katana'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.ui.curLayerBtn.setEnabled(0)
            self.checkForSeq = False
            return

        if self.taskIndex == 4:   # Nuke Render
            self.taskExt = '.nk'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.checkForSeq = False
            self.ui.curLayerBtn.setEnabled(0)
            return

        if self.taskIndex == 5:   # Maya Render
            self.taskExt = '.ma *.mb'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.checkForSeq = False
            if not self.standalone:
                self.ui.curLayerBtn.setEnabled(1)
            return

        if self.taskIndex == 6:   # Maya Cmd Script
            self.taskExt = '.ma *.mb'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.ui.curLayerBtn.setEnabled(0)
            self.ui.seqFrom.setEnabled(0)
            self.ui.seqTo.setEnabled(0)
            self.ui.optionalArgs.setPlainText('"<your_script/cmd_here>;" ')
            self.checkForSeq = False
            return

        if self.taskIndex == 7:   # Mentalray Render
            self.taskExt = '.mi'
            self.taskExtGz = ''
            self.ui.patchBtn.setText('Patch Mi')
            self.ui.patchBtn.setEnabled(1)
            self.ui.renCpBtn.setEnabled(1)
            self.ui.renMvBtn.setEnabled(1)
            self.ui.renderBtn.setEnabled(1)
            self.ui.curLayerBtn.setEnabled(0)
            self.checkForSeq = True
            return
        
        if self.taskIndex == 8:   # FumeFX Sim
            self.taskExt = '.ma *.mb'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.ui.seqFrom.setEnabled(0)
            self.ui.seqTo.setEnabled(0)
            self.ui.optionalArgs.setPlainText('"fumeFXcmd -runSimulation <0:SimTypeID> <fumeShape>;" ')
            self.checkForSeq = False
            if not self.standalone:
                self.ui.curLayerBtn.setEnabled(1)
            return
        
        if self.taskIndex == 9:   # FumeFX Render
            self.taskExt = '.ma *.mb'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.checkForSeq = False
            if not self.standalone:
                self.ui.curLayerBtn.setEnabled(1)
            return

        if self.taskIndex > 9:
            self.renderCmd = False
            Confirm = 'Confirm'
            message = QtGui.QMessageBox(self)
            message.setText("Sorry! This task type is not implemented yet.\n Check for updates from www.nothing-real.com")
            message.setWindowTitle('jobSpooler...')
            message.setIcon(QtGui.QMessageBox.Warning)
            message.addButton(Confirm, QtGui.QMessageBox.AcceptRole)
            message.exec_()
            self.ui.curLayerBtn.setEnabled(0)
            return
            # response = message.clickedButton().text()

        if self.taskIndex == 10:   # Renderman RIB Generate
            self.taskExt = '.mb'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.ui.curLayerBtn.setEnabled(0)
            return

        if self.taskIndex == 11:   # Arnold ASS Generate
            self.taskExt = '.mb'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.ui.curLayerBtn.setEnabled(0)
            return

        if self.taskIndex == 12:   # Mentalray MI gen
            self.taskExt = '.mb'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.ui.curLayerBtn.setEnabled(0)
            return

        if self.taskIndex == 13:   # Fusion Render
            self.taskExt = '.comp'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.ui.curLayerBtn.setEnabled(0)
            return

        if self.taskIndex == 14:   # Shake Render
            self.taskExt = '.shk'
            self.taskExtGz = ''
            self.ui.patchBtn.setEnabled(0)
            self.ui.renCpBtn.setEnabled(0)
            self.ui.renMvBtn.setEnabled(0)
            self.ui.renderBtn.setEnabled(0)
            self.ui.curLayerBtn.setEnabled(0)
            return

    def browsePrj(self):
        fd = QtGui.QFileDialog(self)
        newPrjPath = fd.getExistingDirectory(caption='Set Project Path', directory=self.curDir)
        if newPrjPath:
            self.prjPath = newPrjPath
            self.ui.qPrjPath.setText(self.prjPath)
            if self.scriptAutoNamed:
                self.curDir = self.ui.qPrjPath.text()

    def setPrj(self):
        self.prjPath = self.ui.qPrjPath.text()
        self.prjPathDone = True
        if self.scriptAutoNamed:
            self.curDir = self.prjPath
            self.title()

    def browseSeq(self):
        fd = QtGui.QFileDialog(self)
        #fd.setNameFilter('*.* *.ass')
        curDir = str(self.ui.qTaskSeq.text())

        if not self.prjPath:
            self.prjPath = curDir

        if not self.taskExtGz == '':
            if curDir:
                self.seqName = fd.getOpenFileName(caption='Get a Task File ...', directory=curDir, filter='*' +
                            str(self.taskExt + '\n*' + self.taskExtGz + '\n*.*'))
            else:
                self.seqName = fd.getOpenFileName(caption='Get a Task File ...', directory=self.prjPath, filter='*' +
                            str(self.taskExt + '\n*' + self.taskExtGz + '\n*.*'))
        else:
            if curDir:
                self.seqName = fd.getOpenFileName(caption='Get a Task File ...', directory=curDir, filter='*' +
                            str(self.taskExt + '\n*.*'))
            else:
                self.seqName = fd.getOpenFileName(caption='Get a Task File ...', directory=self.prjPath, filter='*' +
                            str(self.taskExt + '\n*.*'))
        if self.seqName:
            self.ui.qTaskSeq.setText(self.seqName)
    
    def framesSkip(self):
        self.skipFrames = self.ui.skipSpin.value()

    def task_size_func(self, state):
        pass

        '''
        print self.ui.task_size_check_box.checkState()
        if self.ui.task_size_check_box.isChecked():
            self.ui.perTask.setEnabled(True)
            self.ui.skipSpin.setEnabled(True)
            self.ui.select_frames_text_edit.setEnabled(False)
            self.ui.select_frames_text_edit.setPlainText("This option is mutually exclusive with the `Task Size` block options")
            self.frame_list = []
        else:
            self.ui.perTask.setEnabled(False)
            self.ui.skipSpin.setEnabled(False)
            self.ui.select_frames_text_edit.setEnabled(True)
            self.ui.select_frames_text_edit.setPlainText("")
        '''    

    def select_frames_func(self):
        selected_frames_string = self.ui.select_frames_text_edit.toPlainText()

        if selected_frames_string and selected_frames_string is not "":
            if REG_EXP.match(selected_frames_string):
                #print >>sys.stderr, select_frames_string
                frames = selected_frames_string.split(',')

                frame_list = list()
                for frame_block in frames:
                    if '-' in frame_block:
                        (start, end) = frame_block.split('-')
                        (start, end) = (int(start), int(end))
                        if start < end:
                            frame_list.extend(range(start, end+1))
                        else:
                            frame_list.extend(range(end, start+1))    
                    else:
                        frame_list.append(int(frame_block))

                self.frame_list = sorted(list(set(frame_list))) 
                print >>sys.stderr, self.frame_list
            else:
                self.frame_list = []
                print >>sys.stderr, "Ill-formed string, please check. It should be of the format `number,number-number,number...`"           
        else:
            self.frame_list = []        
                
    def taskSeq(self):
        self.seqName = str(self.ui.qTaskSeq.text())

        self.task = seqInfo(self.seqName, self.checkForSeq)

        if self.task.isSeq:
            if not self.ui.autoStart.isEnabled():
                # Re enable 'auto' checkboxes after recovering from a singled file task
                self.ui.seqFrom.setValue(self.task.start)
                self.ui.seqTo.setValue(self.task.end)
                self.ui.autoStart.setEnabled(1)
                self.ui.autoStart.setChecked(1)
                self.ui.autoEnd.setEnabled(1)
                self.ui.autoEnd.setChecked(1)
            else:
                if self.ui.autoStart.isChecked():
                    self.ui.seqFrom.setValue(int(self.task.start))
                if self.ui.autoEnd.isChecked():
                    self.ui.seqTo.setValue(int(self.task.end))
        else:
            pass
            # Single Frame
            #self.ui.seqFrom.setValue(0)
            #self.ui.seqTo.setValue(0)
            #self.ui.autoStart.setChecked(0)
            #self.ui.autoEnd.setChecked(0)
            #self.ui.autoStart.setEnabled(0)
            #self.ui.autoEnd.setEnabled(0)

        if re.search(r'\.+$', self.task.baseFileName) or re.search(r'\_+$', self.task.baseFileName):
            self.ui.taskTitle.setText(self.task.baseFileName[:-1])
        else:
            self.ui.taskTitle.setText(self.task.baseFileName)

        if not self.prjPathDone:
            self.curDir = self.task.baseDir
            self.ui.qPrjPath.setText(self.curDir)
            self.prjPathDone = True
    
    def onlyCurLayer(self):
        curLayer = editRenderLayerGlobals(q=True, crl=True)
        optArgs = self.ui.optionalArgs.toPlainText()
        optArgs = '-l %s '%curLayer + optArgs
        self.ui.optionalArgs.setPlainText(optArgs)
        jobTitle = self.ui.taskTitle.text() + '_%s'%curLayer
        self.ui.taskTitle.setText(jobTitle)
    
    def errorCheck(self):
        self.seqName = str(self.ui.qTaskSeq.text())
        self.task = seqInfo(self.seqName, self.checkForSeq)
        if self.task.err:
            Confirm = 'Confirm'
            Cancel = 'Cancel'
            message = QtGui.QMessageBox(self)
            message.setText("The task sequence provided doesn't seem to be exist!")
            message.setWindowTitle('jobSpooler...')
            message.setIcon(QtGui.QMessageBox.Warning)
            message.addButton(Confirm, QtGui.QMessageBox.AcceptRole)
            message.addButton(Cancel, QtGui.QMessageBox.RejectRole)
            message.exec_()
            response = message.clickedButton().text()
            if response == Confirm:
                self.err = False
            else:
                self.err = True

    def checkToggled(self):
        self.seqName = str(self.ui.qTaskSeq.text())
        self.task = seqInfo(self.seqName, self.checkForSeq)
        if self.task.isSeq:
            if not self.ui.autoStart.isEnabled():
                # Re enable 'auto' checkboxes after recovering from a singled file task
                self.ui.seqFrom.setValue(self.task.start)
                self.ui.seqTo.setValue(self.task.end)
                self.ui.autoStart.setEnabled(1)
                self.ui.autoStart.setChecked(1)
                self.ui.autoEnd.setEnabled(1)
                self.ui.autoEnd.setChecked(1)
            else:
                if self.ui.autoStart.isChecked():
                    self.ui.seqFrom.setValue(int(self.task.start))
                if self.ui.autoEnd.isChecked():
                    self.ui.seqTo.setValue(int(self.task.end))
        else:
            # Single Frame
            self.ui.seqFrom.setValue(0)
            self.ui.seqTo.setValue(0)
            self.ui.autoStart.setChecked(0)
            self.ui.autoEnd.setChecked(0)
            self.ui.autoStart.setEnabled(0)
            self.ui.autoEnd.setEnabled(0)

    def browseScript(self):
        fd = QtGui.QFileDialog(self)
        if self.ui.taskTitle.text():
            tmpName = fd.getSaveFileName(caption='Set "Task Script" name:', directory=self.ui.taskTitle.text()
                                         + '.alf', filter='*.alf\n*.*')
        else:
            tmpName = fd.getSaveFileName(caption='Set "Task Script" name:', directory='untitled.alf',
                                         filter='*.alf\n*.*')
        if tmpName:   # SAVE Clicked
            self.scriptAutoNamed = False
            self.curDir = os.path.dirname(str(tmpName))
            self.jobFile = tmpName
            self.ui.qScriptPath.setText(self.jobFile)

    def engineMod(self):
        self.engine = self.ui.engineTxt.text()

    def priorityChange(self):
        self.priority = self.ui.periorityTxt.value()

    def taskSizeChange(self):
        self.taskSize = self.ui.perTask.value()

    def unCheckStart(self):
        self.ui.autoStart.setChecked(0)

    def unCheckEnd(self):
        self.ui.autoEnd.setChecked(0)

    def title(self):
        if self.ui.taskTitle.text():
            self.jobFile = str(self.curDir) + self.slash + self.ui.taskTitle.text() + '.alf'
        else:
            self.jobFile = str(self.curDir) + self.slash + 'untitled.alf'
        self.ui.qScriptPath.setText(self.jobFile)
        self.jobScript = str(self.ui.qScriptPath.text())

    def scriptHandPath(self):
        self.curDir = os.path.dirname(str(self.ui.qScriptPath.text()))
        self.scriptAutoNamed = False

    def preGen(self):
        self.errorCheck()
        if not self.err:
            self.genTask()

    def genTask(self, internal=True):
        if internal:
            print >>sys.stderr, "Internal"

            # Preparing:
            dataIsOk = False
            header = False
            exArgs = self.ui.optionalArgs.toPlainText()
            extraArgs = ' ' + exArgs
            self.jobFullPath = str(self.ui.qScriptPath.text())
            taskBaseFilename = self.task.baseFileName
            taskPrj = str(self.prjPath)
            taskDir = self.task.baseDir
            relativeDir = os.path.relpath(taskDir, taskPrj) + self.slash
            jobStart = int(self.ui.seqFrom.value())
            jobEnd = int(self.ui.seqTo.value())
            job = ''
            g = codecs.open(self.jobFullPath, 'w', 'utf-8')
            absTaskPath = str(self.ui.qTaskSeq.text())
            self.taskEnd = self.ui.seqTo.value()
                            
            if self.task.isSeq or 2 < self.taskIndex < 6 or 7 < self.taskIndex < 10:
                print >>sys.stderr, "Frame list: ", self.frame_list

                if not self.frame_list: 
                    # Preparing for Sequencial Task
                    jobRange = range(jobStart, jobEnd + 1)
                else:
                    jobRange = self.frame_list    
                    #taskBaseFilename += '.'
            else:
                # Preparing for Singled Task
                jobRange = range(1, 2)
            
            if self.taskIndex == 5:
                ## Force fixing the version in imagePrefix output path
                try:
                    mayaScnName = os.path.splitext(os.path.basename(sceneName()))[0]
                    scnComps = mayaScnName.split('_')
                    scnVer = scnComps[len(scnComps)-1]
                    curImgPrefix =  getAttr('defaultRenderGlobals.imageFilePrefix')
                    
                    imgComps = curImgPrefix.split('/')
                    for pathPart in imgComps:
                        if re.search('v+[%03d]', pathPart):
                            finalImgPath = curImgPrefix.replace(pathPart, scnVer)
                            if finalImgPath != curImgPrefix:
                                setAttr('defaultRenderGlobals.imageFilePrefix', finalImgPath)
                                # Save maya scene after img prefix change:
                                saveAs(mayaScnName)
                except:
                    print "***WARNINIG: In standalone mode, the version in maya image output path cannot be modified, the version specified in the scene will be used instead!"
            
        else:
            print >>sys.stderr, "External"

            # Preparing:
            dataIsOk = False
            header = False
            extraArgs = self.extraArgs
            taskBaseFilename = self.task.baseFileName
            taskPrj = self.prjPath
            taskDir = self.task.baseDir
            relativeDir = os.path.relpath(taskDir, taskPrj) + self.slash
            jobStart = int(self.tskStart)
            jobEnd = int(self.taskEnd)
            job = ''
            g = codecs.open(self.jobFullPath, 'w', 'utf-8')
            absTaskPath = self.taskFile
            self.taskEnd = self.taskEnd

            if self.task.isSeq or 2 < self.taskIndex < 6 or 7 < self.taskIndex < 10:
                print >>sys.stderr, "Frame list: ", self.frame_list

                if not self.frame_list: 
                    # Preparing for Sequencial Task
                    jobRange = range(jobStart, jobEnd + 1)
                else:
                    jobRange = self.frame_list    
                    #taskBaseFilename += '.'
            else:
                # Preparing for Singled Task
                jobRange = range(1, 2)
        
        # Setting imgPath (for preview frame of maya jobs)
        try:
            iP = os.path.dirname(getAttr('defaultRenderGlobals.imageFilePrefix'))
            if len(iP.split('<RenderLayer>')) > 1:
                curLayer = editRenderLayerGlobals(q=True, crl=True)
                iP = iP.split('<RenderLayer>')[0] + curLayer + '/'
        except:
            iP = None
        
        if self.imgPath is not None:
            iP = self.imgPath           # override imagePath above if been passed through the spooler caller

        # Preparing blade profiles specifics:
        extraService = ""
        if self.ui.profilesBox.currentIndex() == 1:
            extraService = " && (@.mem<=40) &! preview"
        
        elif self.ui.profilesBox.currentIndex() == 2:
            extraService = " && (@.mem>40) &! preview"

        elif self.ui.profilesBox.currentIndex() == 3:
            extraService = " && preview "

        elif self.ui.profilesBox.currentIndex() == 4:
            extraService = " && external &! preview"
        
        elif self.ui.profilesBox.currentIndex() == 5:
            extraService = " && (@.mem<=40) && external &! preview"
        
        elif self.ui.profilesBox.currentIndex() == 6:
            extraService = " && (@.mem>40) && external &! preview"
        
        elif self.ui.profilesBox.currentIndex() == 7:
            extraService = " && fumeFX"
        
        elif self.ui.profilesBox.currentIndex() == 8:
            extraService = " && comp" # empty will take only Nuke service key
            
        # OK! Here we are ready to generate the task
        #counter = jobStart
        counter = jobRange[0]
        for s in jobRange:
            counter2 = s

            relativeTaskPath = relativeDir + taskBaseFilename
            if self.task.isSeq:
                paddedS = str(s)
                paddedS = paddedS.zfill(self.task.pad)
                relativeTaskPath += paddedS + self.task.ext
            #elif self.taskIndex == 3:
            #    paddedS = str(s)
            #    paddedS = paddedS.zfill(4)
            #    relativeTaskPath = self.slash + taskBaseFilename + self.task.ext
            #    subtaskTitle = '{Processing frame ' + str(s) + '} '
            else:
                paddedS = str(s).zfill(4)

            # subTask title should be like this except for Massive and Naiad
            subtaskTitle = '{Processing ' + str(s) + '} '
            atleast = '-atleast %s' % str(self.ui.atleastSpin.value())
            atMost = '-atmost %s' % str(self.ui.atmostSpin.value())
            sameHost = '-samehost %s' % str(self.ui.samehostSpin.value())
            slotOpt = '%s %s %s ' % (sameHost, atleast, atMost)
            
            # Setting any Task Type specific Data
            if self.taskIndex == 0:
                # Arnold Render Task
                jobComment = '{# Created by Belal Salem through jobSpooler} '
                jobTitle = '{' + str(self.ui.taskTitle.text()) + '} '
                taskTitle = '{Renders ' + str(jobStart) + '-' + str(jobEnd) + '} '
                taskArgs = '-dw -dp -v 3 -nstdin -nokeypress -nw 3 -i '
                taskCmd = 'kickAss '
                service = '"kick%s" %s' %(extraService, slotOpt)
                tag = '{kick}'
                if taskBaseFilename[-1:] == '.':
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename[:-1] + '_beauty.' \
                                    + paddedS + '.exr}'
                else:
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename + '_beauty.' \
                                    + paddedS + '.exr}'
                oneRange = ''
                dataIsOk = True

            elif self.taskIndex == 1:
                # Renderman Render Task
                jobComment = '{# Created by Belal Salem through jobSpooler} '
                jobTitle = '{' + str(self.ui.taskTitle.text()) + '} '
                taskTitle = '{Renders ' + str(jobStart) + '-' + str(jobEnd) + '} '
                taskArgs = '-Progress -cwd '
                taskCmd = 'prman '
                service = '"PixarRender%s" %s' %(extraService, slotOpt)
                tag = '{prman}'
                if taskBaseFilename[-1:] == '.':
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename[:-1] \
                                     + '.' + paddedS + '.tif}'
                else:
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename \
                                    + '.' + paddedS + '.tif}'
                oneRange = ''
                dataIsOk = True

            elif self.taskIndex == 2:
                # Massive Crowd Simulation
                jobComment = '{# Created by Belal Salem through jobSpooler} '
                jobTitle = '{' + str(self.ui.taskTitle.text()) + '} '
                taskTitle = '{Simulating ' + str(jobStart) + '-' + str(jobEnd) + '} '
                subtaskTitle = taskTitle
                taskArgs = '-gui -alf -v '
                taskCmd = 'crowdSim '
                service = '"massive%s" %s' %(extraService, slotOpt)
                tag = '{massive}'
                imagePreview = ''
                oneRange = str(jobStart) + '-' + str(jobEnd) + ' '
                dataIsOk = True

            elif self.taskIndex == 3:
                # Katana Batch Render
                jobComment = '{# Created by Belal Salem through jobSpooler} '
                jobTitle = '{' + str(self.ui.taskTitle.text()) + '} '
                taskTitle = '{Renders ' + str(jobStart) + '-' + str(jobEnd) + '} '
                taskCmd = 'katanaRen '
                taskArgs = '--batch -t '
                service = '"katana%s" %s' %(extraService, slotOpt)
                tag = '{katana}'
                if taskBaseFilename[-1:] == '.':
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename[:-1] + '_beauty.' + paddedS + '.exr}'
                else:
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename + '_beauty.' + paddedS + '.exr}'
                oneRange = str(s) + ' '
                dataIsOk = True

            elif self.taskIndex == 4:
                # Nuke Batch Render
                jobComment = '{# Created by Belal Salem through jobSpooler} '
                jobTitle = '{' + str(self.ui.taskTitle.text()) + '} '
                taskTitle = '{Renders ' + str(jobStart) + '-' + str(jobEnd) + '} '
                taskCmd = '/usr/local/Nuke7.0v10/Nuke7.0 '
                taskArgs = '-f -t '
                service = '"nuke%s" %s' %(extraService, slotOpt)
                tag = '{nuke}'
                if taskBaseFilename[-1:] == '.':
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename[:-1] + '_beauty.' + paddedS + '.exr}'
                else:
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename + '_beauty.' + paddedS + '.exr}'
                oneRange = str(s) + ' '
                dataIsOk = True

            elif self.taskIndex == 5:
                # Maya Batch Render
                mayaLocation = os.getenv('MAYA_LOCATION')
                jobComment = '{# Created by Belal Salem through jobSpooler} '
                jobTitle = '{' + str(self.ui.taskTitle.text()) + '} '
                taskTitle = '{Renders ' + str(jobStart) + '-' + str(jobEnd) + '} '
                taskCmd = '%s/bin/Render '%mayaLocation
                taskArgs = ''
                service = '"PixarRender%s" %s' %(extraService, slotOpt)
                tag = '{prman}'
                if taskBaseFilename[-1:] == '.':
                    if iP is None:
                        imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename[:-1] + '_beauty.' + paddedS + '.exr}'
                    else:
                        imagePreview = '-preview {rv ' + iP + 'beauty_' + taskBaseFilename[:-1] + '.' + paddedS + '.exr}'
                else:
                    if iP is None:
                        imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename + '_beauty.' + paddedS + '.exr}'
                    else:
                        imagePreview = '-preview {rv ' + iP + 'beauty_' + taskBaseFilename + '.' + paddedS + '.exr}'
                oneRange = str(s) + ' '
                dataIsOk = True

            elif self.taskIndex == 6:
                # Maya Batch run command 'Maya script'
                mayaLocation = os.getenv('MAYA_LOCATION')
                jobComment = '{# Created by Belal Salem through jobSpooler} '
                jobTitle = '{' + str(self.ui.taskTitle.text()) + '} '
                taskTitle = '{Renders ' + str(jobStart) + '-' + str(jobEnd) + '} '
                extraArgs = self.extraArgs
                taskCmd = '%s/bin/maya -batch '%mayaLocation
                taskArgs = ''
                service = '"PixarRender%s" %s' %(extraService, slotOpt)
                tag = '{prman}'
                if taskBaseFilename[-1:] == '.':
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename[:-1] + '_beauty.' + paddedS + '.exr}'
                else:
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename + '_beauty.' + paddedS + '.exr}'
                oneRange = str(s) + ' '
                dataIsOk = True
            
            elif self.taskIndex == 8:
                # FumeFX Simulate
                mayaLocation = os.getenv('MAYA_LOCATION')
                jobComment = '{# Created by Belal Salem through jobSpooler} '
                jobTitle = '{' + str(self.ui.taskTitle.text()) + '} '
                taskTitle = '{Renders ' + str(jobStart) + '-' + str(jobEnd) + '} '
                taskCmd = '%s/bin/maya -batch -command '%mayaLocation
                taskArgs = ''
                service = '"PixarRender%s" %s' %(extraService, slotOpt)
                tag = '{prman}'
                if taskBaseFilename[-1:] == '.':
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename[:-1] + '_beauty.' + paddedS + '.exr}'
                else:
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename + '_beauty.' + paddedS + '.exr}'
                oneRange = str(s) + ' '
                dataIsOk = True
            
            elif self.taskIndex == 9:
                # FumeFX Render
                mayaLocation = os.getenv('MAYA_LOCATION')
                jobComment = '{# Created by Belal Salem through jobSpooler} '
                jobTitle = '{' + str(self.ui.taskTitle.text()) + '} '
                taskTitle = '{Renders ' + str(jobStart) + '-' + str(jobEnd) + '} '
                taskCmd = '%s/bin/Render '%mayaLocation
                taskArgs = ''
                service = '"PixarRender%s" %s' %(extraService, slotOpt)
                tag = '{prman}'
                if taskBaseFilename[-1:] == '.':
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename[:-1] + '_beauty.' + paddedS + '.exr}'
                else:
                    imagePreview = '-preview {sho ' + taskPrj + self.slash + 'images' + self.slash + taskBaseFilename + '_beauty.' + paddedS + '.exr}'
                oneRange = str(s) + ' '
                dataIsOk = True

            else:
                pass

            if not header:
                header = True
                if not self.task.isSeq:
                    relativeTaskPath += self.task.ext
                job += '##AlfredToDo 3.0' + '\n'
                job += 'Job -title ' + jobTitle + '-comment ' + jobComment + '-serialsubtasks 0 -pbias %s -subtasks {'%str(self.priority)+ '\n'
                job += '    Task -title ' + taskTitle + '-serialsubtasks 0 -subtasks {' + '\n'

            if self.taskIndex == 5 or self.taskIndex == 9:
                #processingEnd = counter+self.taskSize-1
                processingEnd = counter2+self.taskSize-1
                if processingEnd > self.taskEnd:
                    processingEnd = self.taskEnd
                #subtaskTitle = '{Processing ' + str(counter) + '-' + str(processingEnd)+ '} '
                subtaskTitle = '{Processing ' + str(counter2) + '-' + str(processingEnd)+ '} '
                if counter <= (self.taskEnd):
                    job     += '        Task -title ' + subtaskTitle + '-cmds {' + '\n'
                else:
                    break
            else:
                job         += '        Task -title ' + subtaskTitle + '-cmds {' + '\n'

            if self.taskIndex == 3: # katana treated differently
                            job     += '            RemoteCmd {' + taskCmd + extraArgs + ' ' + taskArgs + oneRange + absTaskPath + \
                                            ' } -service ' + service + '-tags ' + tag + '\n'
            elif self.taskIndex == 4: # Nuke treated differently
                stFrame = str(counter)
                endFrame = int(counter) + self.taskSize - 1
                if endFrame > self.taskEnd:
                    endFrame = self.taskEnd
                endFrame = str(endFrame)
                if self.skipFrames != 0 :
                    counter += self.taskSize + self.skipFrames - 1
                else:
                    counter += self.taskSize + self.skipFrames
                job                 += '            RemoteCmd {' + taskCmd + extraArgs + ' ' + taskArgs + '-x ' + absTaskPath + ' %s-%s'%(stFrame, endFrame) +\
                                            ' } -service ' + service + '-tags ' + tag + '\n'
            elif self.taskIndex == 5 or self.taskIndex == 9: # Maya and FumeFX Render through Maya have also different treatement
                #stFrame = str(counter) + ' '
                #endFrame = int(counter) + self.taskSize - 1
                stFrame = str(counter2) + ' '
                endFrame = int(counter2) + self.taskSize - 1
                if endFrame > self.taskEnd:
                    endFrame = self.taskEnd
                endFrame = str(endFrame)

                '''
                if self.skipFrames !=0:
                    counter += self.taskSize + self.skipFrames - 1
                else:
                    counter += self.taskSize + self.skipFrames
                '''    

                if self.skipFrames !=0:
                    counter2 += self.taskSize + self.skipFrames - 1
                else:
                    counter2 += self.taskSize + self.skipFrames

                job                 += '            RemoteCmd {' + taskCmd + '-s ' + stFrame + '-e ' + endFrame + extraArgs + ' ' + taskArgs + '-proj ' + taskPrj + ' ' + absTaskPath + \
                                            ' } -service ' + service + '-tags ' + tag + '\n'
            elif self.taskIndex == 8 or self.taskIndex == 6: # running cmd/script in maya batch mode
                job                 += '            RemoteCmd {' + taskCmd + extraArgs + ' ' + taskArgs + '-proj ' + taskPrj + ' -file ' + absTaskPath + \
                                            ' } -service ' + service + '-tags ' + tag + '\n'
            else:
                job += '            RemoteCmd {' + taskCmd + extraArgs + ' ' + taskArgs + taskPrj + ' ' + relativeTaskPath + \
                                    ' } -service ' + service + '-tags ' + tag + '\n'
            job     += '        } ' + imagePreview + '\n'

        if 'fox' in self.engine:
            if self.taskIndex == 5 or self.taskIndex == 4:
                # str(self.ui.taskTitle.text())
                # uuid ?
                from uuid import uuid4
                self.uuid = uuid4() 

                bin = "/nas/projects/development/productionTools/pipeline.config/asset_download_blade"
                self.task_uuid = "{0}__{1}".format(self.ui.taskTitle.text(), self.uuid)
                remote_cmd = "{0}  {1}".format(bin, self.task_uuid)

                job += '    } -cmds {RemoteCmd {' + remote_cmd + '} -service ' + service + '-tags ' + tag + ' }' + '\n'
        else:
            job += '    }' + '\n'

        job += '}' + '\n'


        #Write job to the file and close
        if dataIsOk:
            g.write(unicode(job))
            g.close()
            print >>sys.stdout, "Job Generated Successfully! Thanks for using 'Job Spooler'"
            print >>sys.stdout, "by@ Belal Salem, at 'Nothing Real VFX'"
            print >>sys.stdout, "www.nothing-real.com"

            if self.genMsgEnabled:
                Dismiss = 'Dismiss'
                message = QtGui.QMessageBox(self)
                message.setText('The Job Script was Generated Successfully.')
                message.setWindowTitle('Job Script...')
                message.setIcon(QtGui.QMessageBox.Information)
                message.addButton(Dismiss, QtGui.QMessageBox.AcceptRole)
                message.exec_()
                response = message.clickedButton().text()

        else:
            print >>sys.stderr, "OOOPs!!!! Somthing went wrong!!"
            print >>sys.stderr, "Couldn't generate the job script!"

    def sendAlfred(self):
        self.errorCheck()
        if not self.err:
            self.genMsgEnabled = False
            self.genTask()
            self.genMsgEnabled = True
            cmd = 'alfred ' + self.jobFullPath
            os.system(cmd)
            Dismiss = 'Dismiss'
            message = QtGui.QMessageBox(self)
            message.setText('The Job was sent to Alfred Successfully.')
            message.setWindowTitle('Job Script...')
            message.setIcon(QtGui.QMessageBox.Information)
            message.addButton(Dismiss, QtGui.QMessageBox.AcceptRole)
            message.exec_()
            response = message.clickedButton().text()

    def sendToTractor(self, internal=True):
        print >>sys.stderr, "Engine = {0}".format(self.engine)
        published = False
        if self.taskIndex == 5 or self.taskIndex == 4:
            args = '-publish %s -comment \\\"Render Scene\\\"'%self.seqName
            published = self.publishScene(args)

        if internal:
            self.errorCheck()
            if not self.err:
                self.genMsgEnabled = False
                self.genTask()
                
                self.genMsgEnabled = True

                if self.standalone:
                    if self.taskIndex == 5 or self.taskIndex == 4:
                        
                        fileNameOk = runCommands.checkFileNaming(args)
                        if not fileNameOk:
                            self.intError("Please follow the naming convention before submitting a job")
                            return False
                        
                        if published:
                            cmd = 'tractor-spool.py --engine=%s '%self.engine + '"%s"'%self.jobFullPath
                            os.system(cmd)
                        else:
                            cmd = 'tractor-spool.py --engine=%s '%self.engine + '"%s"'%self.jobFullPath
                            os.system(cmd)
                    else:
                        cmd = 'tractor-spool.py --engine=%s '%self.engine + '"%s"'%self.jobFullPath
                        os.system(cmd)
                else:                        
                    if self.taskIndex == 5 or self.taskIndex == 4:                        
                        if published:
                            if 'fox' in self.engine:
                                self.submit_to_remote_tractor()
                                return
                            else:
                                rfm.tractor.Spool(['--engine=%s'%self.engine, '--priority=%s'%str(self.priority), '%s'%self.jobFullPath])
                    else:
                        rfm.tractor.Spool(['--engine=%s'%self.engine, '--priority=%s'%str(self.priority), '%s'%self.jobFullPath])

                self.genMsgEnabled = True
                Dismiss = 'Dismiss'
                message = QtGui.QMessageBox(self)
                message.setText('The Job was sent to Tractor Successfully.')
                message.setWindowTitle('Job Script...')
                message.setIcon(QtGui.QMessageBox.Information)
                message.addButton(Dismiss, QtGui.QMessageBox.AcceptRole)
                message.exec_()
                message.clickedButton().text()
        else: # running as a standalone function
            '''
            self.extraArgs = opt
            self.jobFullPath = tskScript
            self.task=seqInfo(tskFile, False)
            self.prjPath = prjPath
            self.tskStart = start
            self.taskEnd = end
            self.taskFile = tskFile
            '''
            print self.taskFile
            print self.tskStart
            print self.taskEnd
            if self.taskFile and self.tskStart and self.taskEnd:
                print 'Will generate the task and send to tractor'
                self.genTask(internal=False)
                
                if self.taskIndex == 5 or self.taskIndex == 4:
                    args = '-publish %s -comment \\\"Render Scene\\\"'%self.seqName
                    fileNameOk = runCommands.checkFileNaming(args)
                    if not fileNameOk:
                        self.intError("Please follow the naming convention before submitting a job")
                        return False
                                        
                    if published:
                        rfm.tractor.Spool(['--engine=%s'%self.engine, '--priority=%s'%str(self.priority), '%s'%self.jobFullPath])
                else:
                    rfm.tractor.Spool(['--engine=%s'%self.engine, '--priority=%s'%str(self.priority), '%s'%self.jobFullPath])
                    
    def submit_to_remote_tractor(self):
        print >>sys.stderr, self.jobFullPath, self.priority
        print >>sys.stderr, self.ui.qTaskSeq.text()

        from py_queue.sync import find_scene_deps #, submit_to_queue

        (file_path, _) = find_scene_deps.gen2(self.ui.qTaskSeq.text())

        launch_type = None
        # Based on the user action, we may have 3 different types of actions: 
        # 1. Only Syncing of the assets => SYNC
        # 2. Only render spool as the sync might have been previously done => RENDER
        # 3. Both => SYNC_RENDER
        if self.ui.syncChk.isChecked():
            if self.ui.renChk.isChecked():
                launch_type='SYNC_RENDER'
            else:
                launch_type='SYNC'
        elif self.ui.renChk.isChecked():
            launch_type='RENDER'
        else:
            self.dialog_box("Both `Sync` and `Render` can't be unchecked at the same time")
            self.ui.syncChk.setChecked(True)
            self.ui.renChk.setChecked(True)

        if launch_type is not None:
            cmd_str = "{0} {1} {2} {3} {4} {5}".format(Q_SUBMIT_BIN, launch_type, file_path, getpass.getuser(), self.jobFullPath, self.uuid) 
            print >>sys.stderr, cmd_str 
                    
            """
            /nas/projects/development/productionTools/py_queue/bin/submit_to_queue.py SYNC_RENDER 
            /nas/projects/Tactic/bilal/render/.depsTemp/seq13_scn27_sh006_lig_lighting_v008.ma_filtered.lst abhishek 
            /nas/projects/Tactic/sandbox/bilal/abhishek/sequences/seq13/scn27/sh006_SHOT00000128/lighting/lighting/scenes//seq13_scn27_sh006_lig_lighting_v008.alf caf1f7d1-2a42-4810-a171-2973c82de9ed
            """
            # Subprocess to launch the Q_SUBMIT_BIN
            import subprocess
            p = subprocess.Popen([Q_SUBMIT_BIN, launch_type, '{0}'.format(file_path), '{0}'.format(getpass.getuser()), '{0}'.format(self.jobFullPath), '{0}'.format(self.uuid)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (out, err) = p.communicate()
            if err:
                print err
            if out:
                (task_uuid, task_id) = out.split(' : ')
                self.dialog_box('Task: {0} with id: {1} has been successfully submitted to the Queue.'.format(task_uuid, task_id))
            
    def publishScene(self, args):
        '''
        Publishing the scene to tactic
        '''

        '''
        Dismiss = 'No'
        Accept = 'Yes'
        
        message = QtGui.QMessageBox(self)
        message.setText("Would you like to publish this scene to Tactic?\nNote: If this is for final render, YOU SHOULD PRESS 'yes' here.")
        message.setWindowTitle('Publish scene to Tactic...')
        message.setIcon(QtGui.QMessageBox.Information)
        message.addButton(Accept, QtGui.QMessageBox.AcceptRole)
        message.addButton(Dismiss, QtGui.QMessageBox.AcceptRole)
        message.exec_()
        response = message.clickedButton().text()
        '''
        response = 'Yes'
        if response == 'Yes':
            if self.task == 5:
                globalsAreOK = setupSceneGlobals()

                # disable tactic login window and save scene, then enable actions back
                try:
                    if globalsAreOK:
                        closeActionJobs()
                        saveFile()
                        startActionJobs()
                except:
                    pass

                # check for proper naming convention.
                args = '-publish %s -comment \\\"Render Scene\\\"'%self.seqName
                fileNameOk = runCommands.checkFileNaming(args)
                if not fileNameOk:
                    self.intError("Please follow the naming convention before submitting a job")
                    return False

            # publish the task scene
            status = runCommands.runPopenProcess(args, publish="Yes")
            if status[0] == "Files published successful!":
                self.ui.qTaskSeq.setText(status[1])
                return True
            else:
                return True
        else:
            return True
    
    def intError(self, msg=''):
        Confirm = 'Confirm'
        message = QtGui.QMessageBox(self)
        message.setText(msg)
        message.setWindowTitle('jobSpooler...')
        message.setIcon(QtGui.QMessageBox.Warning)
        message.addButton(Confirm, QtGui.QMessageBox.AcceptRole)
        message.exec_()
        response = message.clickedButton().text()
        return response
            
    def dialog_box(self, msg):
        self.genMsgEnabled = True
        Dismiss = 'OK'
        message = QtGui.QMessageBox(self)
        message.setText(msg)
        message.setWindowTitle('Queue submission')
        message.setIcon(QtGui.QMessageBox.Information)
        message.addButton(Dismiss, QtGui.QMessageBox.AcceptRole)
        message.exec_()

    def renCp(self):
        '''
        Calls A python external exec file "seqRename" with the "-cp" option.
        '''
        fullPath = str(self.ui.qTaskSeq.text())
        os.system('seqRename -cp %s' %fullPath + self.tsr )

    def renMv(self):
        '''
        Calls A python external exec file "seqRename" with the '-mv' option.
        '''
        fullPath = str(self.ui.qTaskSeq.text())
        os.system('seqRename -mv %s' %fullPath + self.tsr)

    def render(self):
        prjDir = str(self.ui.qPrjPath.text())
        fullPath = str(self.ui.qTaskSeq.text())
        if self.renderCmd:
            os.system('cd ' + prjDir + '\n' + 'exec ' + self.renderCmd + fullPath + self.tsr)

def showSpooler(tskType = 0, imgPath=None, tskFile=False, prjPath=False, tskScript='', opt='', title='', start=False, end=False, priority=50, taskSize=1):
    tsT = tskType
    tsFile = tskFile
    pPath = prjPath
    tsSc = tskScript
    op = opt
    t = title
    p = priority
    st = start
    e = end
    pT = taskSize
    iP = imgPath
    try:
        if cmds.window(WINDOW_NAME, exists=True, q=True):
            cmds.deleteUI(WINDOW_NAME)
            dialog = None
        dialog = bs_jobSpooler(imgPath=iP, tskType = tsT, tskFile=tsFile, prjPath=pPath, tskScript=tsSc, opt=op, title=t, start=st, end=e, priority=p, taskSize=pT, standalone=False)
        dialog.show()
        return
    except:
        app = QtGui.QApplication(sys.argv)
        myApp = bs_jobSpooler(imgPath=iP, tskType = tsT, tskFile=tsFile, prjPath=pPath, tskScript=tsSc, opt=op, title=t, start=st, end=e, priority=p, taskSize=pT)
        myApp.show()
        sys.exit(app.exec_())
        return
