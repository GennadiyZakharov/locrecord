#!/usr/bin/env python

import sys
import os
import configparser
import regex as re
from PyQt5 import QtCore, QtGui, QtWidgets

from locrecord_pyuic import Ui_MainWindow

# === Cameras ===
rtspStr = 'rtsp://'
vlcStr = '''vlc'''

run_time_str = '''--run-time {}'''
sout_1_str = '''--sout="#duplicate{dst=std{access=file,mux=avi,'''
dstStr = '''dst="{}"'''
sout_2_str = '''}, dst=display}" vlc://quit'''

title = "VLC video recorder"


class MainWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.is_vlc_running = False
        self.setWindowTitle(title)
        self.setObjectName("MainWindow")
        self.fileName = ""
        self.cameras = []
        self.cameraNumber = 0
        self.load_cameras()
        # noinspection PySimplifyBooleanCheck
        if self.cameras == []:
            print('No cameras available, exiting')
            exit(-1)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.camera_selector.addItems([camera['name'] for camera in self.cameras])
        # noinspection PyUnresolvedReferences
        self.ui.camera_selector.currentIndexChanged.connect(self.select_camera)
        self.ui.camera_selector.setCurrentIndex(0)

        self.ui.file_name_browse.clicked.connect(self.browse)
        self.ui.fileNameEdit.textChanged.connect(self.set_output_file_name)
        #
        self.ui.set_time_stamp_button.clicked.connect(self.set_time_stamp)

        self.ui.previewButton.clicked.connect(self.preview)
        #
        self.ui.processButton.clicked.connect(self.process)

        #
        self.controls = [self.ui.file_name_browse, self.ui.fileNameEdit, self.ui.durationSpinBox, self.ui.set_time_stamp_button,
                         self.ui.previewButton, self.ui.processButton]
        # Restoring settings
        settings = QtCore.QSettings()
        self.ui.fileNameEdit.setText(settings.value("LastFile") if settings.value("LastFile") is not None else "")
        duration = settings.value("Duration")
        if duration is not None:
            self.ui.durationSpinBox.setValue(int(duration))
        if settings.value("Geometry") is not None:
            self.restoreGeometry(settings.value("Geometry"))

    def load_cameras(self):
        print('loading cameras')
        config = configparser.ConfigParser()
        config.read("./cameras.ini")
        for camera in config.sections():
            print(camera)
            camera_dict = {'name': camera}
            options = config.options(camera)
            for option in options:
                try:
                    camera_dict[option] = config.get(camera, option)
                    if camera_dict[option] == -1:
                        print("skip: %s" % option)
                except:
                    print("exception on %s!" % option)
                    del camera_dict[option]
            print(camera_dict)
            self.cameras.append(camera_dict)

    def select_camera(self, camera_number):
        self.cameraNumber = camera_number

    def enable_controls(self, enabled):
        for item in self.controls:
            item.setEnabled(enabled)

    def browse(self):

        current_dir: str = QtCore.QFileInfo(self.fileName).absolutePath() \
            if self.fileName != "" else "."
        # Executing standard open dialog
        fname = QtWidgets.QFileDialog.getSaveFileName(self,
                                                      QtWidgets.QApplication.applicationName() + " - Choose file",
                                                      current_dir, "Video files (*.avi)")
        print(fname)
        if fname != "":
            self.ui.fileNameEdit.setText(fname[0])

    def set_output_file_name(self, name):
        self.fileName = name
        self.ui.processButton.setEnabled(name != '')

    def set_time_stamp(self):
        file_info = QtCore.QFileInfo(self.fileName)
        base_name = file_info.fileName()
        base_name = re.sub(r'^20[0-9][0-9]-[0-1][0-9]-[0-3][0-9]_', '', base_name)
        current_date = QtCore.QDate.currentDate().toString('yyyy-MM-dd') + '_'
        full_name = os.path.join(file_info.absolutePath(), current_date + base_name)
        self.ui.fileNameEdit.setText(full_name)

    def make_camera_url(self):
        camera = self.cameras[self.cameraNumber]
        credentials = camera['credentials'] + '@' if camera['credentials'] != '' else ''
        camera_url = rtspStr + credentials + camera['ip'] + ':' + str(camera['port']) + '/' + camera['address']
        return camera_url

    def preview(self):
        self.start_vlc(vlcStr + ' ' + self.make_camera_url())

    def start_vlc(self, vlc_run_string):
        print('Starting VLC')
        print(vlc_run_string)
        vlc = QtCore.QProcess(self)
        vlc.finished.connect(self.vlc_finished)
        self.is_vlc_running = True
        self.enable_controls(False)
        vlc.start(vlc_run_string)
        while self.is_vlc_running:
            QtWidgets.QApplication.processEvents()
        self.enable_controls(True)

    def vlc_finished(self):
        self.is_vlc_running = False

    def process(self):
        if QtCore.QFile(self.fileName).exists():
            QtGui.QMessageBox.about(self, "VLC-Based video recorder",
                                    'File already exsts!<p><b>' + self.fileName + '</b><p>Please select another one')
            return
        time = self.ui.durationSpinBox.value() * 60
        vlc_run_string = vlcStr + ' ' + self.make_camera_url() + ' ' + run_time_str.format(time) + ' ' + \
                         sout_1_str + dstStr.format(self.fileName.strip()) + sout_2_str
        self.start_vlc(vlc_run_string)

    def closeEvent(self, event):
        # Save settings and exit
        settings = QtCore.QSettings()
        settings.setValue("LastFile", self.fileName)
        settings.setValue("Duration", self.ui.durationSpinBox.value())
        settings.setValue("Geometry", QtCore.QVariant(self.saveGeometry()))


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName("I.P. Pavlov Physiology Institute")
    app.setOrganizationDomain("infran.ru")
    app.setApplicationName(title)
    # app.setWindowIcon(QIcon(":/icon.png"))
    main_window = MainWindow()
    main_window.show()
    return app.exec_()


if __name__ == '__main__':
    main()
