#!/usr/bin/python
# -*- coding: UTF-8 -*-
import random
import sys
import cv2

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QPalette, QBrush, QPixmap
import os
import time
import numpy as np
from driver_detection import Face_mesh
from UI.ui_driver import Ui_Form
from pygame import mixer

FULLSCREEN = False

# Set Qt platform plugin path from PyQt5 (PySide2 not compatible with Python 3.12)
import PyQt5
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins', 'platforms')

class Driver_Monitoring_System():
    def __init__(self):
        self.timer_camera = QtCore.QTimer()
        self.cap = cv2.VideoCapture()
        self.fm = Face_mesh()
        self.CAM_NUM = 0
        self.sound_file = "./UI/alarm.mp3"
        self.sound_play = False
        self.last_play = False
        mixer.init()
        mixer.music.load(self.sound_file)
        self.set_ui()
        self.slot_init()
        self.__flag_work = 0
        self.count = 0
        self.fps = []
        self.aver_fps = 0

    def set_ui(self):
        self.MainWindow = QMainWindow()
        self.ui = Ui_Form()
        self.ui.setupUi(self.MainWindow)
        r = self.ui.ratio

        # Load icons/images once at original resolution; we will resize per frame
        self.green_drinking_orig = cv2.cvtColor(cv2.imread('./UI/green_drinking.png'), cv2.COLOR_BGR2RGB)
        self.green_phoning_orig  = cv2.cvtColor(cv2.imread('./UI/green_phoning.png'),  cv2.COLOR_BGR2RGB)
        self.green_texting_orig  = cv2.cvtColor(cv2.imread('./UI/green_texting.png'),  cv2.COLOR_BGR2RGB)
        self.red_drinking_orig   = cv2.cvtColor(cv2.imread('./UI/red_drinking.png'),   cv2.COLOR_BGR2RGB)
        self.red_phoning_orig    = cv2.cvtColor(cv2.imread('./UI/red_phoning.png'),    cv2.COLOR_BGR2RGB)
        self.red_texting_orig    = cv2.cvtColor(cv2.imread('./UI/red_texting.png'),    cv2.COLOR_BGR2RGB)
        self.happy_orig          = cv2.cvtColor(cv2.imread('./UI/happy.jpg'),          cv2.COLOR_BGR2RGB)
        self.angry_orig          = cv2.cvtColor(cv2.imread('./UI/angry.jpg'),          cv2.COLOR_BGR2RGB)

        self.MainWindow.setWindowTitle("Driver monitoring system       AutoMan @ NTU")
        self.MainWindow.setWindowIcon(QtGui.QIcon('AutoMan.ico'))

        button_color = [self.ui.button_open_camera, self.ui.button_close]
        for i in range(2):
            button_color[i].setStyleSheet("QPushButton{color:black}"
                                        "QPushButton:hover{color:red}"
                                        "QPushButton{background-color:rgb(246,197,18)}"
                                        "QPushButton{border:2px}"
                                        "QPushButton{border-radius:6px}"
                                        "QPushButton{padding:2px 2px}")

        self.ui.button_open_camera.setMinimumHeight(int(20 * r))
        self.ui.button_close.setMinimumHeight(int(20 * r))

        self.xdata = list(range(len(self.fm.yawn_interval)))
        self.ydata = [1/(interval + 0.00000001) for interval in self.fm.yawn_interval]
        self.x = list(range(len(self.fm.blink_interval)))
        self.y = [1/(interval + 0.00000001) for interval in self.fm.blink_interval]

    def update_plot(self):
        self.xdata = list(range(len(self.fm.yawn_interval)))
        self.ydata = [1 / (interval + 0.00000001) for interval in self.fm.yawn_interval]
        self.ui.canvas1.axes.cla()
        self.ui.canvas1.axes.plot(self.xdata, self.ydata, 'orange', alpha=1)
        self.ui.canvas1.axes.set_ylim(bottom=0, top=40)
        self.ui.canvas1.axes.fill_between(self.xdata, self.ydata, y2=0, color='orange', alpha=1, label='area')
        self.ui.canvas1.draw()

        self.x = list(range(len(self.fm.blink_interval)))
        self.y = [1 / (interval + 0.00000001) for interval in self.fm.blink_interval]
        self.ui.canvas2.axes.cla()
        self.ui.canvas2.axes.plot(self.x, self.y, 'b', alpha=1)
        self.ui.canvas2.axes.set_ylim(bottom=0, top=3000000)
        self.ui.canvas2.axes.fill_between(self.x, self.y, y2=0, color='b', alpha=1, label='area')
        self.ui.canvas2.draw()


    def slot_init(self):
        self.ui.button_open_camera.clicked.connect(self.button_open_camera_click)
        self.timer_camera.timeout.connect(self.show_camera)
        self.ui.button_close.clicked.connect(QCoreApplication.instance().quit)


    def button_open_camera_click(self):
        if self.timer_camera.isActive() == False:
            flag = self.cap.open(self.CAM_NUM)
            if flag == False:
                msg = QtWidgets.QMessageBox.warning(self, u"Warning", u"Please check the connection of camera!",
                                                    buttons=QtWidgets.QMessageBox.Ok,
                                                    defaultButton=QtWidgets.QMessageBox.Ok)
            else:
                self.timer_camera.start(30)
                self.ui.button_open_camera.setText(u'Close Camera')
        else:
            self.timer_camera.stop()
            self.cap.release()
            self.ui.camera_show.clear()
            self.ui.button_open_camera.setText(u'Open Camera')

    def show_camera(self):
        start_time = time.time()
        flag, self.image = self.cap.read()
        if not flag:
            self.cap.open(self.CAM_NUM)
            return

        # Process algorithm output
        output = self.fm.get_3D_face_mesh(self.image)

        # Sizes from current UI (responsive)
        cam_w, cam_h = self.ui.camera_show.width(), self.ui.camera_show.height()
        mesh_w, mesh_h = self.ui.face_mesh.width(), self.ui.face_mesh.height()
        le_w, le_h = self.ui.left_eye.width(), self.ui.left_eye.height()
        re_w, re_h = self.ui.right_eye.width(), self.ui.right_eye.height()
        mouth_w, mouth_h = self.ui.mouth.width(), self.ui.mouth.height()

        # Prepare camera frame to fit its QLabel
        show = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        if cam_w > 0 and cam_h > 0:
            show = cv2.resize(show, (cam_w, cam_h), interpolation=cv2.INTER_AREA)

        # Draw top bar and text using proportions relative to cam_w, cam_h
        # Base reference was 640x480 and bar 40px -> use proportional height
        bar_h = max(1, int(40/480.0 * cam_h))
        if bar_h > 0:
            cv2.rectangle(show, (0, 0), (cam_w, bar_h), color=(180, 180, 180), thickness=-1)
        # Font scale based on height; thickness based on scale
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.3, 0.6 * (cam_h / 480.0))
        thickness = max(1, int(2 * (cam_h / 480.0)))

        # We will compute FPS later; print placeholder here and update after computing aver_fps
        cv2.putText(show, f"FPS: {self.aver_fps:.2f}", (int(10/640.0*cam_w), min(bar_h - 5, int(30/480.0*cam_h))),
                    font, font_scale, (0, 0, 255), thickness)

        # Abnormal behavior icons positions (based on original 640x480 coordinates used in legacy code)
        # Original ranges:
        # 50..110, 120..180, 190..250 y; x 530..590 -> 60x60 icons with 10px vertical gaps
        icon_w = max(1, int(60/640.0 * cam_w))
        icon_h = max(1, int(60/480.0 * cam_h))
        icon_x = int(530/640.0 * cam_w)
        y1 = int(50/480.0 * cam_h)
        y2 = int(120/480.0 * cam_h)
        y3 = int(190/480.0 * cam_h)

        # Prepare icons per current size
        green_drinking = cv2.resize(self.green_drinking_orig, (icon_w, icon_h), interpolation=cv2.INTER_AREA)
        green_phoning  = cv2.resize(self.green_phoning_orig,  (icon_w, icon_h), interpolation=cv2.INTER_AREA)
        green_texting  = cv2.resize(self.green_texting_orig,  (icon_w, icon_h), interpolation=cv2.INTER_AREA)
        red_drinking   = cv2.resize(self.red_drinking_orig,   (icon_w, icon_h), interpolation=cv2.INTER_AREA)
        red_phoning    = cv2.resize(self.red_phoning_orig,    (icon_w, icon_h), interpolation=cv2.INTER_AREA)
        red_texting    = cv2.resize(self.red_texting_orig,    (icon_w, icon_h), interpolation=cv2.INTER_AREA)

        # Place green icons by default
        if icon_x + icon_w <= cam_w and y1 + icon_h <= cam_h:
            show[y1:y1+icon_h, icon_x:icon_x+icon_w] = green_drinking
        if icon_x + icon_w <= cam_w and y2 + icon_h <= cam_h:
            show[y2:y2+icon_h, icon_x:icon_x+icon_w] = green_phoning
        if icon_x + icon_w <= cam_w and y3 + icon_h <= cam_h:
            show[y3:y3+icon_h, icon_x:icon_x+icon_w] = green_texting

        # Prepare other images to their label sizes
        annotated_image = cv2.cvtColor(output[1], cv2.COLOR_BGR2RGB)
        left_eye = cv2.cvtColor(output[2], cv2.COLOR_BGR2RGB)
        right_eye = cv2.cvtColor(output[3], cv2.COLOR_BGR2RGB)
        mouth = cv2.cvtColor(output[4], cv2.COLOR_BGR2RGB)

        if mesh_w > 0 and mesh_h > 0:
            annotated_image = cv2.resize(annotated_image, (mesh_w, mesh_h), interpolation=cv2.INTER_AREA)
        if le_w > 0 and le_h > 0:
            left_eye = cv2.resize(left_eye, (le_w, le_h), interpolation=cv2.INTER_AREA)
        if re_w > 0 and re_h > 0:
            right_eye = cv2.resize(right_eye, (re_w, re_h), interpolation=cv2.INTER_AREA)
        if mouth_w > 0 and mouth_h > 0:
            mouth = cv2.resize(mouth, (mouth_w, mouth_h), interpolation=cv2.INTER_AREA)

        # Compute metrics
        head_roll  = np.sum(self.fm.angle_roll) / len(self.fm.angle_roll)
        head_yaw   = np.sum(self.fm.angle_yaw) / len(self.fm.angle_yaw)
        head_pitch = np.sum(self.fm.angle_pitch) / len(self.fm.angle_pitch)
        gaze_pitch = np.sum(self.fm.gaze_pitch) / len(self.fm.gaze_pitch)
        gaze_yawn  = np.sum(self.fm.gaze_yaw) / len(self.fm.gaze_yaw)

        self.ui.gaze_pitch.setText(f"{gaze_pitch:.1f}")
        self.ui.gaze_yaw.setText(f"{gaze_yawn:.1f}")

        expression_score = 0
        behavior_score = 0

        head_yaw_score   = 60 / 40 * head_yaw if head_yaw > 0 else -head_yaw
        head_pitch_score = 2 * head_pitch if head_pitch > 0 else -2 * head_pitch
        gaze_yawn_score  = 60 / 50 * gaze_yawn if gaze_yawn > 0 else -gaze_yawn
        gaze_pitch_score = 60 / 40 * gaze_pitch if gaze_pitch > 0 else -3 * gaze_pitch

        dis_score = np.max([head_yaw_score, head_pitch_score, gaze_yawn_score, gaze_pitch_score])
        if self.fm.eye_close or self.fm.yawning:
            distraction_score = dis_score / 10
        elif dis_score < 52:
            distraction_score = dis_score / (53 - dis_score)
        else:
            distraction_score = dis_score

        drowsiness_score1 = self.fm.blink_duration / 100 * 33 + 6 * (len(self.fm.blink_frequency) - 2)
        drowsiness_score2 = self.fm.yawn_duration / 100 * 33 + 20 * (len(self.fm.yawn_frequency) - 1)
        drowsiness_score = np.min([drowsiness_score1, drowsiness_score2, 0])

        if self.fm.abnormal_behaviour in ['drinking', 'answering the phone', 'texting with phone']:
            distraction_score = dis_score / 10
            drowsiness_score = drowsiness_score / 10
            behavior_score = self.fm.behaviour_score
        if self.fm.expression in ['Happy', 'Angry']:
            distraction_score = dis_score / 10
            drowsiness_score = drowsiness_score / 10
            expression_score = self.fm.expression_score

        # Status label on top bar
        status_text = "Abnormal detected!!!" if self.fm.abnormal_behaviour in ['drinking', 'answering the phone', 'texting with phone'] else "---Normal driving---"
        status_color = (255, 0, 0) if "Abnormal" in status_text else (0, 255, 0)
        cv2.putText(show, status_text, (int(230/640.0 * cam_w), min(bar_h - 5, int(26/480.0 * cam_h))),
                    font, font_scale, status_color, thickness)

        # Replace icons with red if abnormal
        if self.fm.abnormal_behaviour == 'drinking' and icon_x + icon_w <= cam_w and y1 + icon_h <= cam_h:
            show[y1:y1+icon_h, icon_x:icon_x+icon_w] = red_drinking
        elif self.fm.abnormal_behaviour == 'answering the phone' and icon_x + icon_w <= cam_w and y2 + icon_h <= cam_h:
            show[y2:y2+icon_h, icon_x:icon_x+icon_w] = red_phoning
        elif self.fm.abnormal_behaviour == 'texting with phone' and icon_x + icon_w <= cam_w and y3 + icon_h <= cam_h:
            show[y3:y3+icon_h, icon_x:icon_x+icon_w] = red_texting

        # Convert to QImages (with correct bytesPerLine) and set pixmaps
        def to_qimage(rgb_img):
            h, w, ch = rgb_img.shape
            return QtGui.QImage(rgb_img.data, w, h, ch * w, QtGui.QImage.Format_RGB888)

        self.ui.camera_show.setPixmap(QtGui.QPixmap.fromImage(to_qimage(show)))
        self.ui.face_mesh.setPixmap(QtGui.QPixmap.fromImage(to_qimage(annotated_image)))
        self.ui.left_eye.setPixmap(QtGui.QPixmap.fromImage(to_qimage(left_eye)))
        self.ui.right_eye.setPixmap(QtGui.QPixmap.fromImage(to_qimage(right_eye)))
        self.ui.mouth.setPixmap(QtGui.QPixmap.fromImage(to_qimage(mouth)))

        # Progress bar coloring (unchanged)
        if self.fm.blink_duration < 200:
            self.ui.blink_duration.setStyleSheet("QProgressBar::chunk{background-color:green;text-align:center;}")
        else:
            self.ui.blink_duration.setStyleSheet("QProgressBar::chunk{background-color:red;}")

        self.ui.distraction_detection.setStyleSheet(
            "QProgressBar::chunk{background-color:%s;text-align:center;}" %
            ("green" if distraction_score < 60 else "red"))
        self.ui.drowsiness_detection.setStyleSheet(
            "QProgressBar::chunk{background-color:%s;text-align:center;}" %
            ("green" if drowsiness_score < 60 else "red"))
        self.ui.emotion_detection.setStyleSheet(
            "QProgressBar::chunk{background-color:%s;text-align:center;}" %
            ("green" if expression_score < 60 else "red"))
        self.ui.behavior_detection.setStyleSheet(
            "QProgressBar::chunk{background-color:%s;text-align:center;}" %
            ("green" if behavior_score < 60 else "red"))

        self.ui.blink_duration.setValue(float(self.fm.blink_duration))
        self.ui.drowsiness_detection.setValue(float(drowsiness_score))
        self.ui.distraction_detection.setValue(float(distraction_score))
        self.ui.emotion_detection.setValue(0 * float(expression_score))
        self.ui.behavior_detection.setValue(float(behavior_score))

        # Alarm sound logic (unchanged)
        self.sound_play = (
            drowsiness_score > 60
            or distraction_score > 60
            or self.fm.abnormal_behaviour in ['drinking', 'answering the phone', 'texting with phone']
            or expression_score > 60
            or behavior_score > 60
        )
        if self.sound_play != self.last_play:
            if self.sound_play:
                mixer.music.play(-1)
            else:
                mixer.music.stop()
        self.last_play = self.sound_play

        # FPS
        end_time = time.time()
        process_time = max(1e-6, end_time - start_time)
        self.fps.append(1.0 / process_time)
        if len(self.fps) > 100:
            self.fps.pop(0)
        self.aver_fps = float(np.sum(self.fps) / len(self.fps))

        # Update plots (they will resize with layout)
        self.update_plot()


    def closeEvent(self, event):
        ok = QtWidgets.QPushButton()
        cacel = QtWidgets.QPushButton()

        msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, u"Close", u"Do you want to close?")

        msg.addButton(ok, QtWidgets.QMessageBox.ActionRole)
        msg.addButton(cacel, QtWidgets.QMessageBox.RejectRole)
        ok.setText(u'OK')
        cacel.setText(u'Cancel')
        if msg.exec_() == QtWidgets.QMessageBox.RejectRole:
            event.ignore()
        else:
            if self.cap.isOpened():
                self.cap.release()
            if self.timer_camera.isActive():
                self.timer_camera.stop()
            event.accept()


if __name__ == "__main__":
    App = QApplication(sys.argv)
    driver = Driver_Monitoring_System()
    if FULLSCREEN:
        driver.MainWindow.showFullScreen()
    else:
        driver.MainWindow.show()
    sys.exit(App.exec_())