# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=1000):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.get_yaxis().set_visible(False)
        self.axes.get_xaxis().set_visible(False)
        self.axes.set(facecolor="white")
        fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
        fig.set_facecolor('white')
        super(MplCanvas, self).__init__(fig)
        # Make canvas responsive within the layout
        from PyQt5 import QtWidgets
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.updateGeometry()


class Ui_Form(object):
    BASE_WIDTH = 1280  # 16:9 aspect ratio
    BASE_HEIGHT = 720
    
    # Comprehensive font rules for every text element
    FONT_RULES = {
        # Main section headers (larger text)
        'head_pose_label': {'base_size': 12, 'min_size': 10, 'max_size': 24},
        'eye_state_label': {'base_size': 12, 'min_size': 10, 'max_size': 24},
        'gaze_direction_label': {'base_size': 12, 'min_size': 10, 'max_size': 24},
        'blink_duration_label': {'base_size': 12, 'min_size': 10, 'max_size': 24},
        'yawn_frequency_label': {'base_size': 12, 'min_size': 10, 'max_size': 24},
        'drowsiness_state_label': {'base_size': 12, 'min_size': 10, 'max_size': 24},
        'quantification_label': {'base_size': 12, 'min_size': 10, 'max_size': 24},
        
        # Detection status labels
        'drowsiness_detection_label': {'base_size': 10, 'min_size': 9, 'max_size': 20},
        'distraction_detection_label': {'base_size': 10, 'min_size': 9, 'max_size': 20},
        'emotion_detection_label': {'base_size': 10, 'min_size': 9, 'max_size': 20},
        'behavior_detection_label': {'base_size': 10, 'min_size': 9, 'max_size': 20},
        
        # Small descriptive labels (more generous sizing)
        'left_eye_label': {'base_size': 9, 'min_size': 8, 'max_size': 16},
        'right_eye_label': {'base_size': 9, 'min_size': 8, 'max_size': 16},
        'mouth_label': {'base_size': 9, 'min_size': 8, 'max_size': 16},
        'gaze_yaw_label': {'base_size': 9, 'min_size': 8, 'max_size': 16},
        'gaze_pitch_label': {'base_size': 9, 'min_size': 8, 'max_size': 16},
        
        # Input fields (gaze yaw/pitch)
        'gaze_yaw': {'base_size': 9, 'min_size': 8, 'max_size': 16},
        'gaze_pitch': {'base_size': 9, 'min_size': 8, 'max_size': 16},
        
        # Buttons (more prominent)
        'button_open_camera': {'base_size': 10, 'min_size': 9, 'max_size': 18},
        'button_close': {'base_size': 10, 'min_size': 9, 'max_size': 18},
        
        # Progress bars text
        'blink_duration': {'base_size': 8, 'min_size': 7, 'max_size': 14},
        'drowsiness_detection': {'base_size': 8, 'min_size': 7, 'max_size': 14},
        'distraction_detection': {'base_size': 8, 'min_size': 7, 'max_size': 14},
        'emotion_detection': {'base_size': 8, 'min_size': 7, 'max_size': 14},
        'behavior_detection': {'base_size': 8, 'min_size': 7, 'max_size': 14},
    }
    
    POSITIONS = {
        'face_mesh': (20, 35, 300, 240),
        'camera_show': (340, 10, 920, 550),
        'head_pose_label': (10, 5, 310, 31),
        'eye_state_label': (10, 290, 310, 31),
        'left_eye': (20, 320, 90, 70),
        'right_eye': (120, 320, 90, 70),
        'mouth': (220, 320, 100, 70),
        'left_eye_label': (40, 400, 70, 18),
        'right_eye_label': (130, 400, 70, 18),
        'mouth_label': (250, 400, 70, 18),
        'gaze_direction_label': (10, 420, 310, 31),
        'gaze_yaw_label': (20, 455, 30, 18),
        'gaze_yaw': (55, 455, 45, 22),
        'gaze_pitch_label': (110, 455, 40, 18),
        'gaze_pitch': (155, 455, 45, 22),
        'blink_duration_label': (210, 420, 110, 31),
        'blink_duration': (210, 455, 110, 22),
        'yawn_frequency_label': (10, 480, 150, 31),
        'drowsiness_state_label': (170, 480, 150, 31),
        'draw_figure': (10, 510, 310, 100),
        'button_open_camera': (520, 570, 120, 30),
        'button_close': (880, 570, 120, 30),
        'quantification_label': (400, 610, 480, 25),
        'drowsiness_detection_label': (20, 640, 110, 25),
        'drowsiness_detection': (130, 640, 380, 25),
        'distraction_detection_label': (20, 675, 110, 25),
        'distraction_detection': (130, 675, 380, 25),
        'emotion_detection_label': (650, 675, 110, 25),
        'emotion_detection': (760, 675, 400, 25),
        'behavior_detection_label': (650, 640, 110, 25),
        'behavior_detection': (760, 640, 400, 25),
    }

    def setupUi(self, Form):
        # Static scaling of icons
        self.ratio = 1.8

        Form.setObjectName("Form")
        # Set initial size to 16:9 aspect ratio
        Form.resize(self.BASE_WIDTH, self.BASE_HEIGHT)
        
        # Create central widget and main layout
        self.centralWidget = QtWidgets.QWidget(Form)
        if hasattr(Form, 'setCentralWidget'):
            Form.setCentralWidget(self.centralWidget)
        
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setObjectName("mainLayout")
        
        # Create container that maintains aspect ratio
        self.container = QtWidgets.QWidget()
        self.container.setMinimumSize(QtCore.QSize(self.BASE_WIDTH, self.BASE_HEIGHT))
        self.container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.container.setObjectName("container")
        
        # Add container to scroll area for small screens
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.container)
        self.mainLayout.addWidget(self.scrollArea)
        
        # Create all UI elements
        self._create_ui_elements()
        
        # Set initial geometries
        QtCore.QTimer.singleShot(0, lambda: self.update_geometries(
            self.container.width(), 
            self.container.height()
        ))
        
        # Connect resize event
        Form.resizeEvent = self.resizeEvent
        Form.showEvent = self.showEvent  # Ensure proper sizing on first show
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def _create_ui_elements(self):
        """Create all UI elements"""
        # Create widgets
        self.face_mesh = QtWidgets.QLabel(self.container)
        self.camera_show = QtWidgets.QLabel(self.container)
        self.head_pose_label = QtWidgets.QLabel(self.container)
        self.eye_state_label = QtWidgets.QLabel(self.container)
        self.left_eye = QtWidgets.QLabel(self.container)
        self.right_eye = QtWidgets.QLabel(self.container)
        self.mouth = QtWidgets.QLabel(self.container)
        self.left_eye_label = QtWidgets.QLabel(self.container)
        self.right_eye_label = QtWidgets.QLabel(self.container)
        self.mouth_label = QtWidgets.QLabel(self.container)
        self.gaze_direction_label = QtWidgets.QLabel(self.container)
        self.gaze_yaw_label = QtWidgets.QLabel(self.container)
        self.blink_duration_label = QtWidgets.QLabel(self.container)
        self.gaze_pitch = QtWidgets.QLineEdit(self.container)
        self.gaze_pitch_label = QtWidgets.QLabel(self.container)
        self.gaze_yaw = QtWidgets.QLineEdit(self.container)
        self.blink_duration = QtWidgets.QProgressBar(self.container)
        self.yawn_frequency_label = QtWidgets.QLabel(self.container)
        self.drowsiness_state_label = QtWidgets.QLabel(self.container)
        self.draw_figure = QtWidgets.QWidget(self.container)
        self.button_open_camera = QtWidgets.QPushButton(self.container)
        self.button_close = QtWidgets.QPushButton(self.container)
        self.quantification_label = QtWidgets.QLabel(self.container)
        self.drowsiness_detection_label = QtWidgets.QLabel(self.container)
        self.drowsiness_detection = QtWidgets.QProgressBar(self.container)
        self.distraction_detection_label = QtWidgets.QLabel(self.container)
        self.distraction_detection = QtWidgets.QProgressBar(self.container)
        self.emotion_detection_label = QtWidgets.QLabel(self.container)
        self.emotion_detection = QtWidgets.QProgressBar(self.container)
        self.behavior_detection_label = QtWidgets.QLabel(self.container)
        self.behavior_detection = QtWidgets.QProgressBar(self.container)
        
        # Set up fonts - use better base sizes
        font = QtGui.QFont("Arial", 12)
        font.setBold(True)
        
        font_small = QtGui.QFont("Arial", 9)  # Increased from 8pt
        
        font_medium = QtGui.QFont("Arial", 10)
        font_medium.setBold(True)
        
        # Configure widgets
        self._configure_widgets(font, font_small, font_medium)

    def _configure_widgets(self, font, font_small, font_medium):
        """Configure widget properties with better base font sizes"""
        self.face_mesh.setFrameShape(QtWidgets.QFrame.Box)
        self.face_mesh.setFrameShadow(QtWidgets.QFrame.Plain)
        self.face_mesh.setText("")
        self.face_mesh.setObjectName("face_mesh")
        
        self.camera_show.setFrameShape(QtWidgets.QFrame.Box)
        self.camera_show.setFrameShadow(QtWidgets.QFrame.Plain)
        self.camera_show.setText("")
        self.camera_show.setObjectName("camera_show")
        
        # Main headers
        for label in [self.head_pose_label, self.eye_state_label, self.gaze_direction_label,
                     self.blink_duration_label, self.yawn_frequency_label, self.drowsiness_state_label,
                     self.quantification_label]:
            label.setFont(font)
            label.setFrameShape(QtWidgets.QFrame.NoFrame)
            label.setFrameShadow(QtWidgets.QFrame.Plain)
        
        # Eye/mouth displays
        for eye in [self.left_eye, self.right_eye, self.mouth]:
            eye.setFrameShape(QtWidgets.QFrame.Box)
            eye.setFrameShadow(QtWidgets.QFrame.Plain)
            eye.setText("")
        
        # Small labels with increased base size
        for label in [self.left_eye_label, self.right_eye_label, self.mouth_label,
                     self.gaze_yaw_label, self.gaze_pitch_label]:
            label.setFont(font_small)
        
        # Gaze input fields with larger base font
        for field in [self.gaze_yaw, self.gaze_pitch]:
            field.setFont(font_small)
            field.setFrame(True)  # Make input fields more visible
            field.setAlignment(QtCore.Qt.AlignCenter)
        
        # Blink duration progress bar
        self.blink_duration.setRange(0, 300)
        self.blink_duration.setFont(font_small)
        
        # Draw figure container
        self.draw_figure.setObjectName("draw_figure")
        self.hLayout = QtWidgets.QHBoxLayout(self.draw_figure)
        self.hLayout.setObjectName("hLayout")
        self.hLayout.setContentsMargins(0, 0, 0, 0)
        self.canvas1 = MplCanvas(self.draw_figure, width=2, height=1, dpi=50)
        self.canvas2 = MplCanvas(self.draw_figure, width=2, height=1, dpi=50)
        self.hLayout.addWidget(self.canvas1)
        self.hLayout.addWidget(self.canvas2)
        
        # Buttons with larger base font and padding
        for button in [self.button_open_camera, self.button_close]:
            button.setFont(font_medium)
            button.setStyleSheet("""
                QPushButton {
                    padding: 3px 8px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f0f0f0;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
        
        # Detection labels
        for label in [self.drowsiness_detection_label, self.distraction_detection_label,
                     self.emotion_detection_label, self.behavior_detection_label]:
            label.setFont(font_medium)
            label.setFrameShape(QtWidgets.QFrame.NoFrame)
            label.setFrameShadow(QtWidgets.QFrame.Plain)
        
        # Detection progress bars
        for bar in [self.drowsiness_detection, self.distraction_detection,
                   self.emotion_detection, self.behavior_detection]:
            bar.setRange(0, 100)
            bar.setFont(font_small)
            bar.setTextVisible(True)

        for img_label in [self.camera_show, self.face_mesh, self.left_eye, self.right_eye, self.mouth]:
            img_label.setScaledContents(True)
            img_label.setAlignment(QtCore.Qt.AlignCenter)

    def update_geometries(self, width, height):
        """Update all widget geometries based on current container size"""
        # Calculate scaling factors
        scale_x = width / self.BASE_WIDTH
        scale_y = height / self.BASE_HEIGHT
        scale = min(scale_x, scale_y)  # Use uniform scaling
        
        for widget_name, (x_base, y_base, w_base, h_base) in self.POSITIONS.items():
            widget = getattr(self, widget_name, None)
            if widget:
                # Calculate scaled position and size
                x = int(x_base * scale_x)
                y = int(y_base * scale_y)
                w = int(w_base * scale_x)
                h = int(h_base * scale_y)
                widget.setGeometry(QtCore.QRect(x, y, w, h))
                
                # Apply font scaling if this widget has font rules
                if widget_name in self.FONT_RULES:
                    rule = self.FONT_RULES[widget_name]
                    font = widget.font()
                    new_size = max(rule['min_size'], min(rule['max_size'], int(rule['base_size'] * scale)))
                    font.setPointSize(new_size)
                    widget.setFont(font)
                
                # Special handling for progress bars
                if isinstance(widget, QtWidgets.QProgressBar):
                    # Ensure text visibility at small sizes
                    widget.setTextVisible(new_size >= 7 if (widget_name in self.FONT_RULES) else True)
                    
                    # Update progress bar chunk size based on scale
                    if widget_name in ['blink_duration', 'drowsiness_detection', 'distraction_detection',
                                     'emotion_detection', 'behavior_detection']:
                        chunk_width = max(5, min(20, int(10 * scale)))
                        color = {
                            'drowsiness_detection': '#05B8CC',
                            'distraction_detection': '#FFA500',
                            'emotion_detection': '#2ECC71',
                            'behavior_detection': '#9B59B6',
                            'blink_duration': '#FF6B6B'
                        }.get(widget_name, '#4CAF50')
                        
                        widget.setStyleSheet(f"""
                            QProgressBar {{
                                border: 1px solid #999;
                                border-radius: 3px;
                                text-align: center;
                                font-size: {new_size if widget_name in self.FONT_RULES else 8}px;
                            }}
                            QProgressBar::chunk {{
                                background-color: {color};
                                width: {chunk_width}px;
                            }}
                        """)

    def resizeEvent(self, event):
        """Handle resize events"""
        if hasattr(self, 'container'):
            # Update container size while maintaining aspect ratio
            container_width = event.size().width()
            container_height = int(container_width * self.BASE_HEIGHT / self.BASE_WIDTH)
            
            if container_height > event.size().height():
                container_height = event.size().height()
                container_width = int(container_height * self.BASE_WIDTH / self.BASE_HEIGHT)
            
            self.container.setFixedSize(container_width, container_height)
            self.update_geometries(container_width, container_height)
        event.accept()

    def showEvent(self, event):
        """Ensure proper sizing when window is first shown"""
        QtCore.QTimer.singleShot(50, lambda: self.update_geometries(
            self.container.width(),
            self.container.height()
        ))
        event.accept()

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Driver Monitoring System"))
        self.head_pose_label.setText(_translate("Form", "Head pose"))
        self.eye_state_label.setText(_translate("Form", "Eyes and mouth state"))
        self.left_eye_label.setText(_translate("Form", "Left eye"))
        self.right_eye_label.setText(_translate("Form", "Right eye"))
        self.mouth_label.setText(_translate("Form", "Mouth"))
        self.gaze_direction_label.setText(_translate("Form", "Gaze direction"))
        self.gaze_yaw_label.setText(_translate("Form", "Yaw"))
        self.blink_duration_label.setText(_translate("Form", "Close eyes"))
        self.gaze_pitch_label.setText(_translate("Form", "Pitch"))
        self.yawn_frequency_label.setText(_translate("Form", "Yawn state"))
        self.quantification_label.setText(_translate("Form", "Quantified detection results"))
        self.drowsiness_state_label.setText(_translate("Form", "Blink rate"))
        self.drowsiness_detection_label.setText(_translate("Form", "Drowsiness"))
        self.distraction_detection_label.setText(_translate("Form", "Distraction"))
        self.emotion_detection_label.setText(_translate("Form", "Emotion"))
        self.behavior_detection_label.setText(_translate("Form", "Behavior"))
        self.button_open_camera.setText(_translate("Form", "Open Camera"))
        self.button_close.setText(_translate("Form", "Exit"))