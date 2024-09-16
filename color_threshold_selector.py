import sys 
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QComboBox, QFileDialog
from PyQt5.QtGui import QImage, QPixmap, QClipboard
from PyQt5.QtCore import Qt
import cv2
import numpy as np

class ColorThresholdSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('阈值选择器')
        self.setGeometry(100, 100, 1200, 800)

        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 图像显示区域
        image_layout = QHBoxLayout()
        self.source_label = QLabel()  # 原始图像标签
        self.segmented_label = QLabel()  # 分割后图像标签
        image_layout.addWidget(self.source_label)
        image_layout.addWidget(self.segmented_label)
        main_layout.addLayout(image_layout)

        # 控制区域
        controls_layout = QHBoxLayout()

        # 加载图像按钮
        self.load_button = QPushButton('选择图像')
        self.load_button.clicked.connect(self.load_image)
        controls_layout.addWidget(self.load_button)

        # 颜色空间选择下拉框
        self.color_space_combo = QComboBox()
        self.color_space_combo.addItems(['RGB', 'LAB', 'HSV'])
        self.color_space_combo.currentIndexChanged.connect(self.update_color_space)
        self.color_space_combo.setFixedHeight(self.load_button.sizeHint().height())
        controls_layout.addWidget(self.color_space_combo)

        # 重置滑块按钮
        self.reset_button = QPushButton('重置滑块')
        self.reset_button.clicked.connect(self.reset_sliders)
        controls_layout.addWidget(self.reset_button)

        # 复制阈值按钮
        self.copy_button = QPushButton('复制阈值')
        self.copy_button.clicked.connect(self.copy_thresholds)
        controls_layout.addWidget(self.copy_button)

        main_layout.addLayout(controls_layout)

        # 滑块区域
        self.sliders = []
        self.slider_labels = []
        self.value_labels = []
        slider_layout = QVBoxLayout()
        for i in range(6):
            slider_row = QHBoxLayout()
            
            label = QLabel()
            slider_row.addWidget(label)
            self.slider_labels.append(label)

            slider = QSlider(Qt.Horizontal)
            slider.valueChanged.connect(self.update_threshold)
            slider_row.addWidget(slider)
            self.sliders.append(slider)

            value_label = QLabel()
            slider_row.addWidget(value_label)
            self.value_labels.append(value_label)

            slider_layout.addLayout(slider_row)

        main_layout.addLayout(slider_layout)

        self.setLayout(main_layout)

        self.image = None
        self.update_color_space()

    def load_image(self):
        # 打开文件对话框选择图像
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "打开图像", 
            "", 
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp)"
        )
        if file_name:
            try:
                # 使用numpy.fromfile读取图像数据
                image_data = np.fromfile(file_name, dtype=np.uint8)
                self.image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                if self.image is not None:
                    self.display_image(self.source_label, self.image)
                    self.update_threshold()
                else:
                    print(f"加载图像失败: {file_name}")
            except Exception as e:
                print(f"加载图像时发生异常: {e}")

    def update_color_space(self):
        # 更新颜色空间和滑块范围
        color_space = self.color_space_combo.currentText()
        if color_space == 'RGB':
            for slider in self.sliders:
                slider.setRange(0, 255)
        elif color_space == 'LAB':
            self.sliders[0].setRange(0, 100)  # L
            self.sliders[1].setRange(0, 100)  # L
            for slider in self.sliders[2:]:
                slider.setRange(-128, 127)  # a and b
        elif color_space == 'HSV':
            self.sliders[0].setRange(0, 179)  # H
            self.sliders[1].setRange(0, 179)  # H
            for slider in self.sliders[2:]:
                slider.setRange(0, 255)  # S and V
        self.reset_sliders()
        self.update_threshold()

    def reset_sliders(self):
        # 重置滑块到默认值
        color_space = self.color_space_combo.currentText()
        for i, slider in enumerate(self.sliders):
            if color_space == 'LAB':
                if i < 2:  # L channel
                    slider.setValue(0 if i % 2 == 0 else 100)
                else:  # a and b channels
                    slider.setValue(-128 if i % 2 == 0 else 127)
            elif color_space == 'HSV':
                if i < 2:  # H channel
                    slider.setValue(0 if i % 2 == 0 else 179)
                else:  # S and V channels
                    slider.setValue(0 if i % 2 == 0 else 255)
            else:  # RGB
                slider.setValue(0 if i % 2 == 0 else 255)
        self.update_threshold()

    def copy_thresholds(self):
        # 复制当前阈值到剪贴板
        color_space = self.color_space_combo.currentText()
        thresholds = [slider.value() for slider in self.sliders]
        threshold_str = f"{color_space} 阈值: 下界={thresholds[::2]}, 上界={thresholds[1::2]}"
        QApplication.clipboard().setText(threshold_str)
        print(f"已复制到剪贴板: {threshold_str}")

    def update_threshold(self):
        # 更新阈值并显示结果
        if self.image is None:
            return
        color_space = self.color_space_combo.currentText()
        if color_space == 'RGB':
            img = self.image
        elif color_space == 'LAB':
            img = cv2.cvtColor(self.image, cv2.COLOR_BGR2LAB)
        else:  # HSV
            img = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)

        # 获取下界和上界
        lower = np.array([self.sliders[i].value() for i in range(0, 6, 2)])
        upper = np.array([self.sliders[i].value() for i in range(1, 6, 2)])

        # 对LAB颜色空间范围映射
        if color_space == 'LAB':
            lower[0] = int(lower[0] * 255 / 100)
            upper[0] = int(upper[0] * 255 / 100)
            lower[1:] = lower[1:] + 128
            upper[1:] = upper[1:] + 128

        # 创建掩码
        mask = cv2.inRange(img, lower, upper)
        result = cv2.bitwise_and(self.image, self.image, mask=mask)

        self.display_image(self.segmented_label, result)
        self.update_slider_labels()

    def update_slider_labels(self):
        # 更新滑块标签
        color_space = self.color_space_combo.currentText()
        channel_names = {
            'RGB': ['R', 'G', 'B'],
            'LAB': ['L', 'A', 'B'],
            'HSV': ['H', 'S', 'V']
        }
        for i, (label, value_label) in enumerate(zip(self.slider_labels, self.value_labels)):
            channel = channel_names[color_space][i // 2]
            min_max = "最小值" if i % 2 == 0 else "最大值"
            value = self.sliders[i].value()
            label.setText(f"{channel} {min_max}")
            value_label.setText(f"{value}")

    def display_image(self, label, img):
        # 在标签上显示图像
        h, w = img.shape[:2]
        bytes_per_line = 3 * w
        q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        label.setPixmap(pixmap.scaled(600, 600, Qt.KeepAspectRatio))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ColorThresholdSelector()
    ex.show()
    sys.exit(app.exec_())
