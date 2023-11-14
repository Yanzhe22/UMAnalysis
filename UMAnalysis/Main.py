import os
import sys
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QMainWindow
from UMAnalysis import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.emg_file_path = " "
        self.move_file_path = " "

        self.cd_path_str = str(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")

        # checkBox为原始数据，checkBox_2为整流平滑，默认原始数据为选中状态
        self.checkBox_list = [self.checkBox, self.checkBox_2]
        self.checkBox.setChecked(True)

        # !! UI设计不加信号槽，在main中实现click的功能
        # 各按钮绑定相关功能
        self.pushButton.clicked.connect(self.open_emg_file)
        self.pushButton_2.clicked.connect(self.open_movement_file)
        self.pushButton_5.clicked.connect(self.emg_plot)
        self.pushButton_6.clicked.connect(self.movement_plot)

    def open_emg_file(self):
        """
        打开sEMG数据文件
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "选择并加载sEMG数据")
        if file_path:
            self.textBrowser.setText(file_path.split("/")[-1])
            self.emg_file_path = file_path

        # 载入新的文件后清空旧文件的图像
        with open('temp_emg.html', 'w', encoding='utf-8') as f:
            f.write(" ")

        self.webEngineView.load(QUrl(self.cd_path_str + '/temp_emg.html'))

    def open_movement_file(self):
        """
        打开运动数据文件
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "选择并加载运动数据")
        if file_path:
            self.textBrowser_2.setText(file_path.split("/")[-1])
            self.move_file_path = file_path

        # 载入新的文件后清空旧文件的图像
        with open('temp_tj.html', 'w', encoding='utf-8') as f:
            f.write(" ")
        with open('temp_force.html', 'w', encoding='utf-8') as f:
            f.write(" ")

        self.webEngineView_2.load(QUrl(self.cd_path_str + '/temp_force.html'))
        self.webEngineView_3.load(QUrl(self.cd_path_str + '/temp_tj.html'))

    def emg_plot(self):
        """
        确认选择，调用EMG的绘图方法
        """
        # 列表存选中的处理方式
        processing_selected = []
        for processing in self.checkBox_list[0:2]:
            if processing.isChecked():
                processing_selected.append(processing.text())
        # print(processing_selected)

        # 未选中则提示，已选中则绘制
        if len(processing_selected) == 0:
            QMessageBox.information(self, "提示", "请选择数据处理方式！")
        else:
            self.create_emg_chart()

    def create_emg_chart(self):
        """
        webEngineView处，EMG的绘图方法
        """
        # 读取sEMG数据，放大1000倍，单位转为mV
        emg_data = pd.read_csv(self.emg_file_path, header=None)
        emg_data_mv = emg_data.multiply(1000)
        # 时间戳转换，秒
        emg_data_mv.iloc[:, 0] = emg_data_mv.iloc[:, 0].apply(lambda x: (x - emg_data_mv.iloc[0, 0]) / 1000000)
        emg = []

        # 读取html
        with open('sEMG_plot.html', 'r', encoding='utf-8') as file:
            js = file.read()

        # 将数据替换进JavaScript
        for i in range(9):
            emg.append(emg_data_mv.iloc[:, i].values.tolist())
            str1 = "{" + str(i) + "}"
            js = js.replace(str1, f"{emg[i]}")

        # 带数据生成新的html文件
        with open('temp_emg.html', 'w', encoding='utf-8') as f:
            f.write(js)

        self.webEngineView.load(QUrl(self.cd_path_str + '/temp_emg.html'))

    def movement_plot(self):
        """
        分别调用轨迹绘制方法和力传感器绘制方法
        """
        # webEngineView_2处，绘制力传感器图像
        self.create_force_chart()

        # webEngineView_3处，绘制轨迹图像
        self.create_trajectory_chart()

    def create_force_chart(self):
        """
        webEngineView_2处，力传感器数据绘图方法
        """
        # 读取运动数据中的力传感器数据，0、4、5、7列分别为时间戳、Fx、Fy和运动标志位
        force_data = pd.read_csv(self.move_file_path, header=None, usecols=(0, 4, 5, 7))
        force_data.iloc[:, 0] = force_data.iloc[:, 0].apply(lambda x: (x - force_data.iloc[0, 0]) / 1000)

        # 读取html
        with open('force_plot.html', 'r', encoding='utf-8') as file:
            js_force = file.read()

        # 处理数据并替换进JavaScript
        timestamp = force_data[0].values.tolist()
        f_x = force_data[4].values.tolist()
        f_y = force_data[5].values.tolist()
        f_flag = force_data[7].values.tolist()

        js_force = js_force.replace('data_timestamp', f'{timestamp}')
        js_force = js_force.replace('F1', f'{f_x}')
        js_force = js_force.replace('F2', f'{f_y}')
        js_force = js_force.replace('F3', f'{f_flag}')

        # 带数据生成新的html
        with open('temp_force.html', 'w', encoding='utf-8') as f:
            f.write(js_force)

        self.webEngineView_2.load(QUrl(self.cd_path_str + '/temp_force.html'))

    def create_trajectory_chart(self):
        """
        webEngineView_3处，运动轨迹的绘图方法
        """
        # 读取运动数据中的坐标轨迹，1、2、7列分别为x坐标、y坐标和运动标志位
        trajectory_data = pd.read_csv(self.move_file_path, header=None, usecols=(1, 2, 7))

        # 失真处理，x坐标缩为一半，y坐标不变
        trajectory_data.iloc[:, 0] = trajectory_data.iloc[:, 0].apply(lambda x: x / 2)

        tj_flag = trajectory_data.iloc[:, 2].unique().tolist()

        # 读取html
        with open('trajectory_plot.html', 'r', encoding='utf-8') as file:
            js_tj = file.read()

        # 将数据替换进JavaScript
        for i in tj_flag:
            tj_data = trajectory_data[trajectory_data.iloc[:, 2] == i][[1, 2]].values.tolist()
            str2 = "data_" + str(i)
            js_tj = js_tj.replace(str2, f'{tj_data}')

        # 带数据生成新的html
        with open('temp_tj.html', 'w', encoding='utf-8') as f:
            f.write(js_tj)

        self.webEngineView_3.load(QUrl(self.cd_path_str + '/temp_tj.html'))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
