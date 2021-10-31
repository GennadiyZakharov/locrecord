#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import ConfigParser
from PyQt4 import QtCore,QtGui

# === Cameras ===
rtspStr = 'rtsp://'

vlcStr = '''vlc'''

runTimeStr ='''--run-time {}'''
sout1Str = '''--sout="#duplicate{dst=std{access=file,mux=avi,'''
dstStr = '''dst="{}"'''
sout2Str = '''}, dst=display}" vlc://quit'''

title = "VLC video recorder"

class MainWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle(title)
        self.setObjectName("MainWindow")
        self.fileName = QtCore.QString()
        self.cameras = []
        self.cameraNumber = 0
           
        self.loadCameras()     
        if self.cameras == []:
            print 'No cameras avaliable, exiting'
            exit(-1)
        
        layout= QtGui.QGridLayout()
        
        cameraLabel = QtGui.QLabel("Camera: ")
        layout.addWidget(cameraLabel,0,0)
        cameraSelector = QtGui.QComboBox()
        cameraSelector.addItems([camera['name'] for camera in self.cameras])
        cameraSelector.currentIndexChanged.connect(self.selectCamera)
        layout.addWidget(cameraSelector,0,2)
        cameraSelector.setCurrentIndex(0)
        
        fileNameLabel = QtGui.QLabel("Output file Name: ")
        layout.addWidget(fileNameLabel,1,0)
        fileNameBrowse = QtGui.QPushButton("Browse...")
        fileNameBrowse.clicked.connect(self.browse)
        layout.addWidget(fileNameBrowse,1,2)
        self.fileNameEdit = QtGui.QLineEdit()
        self.fileNameEdit.textChanged.connect(self.checkFileName)
        layout.addWidget(self.fileNameEdit,2,0,1,3)
        #
        durationLabel = QtGui.QLabel('Duration, min:')
        layout.addWidget(durationLabel,3,0)
        self.durationSpinBox = QtGui.QSpinBox()
        self.durationSpinBox.setMinimum(5)
        self.durationSpinBox.setMaximum(120)        
        layout.addWidget(self.durationSpinBox,3,1)
        setTimeStampButton = QtGui.QPushButton("Set time stamp")
        setTimeStampButton.clicked.connect(self.setTimeStamp)
        layout.addWidget(setTimeStampButton,3,2)
        
        self.previewButton = QtGui.QPushButton("Preview")
        layout.addWidget(self.previewButton,4,0)
        self.previewButton.clicked.connect(self.preview)
        #
        self.processButton = QtGui.QPushButton("<< Start >>")
        layout.addWidget(self.processButton,4,1,1,2)
        self.processButton.clicked.connect(self.process)
        
        self.setLayout(layout)
        #
        self.controls = [fileNameBrowse,self.fileNameEdit,self.durationSpinBox,setTimeStampButton,
                         self.previewButton,self.processButton]
        # Restoring settings
        settings = QtCore.QSettings()
        self.fileNameEdit.setText(settings.value("LastFile").toString())
        duration, isPresent = settings.value("Duration").toInt()
        if isPresent :
            self.durationSpinBox.setValue(duration)
        else :
            self.durationSpinBox.setValue(60)
        self.restoreGeometry(settings.value("Geometry").toByteArray())
        
    def loadCameras(self):
        print 'loading cameras'
        config = ConfigParser.ConfigParser()
        filelist = config.read("/opt/cameras.ini")
        for camera in config.sections():
            print camera
            cameraDict={'name':camera}
            options = config.options(camera)
            for option in options:
                try:
                    cameraDict[option] = config.get(camera, option)
                    if cameraDict[option] == -1:
                        DebugPrint("skip: %s" % option)
                except:
                    print("exception on %s!" % option)
                    del cameraDict[option]
            print cameraDict
            self.cameras.append(cameraDict)
        
    def selectCamera(self, cameraNumber):
        self.cameraNumber = cameraNumber

    def enableControls(self, enabled):
        for item in self.controls :
            item.setEnabled(enabled)
    
    def browse(self):
        
        currentDir = QtCore.QFileInfo(self.fileName).absolutePath() \
            if not self.fileName.isEmpty() else "."
        # Executing standard open dialog
        fname = QtGui.QFileDialog.getSaveFileName(self, 
                        QtGui.QApplication.applicationName()+ " - Choose file",
                        currentDir, "Video files (*.avi)")
        if not fname.isEmpty():
            self.fileNameEdit.setText(fname)

    def checkFileName(self, name):
        self.fileName =  name
        self.processButton.setEnabled(not name.isEmpty())

    def setTimeStamp(self):
        currentDate = QtCore.QDate.currentDate().toString('yyyy-MM-dd')+'_'
        fileInfo = QtCore.QFileInfo(self.fileName)
        baseName = fileInfo.fileName()
        baseName = baseName.remove(QtCore.QRegExp('^20[0-9][0-9]-[0-1][0-9]-[0-3][0-9]_'))
        fullName = fileInfo.absolutePath()+currentDate+baseName
        self.fileNameEdit.setText(fullName)
    
    def urlStr(self):
        camera = self.cameras[self.cameraNumber]
        creditals = camera['creditals']+'@' if camera['creditals'] != '' else ''
        cameraUrl=rtspStr+creditals+camera['ip']+':'+str(camera['port'])+'/'+camera['address']
        print 'Camera:'+camera['name']+' '+cameraUrl
        return cameraUrl
    
    def preview(self):
        self.startVlc(vlcStr + ' ' + self.urlStr())

    
    def startVlc(self,runString):
        print 'Starting VLC'
        print runString
        vlc = QtCore.QProcess(self);
        vlc.finished.connect(self.vlcFinished)
        self.runflag = True
        self.enableControls(False)
        vlc.start(runString)
        while self.runflag :
            QtGui.QApplication.processEvents()
        self.enableControls(True)
    
    def vlcFinished(self):
        self.runflag=False
    
    def process(self):
        if QtCore.QFile(self.fileName).exists() :
            QtGui.QMessageBox.about(self, "VLC-Based video recorder",
            'File already exsts!<p><b>'+self.fileName+'</b><p>Please select another one')
            return
        time = self.durationSpinBox.value()*60
        runString = vlcStr +' '+ self.urlStr() +' '+ runTimeStr.format(time) + ' ' + \
                    sout1Str + dstStr.format(self.fileName.trimmed()) + sout2Str
        self.startVlc(runString)

    def closeEvent(self, event):
        # Save settings and exit
        settings = QtCore.QSettings()
        settings.setValue("LastFile", self.fileName)
        settings.setValue("Duration", self.durationSpinBox.value())
        settings.setValue("Geometry", QtCore.QVariant(self.saveGeometry()))

def main():
    app = QtGui.QApplication(sys.argv)
    app.setOrganizationName("I.P. Pavlov Physiology Institute")
    app.setOrganizationDomain("infran.ru")
    app.setApplicationName(title)
    #app.setWindowIcon(QIcon(":/icon.png"))
    mainWindow = MainWindow()
    mainWindow.show()
    return app.exec_()

if __name__ == '__main__':
    main()
