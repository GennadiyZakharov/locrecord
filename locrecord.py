#!/usr/bin/env python

import sys
import os
import configparser
import regex as re
from PyQt5 import QtCore, QtGui, QtWidgets

# === Cameras ===
rtspStr = 'rtsp://'
vlcStr = '''vlc'''

runTimeStr = '''--run-time {}'''
sout1Str = '''--sout="#duplicate{dst=std{access=file,mux=avi,'''
dstStr = '''dst="{}"'''
sout2Str = '''}, dst=display}" vlc://quit'''

title = "VLC video recorder"


class MainWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle(title)
        self.setObjectName("MainWindow")
        self.fileName = ""
        self.cameras = []
        self.cameraNumber = 0
        self.loadCameras()
        if self.cameras == []:
            print('No cameras avaliable, exiting')
            exit(-1)

        layout = QtWidgets.QGridLayout()

        camera_label = QtWidgets.QLabel("Camera: ")
        layout.addWidget(camera_label, 0, 0)
        camera_selector = QtWidgets.QComboBox()
        camera_selector.addItems([camera['name'] for camera in self.cameras])
        camera_selector.currentIndexChanged.connect(self.selectCamera)
        layout.addWidget(camera_selector, 0, 2)
        camera_selector.setCurrentIndex(0)

        file_name_label = QtWidgets.QLabel("Output file Name: ")
        layout.addWidget(file_name_label, 1, 0)
        fileNameBrowse = QtWidgets.QPushButton("Browse...")
        fileNameBrowse.clicked.connect(self.browse)
        layout.addWidget(fileNameBrowse, 1, 2)
        self.fileNameEdit = QtWidgets.QLineEdit()
        self.fileNameEdit.textChanged.connect(self.checkFileName)
        layout.addWidget(self.fileNameEdit, 2, 0, 1, 3)
        #
        durationLabel = QtWidgets.QLabel('Duration, min:')
        layout.addWidget(durationLabel, 3, 0)
        self.durationSpinBox = QtWidgets.QSpinBox()
        self.durationSpinBox.setMinimum(5)
        self.durationSpinBox.setMaximum(120)
        layout.addWidget(self.durationSpinBox, 3, 1)
        setTimeStampButton = QtWidgets.QPushButton("Set time stamp")
        setTimeStampButton.clicked.connect(self.setTimeStamp)
        layout.addWidget(setTimeStampButton, 3, 2)

        self.previewButton = QtWidgets.QPushButton("Preview")
        layout.addWidget(self.previewButton, 4, 0)
        self.previewButton.clicked.connect(self.preview)
        #
        self.processButton = QtWidgets.QPushButton("<< Start >>")
        layout.addWidget(self.processButton, 4, 1, 1, 2)
        self.processButton.clicked.connect(self.process)

        self.setLayout(layout)
        #
        self.controls = [fileNameBrowse, self.fileNameEdit, self.durationSpinBox, setTimeStampButton,
                         self.previewButton, self.processButton]
        # Restoring settings
        settings = QtCore.QSettings()
        self.fileNameEdit.setText(settings.value("LastFile") if settings.value("LastFile") is not None else "")
        duration = settings.value("Duration")
        if duration is not None:
            self.durationSpinBox.setValue(int(duration))
        else:
            self.durationSpinBox.setValue(60)
        if settings.value("Geometry") is not None:
            self.restoreGeometry(settings.value("Geometry"))

    def loadCameras(self):
        print('loading cameras')
        config = configparser.ConfigParser()
        filelist = config.read("./cameras.ini")
        for camera in config.sections():
            print(camera)
            cameraDict = {'name': camera}
            options = config.options(camera)
            for option in options:
                try:
                    cameraDict[option] = config.get(camera, option)
                    if cameraDict[option] == -1:
                        print("skip: %s" % option)
                except:
                    print("exception on %s!" % option)
                    del cameraDict[option]
            print(cameraDict)
            self.cameras.append(cameraDict)

    def selectCamera(self, cameraNumber):
        self.cameraNumber = cameraNumber

    def enableControls(self, enabled):
        for item in self.controls:
            item.setEnabled(enabled)

    def browse(self):

        currentDir = QtCore.QFileInfo(self.fileName).absolutePath() \
            if self.fileName != "" else "."
        # Executing standard open dialog
        fname = QtWidgets.QFileDialog.getSaveFileName(self,
                                                      QtWidgets.QApplication.applicationName() + " - Choose file",
                                                      currentDir, "Video files (*.avi)")
        print(fname)
        if fname != "":
            self.fileNameEdit.setText(fname[0])

    def checkFileName(self, name):
        self.fileName = name
        self.processButton.setEnabled(name != '')

    def setTimeStamp(self):
        fileInfo = QtCore.QFileInfo(self.fileName)
        baseName = fileInfo.fileName()
        re.sub(r'^20[0-9][0-9]-[0-1][0-9]-[0-3][0-9]_', '', baseName)
        #baseName = baseName.remove(QtCore.QRegExp('^20[0-9][0-9]-[0-1][0-9]-[0-3][0-9]_'))
        currentDate = QtCore.QDate.currentDate().toString('yyyy-MM-dd') + '_'
        fullName = os.path.join(fileInfo.absolutePath(), currentDate + baseName)
        self.fileNameEdit.setText(fullName)

    def urlStr(self):
        camera = self.cameras[self.cameraNumber]
        creditals = camera['creditals'] + '@' if camera['creditals'] != '' else ''
        cameraUrl = rtspStr + creditals + camera['ip'] + ':' + str(camera['port']) + '/' + camera['address']
        print('Camera:' + camera['name'] + ' ' + cameraUrl)
        return cameraUrl

    def preview(self):
        self.startVlc(vlcStr + ' ' + self.urlStr())

    def startVlc(self, runString):
        print('Starting VLC')
        print(runString)
        vlc = QtCore.QProcess(self)
        vlc.finished.connect(self.vlcFinished)
        self.runflag = True
        self.enableControls(False)
        vlc.start(runString)
        while self.runflag:
            QtWidgets.QApplication.processEvents()
        self.enableControls(True)

    def vlcFinished(self):
        self.runflag = False

    def process(self):
        if QtCore.QFile(self.fileName).exists():
            QtGui.QMessageBox.about(self, "VLC-Based video recorder",
                                    'File already exsts!<p><b>' + self.fileName + '</b><p>Please select another one')
            return
        time = self.durationSpinBox.value() * 60
        runString = vlcStr + ' ' + self.urlStr() + ' ' + runTimeStr.format(time) + ' ' + \
                    sout1Str + dstStr.format(self.fileName.strip()) + sout2Str
        self.startVlc(runString)

    def closeEvent(self, event):
        # Save settings and exit
        settings = QtCore.QSettings()
        settings.setValue("LastFile", self.fileName)
        settings.setValue("Duration", self.durationSpinBox.value())
        settings.setValue("Geometry", QtCore.QVariant(self.saveGeometry()))


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName("I.P. Pavlov Physiology Institute")
    app.setOrganizationDomain("infran.ru")
    app.setApplicationName(title)
    # app.setWindowIcon(QIcon(":/icon.png"))
    mainWindow = MainWindow()
    mainWindow.show()
    return app.exec_()


if __name__ == '__main__':
    main()
