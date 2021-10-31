#!/usr/bin/env python

import sys
import os
import configparser
import regex as re
from PyQt5 import QtCore, QtGui, QtWidgets

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

        layout = QtWidgets.QGridLayout()

        camera_label = QtWidgets.QLabel("Camera: ")
        layout.addWidget(camera_label, 0, 0)
        camera_selector = QtWidgets.QComboBox()
        camera_selector.addItems([camera['name'] for camera in self.cameras])
        # noinspection PyUnresolvedReferences
        camera_selector.currentIndexChanged.connect(self.select_camera)
        layout.addWidget(camera_selector, 0, 2)
        camera_selector.setCurrentIndex(0)

        file_name_label = QtWidgets.QLabel("Output file Name: ")
        layout.addWidget(file_name_label, 1, 0)
        file_name_browse = QtWidgets.QPushButton("Browse...")
        file_name_browse.clicked.connect(self.browse)
        layout.addWidget(file_name_browse, 1, 2)
        self.fileNameEdit = QtWidgets.QLineEdit()
        self.fileNameEdit.textChanged.connect(self.set_output_file_name)
        layout.addWidget(self.fileNameEdit, 2, 0, 1, 3)
        #
        duration_label = QtWidgets.QLabel('Duration, min:')
        layout.addWidget(duration_label, 3, 0)
        self.durationSpinBox = QtWidgets.QSpinBox()
        self.durationSpinBox.setMinimum(5)
        self.durationSpinBox.setMaximum(120)
        layout.addWidget(self.durationSpinBox, 3, 1)
        set_time_stamp_button = QtWidgets.QPushButton("Set time stamp")
        set_time_stamp_button.clicked.connect(self.set_time_stamp)
        layout.addWidget(set_time_stamp_button, 3, 2)

        self.previewButton = QtWidgets.QPushButton("Preview")
        layout.addWidget(self.previewButton, 4, 0)
        self.previewButton.clicked.connect(self.preview)
        #
        self.processButton = QtWidgets.QPushButton("<< Start >>")
        layout.addWidget(self.processButton, 4, 1, 1, 2)
        self.processButton.clicked.connect(self.process)

        self.setLayout(layout)
        #
        self.controls = [file_name_browse, self.fileNameEdit, self.durationSpinBox, set_time_stamp_button,
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
            self.fileNameEdit.setText(fname[0])

    def set_output_file_name(self, name):
        self.fileName = name
        self.processButton.setEnabled(name != '')

    def set_time_stamp(self):
        file_info = QtCore.QFileInfo(self.fileName)
        base_name = file_info.fileName()
        base_name = re.sub(r'^20[0-9][0-9]-[0-1][0-9]-[0-3][0-9]_', '', base_name)
        current_date = QtCore.QDate.currentDate().toString('yyyy-MM-dd') + '_'
        full_name = os.path.join(file_info.absolutePath(), current_date + base_name)
        self.fileNameEdit.setText(full_name)

    def make_camera_url(self):
        camera = self.cameras[self.cameraNumber]
        credentials = camera['credentials'] + '@' if camera['credentials'] != '' else ''
        camera_url = rtspStr + credentials + camera['ip'] + ':' + str(camera['port']) + '/' + camera['address']
        print('Camera:' + camera['name'] + ' ' + camera_url)
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
        time = self.durationSpinBox.value() * 60
        vlc_run_string = vlcStr + ' ' + self.make_camera_url() + ' ' + run_time_str.format(time) + ' ' + \
                         sout_1_str + dstStr.format(self.fileName.strip()) + sout_2_str
        self.start_vlc(vlc_run_string)

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
    main_window = MainWindow()
    main_window.show()
    return app.exec_()


if __name__ == '__main__':
    main()
