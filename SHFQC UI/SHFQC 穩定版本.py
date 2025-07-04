import sys
import os
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout,
    QGroupBox, QLineEdit, QPushButton,
    QLabel, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox,
    QDialog, QVBoxLayout, QMessageBox, QErrorMessage, QSlider,
    QTextEdit, QProgressBar
)
from PyQt6.QtCore import QThreadPool
from PyQt6.QtGui import QIcon

import matplotlib.pyplot as plt

from zhinst.toolkit import Session
from pyvisa import ResourceManager

#* 導入自訂模組
from library.init_UI.MainUI_builder import UIBuilder
from library.init_UI.init_components import init_components
from library.device_control import SHFQC, YOKOGAWA
from library.waveform_generation import generate_waveform
from library.File_Storage import DataSaver, FileLoader
from library.measurement_controller import MeasurementController
from library.gui_components import SaveDataDialog, ParameterDialog, YOKOGAWAControlDialog
from library.Formula_Parser import FormulaParser
from library.plot_manager import PlotManager
from library.config_handler import ConfigHandler


class OptimizedSHFQCGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SHFQC控制程序 - v3.1")
        self.setWindowIcon(QIcon('icon.png'))
        self.setGeometry(100, 100, 1500, 900)
        
        #* 繪圖區字體設置
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        #* 初始化定義控制組建
        init_components.init_components(self)
        
        #* 創建主視窗介面
        UIBuilder.create_main_ui(self)
        
        #* 初始化配置管理器
        self.config_path = os.path.join(os.path.dirname(__file__), 'shfqc_config.ini')
        self.config_handler = ConfigHandler(self.config_path)
        #* 初始化繪圖管理器
        self.plot_manager = PlotManager(self)
        #* 初始化公式解析工具
        self.formula_parser = FormulaParser()
        #* 初始化量測線程控制器
        self.measurement_controller = MeasurementController(self)

        #* 初始化量測數據暫存
        #時域
        self.time_domain_data = None
        #頻域
        self.freq_domain_data = None
        #功率掃描
        self.power_data = None
        self.power_amplitudes = None
        #頻率掃描
        self.freq_dep_data = None
        self.freq_lo_values = None
        #電流-頻率掃描
        self.current_freq_data = None
        self.freq_values = None
        self.current_values = None

        #* 事件連接
        self._connect_signals()

        #* 加載配置數據
        self.load_settings()

        #* 初始化波型預覽顯示
        self.update_waveform_preview()

        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(4)

    # region: 事件链连接
    def _connect_signals(self):
        self.save_config_btn.clicked.connect(self.save_settings)
        self.run_measure_btn.clicked.connect(self.run_time_domain)
        self.run_sweep_btn.clicked.connect(self.run_frequency_sweep)
        self.run_power_btn.clicked.connect(self.run_power_dependent)
        self.run_freq_dep_btn.clicked.connect(self.run_frequency_dependent)
        self.run_current_freq_btn.clicked.connect(self.run_current_frequency_dependent)
        self.abort_btn.clicked.connect(self.abort_measurement)
        self.btn_connect.clicked.connect(self.connect_device)
        self.save_data_btn.clicked.connect(self.save_data)
        self.load_data_btn.clicked.connect(self.load_data)
        self.yoko_devices_contect.clicked.connect(self.check_yoko)
        self.btn_control_yoko.clicked.connect(self.open_yoko_control)
        
        
        # 波形相关信号
        self.wave_type_combo.currentIndexChanged.connect(self.wave_param_stack.setCurrentIndex)
        self.wave_type_combo.currentIndexChanged.connect(self.update_waveform_preview)
        self.digital_lo_spin.valueChanged.connect(self.update_waveform_preview)
        self.gain_spin.valueChanged.connect(self.update_waveform_preview)
        self.pulse_length_spin.valueChanged.connect(self.update_waveform_preview)
        self.rise_samples_spin.valueChanged.connect(self.update_waveform_preview)
        self.fall_samples_spin.valueChanged.connect(self.update_waveform_preview)
        self.front_std_spin.valueChanged.connect(self.update_waveform_preview)
        self.end_std_spin.valueChanged.connect(self.update_waveform_preview)
        self.front_tau_spin.valueChanged.connect(self.update_waveform_preview)
        self.end_tau_spin.valueChanged.connect(self.update_waveform_preview)
        self.front_concave_check.stateChanged.connect(self.update_waveform_preview)
        self.end_concave_check.stateChanged.connect(self.update_waveform_preview)
        self.custom_points_spin.valueChanged.connect(self.update_waveform_preview)
        self.custom_duration_spin.valueChanged.connect(self.update_waveform_preview)
        self.custom_params_btn.clicked.connect(self.set_custom_parameters)
        self.parse_formula_btn.clicked.connect(self.handle_parse_formula)
        
        # 绘图更新信号
        self.power_slider.valueChanged.connect(self.update_power_slice)
        self.freq_dep_slider.valueChanged.connect(self.update_freq_dep_slice)
        self.current_slider.valueChanged.connect(self.current_freq_slide_valueget)
        self.freq_slider_current_freq.valueChanged.connect(self.current_freq_slide_valueget)
        
        # 方案选择变化
        self.scheme_combo.currentIndexChanged.connect(self.update_scheme_ui)
    # endregion

    # region: 波形生成功能
    def set_custom_parameters(self):
        """设置自定义波型的参数"""
        try:
            # 解析公式以获取变量
            formula = self.custom_formula_edit.text()
            if not formula:
                QMessageBox.warning(self, "警告", "請先輸入公式")
                return
                
            # 解析公式
            if not self.formula_parser.parse(formula):
                QMessageBox.warning(self, "解析錯誤", "公式解析失敗")
                return
                
            # 获取变量（排除时间变量）
            variables = [v for v in self.formula_parser.variables if v not in ('t', 'time')]
            
            if not variables:
                self.custom_params = {}
                self.custom_params_label.setText("參數: 無")
                return
                
            # 显示参数设置对话框
            dialog = ParameterDialog(variables, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.custom_params = dialog.get_parameters()
                param_text = ", ".join([f"{k}={v}" for k, v in self.custom_params.items()])
                self.custom_params_label.setText(f"參數: {param_text}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"參數設置失敗: {str(e)}")
            
    def handle_parse_formula(self):
        """处理解析公式按钮点击事件"""
        try:
            formula = self.custom_formula_edit.text()
            if not formula:
                QMessageBox.warning(self, "警告", "請先輸入公式")
                return
                
            # 解析公式
            if not self.formula_parser.parse(formula):
                QMessageBox.warning(self, "解析錯誤", "公式解析失敗")
                return
                
            # 获取变量（排除时间变量）
            variables = [v for v in self.formula_parser.variables if v not in ('t', 'time')]
            
            if not variables:
                self.custom_params = {}
                self.custom_params_label.setText("參數: 無")
                QMessageBox.information(self, "解析完成", "公式解析成功，未發現需要設置的參數")
                return
                
            # 显示参数设置对话框
            dialog = ParameterDialog(variables, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.custom_params = dialog.get_parameters()
                param_text = ", ".join([f"{k}={v}" for k, v in self.custom_params.items()])
                self.custom_params_label.setText(f"參數: {param_text}")
                QMessageBox.information(self, "解析完成", f"公式解析成功，已設置參數: {param_text}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"公式解析失敗: {str(e)}")
        finally:
            # 更新波形预览
            self.update_waveform_preview()
            
    def generate_waveform(self):
        """根据当前参数生成波形"""
        # 收集所有需要的参数
        wave_params = {
            'wave_type': self.wave_type_combo.currentText(),
            'pulse_length': self.pulse_length_spin.value(),
            'rise_samples': self.rise_samples_spin.value(),
            'fall_samples': self.fall_samples_spin.value(),
            'gain': self.gain_spin.value(),
            'digital_lo': self.digital_lo_spin.value(),
            'front_std': self.front_std_spin.value(),
            'end_std': self.end_std_spin.value(),
            'front_tau': self.front_tau_spin.value(),
            'end_tau': self.end_tau_spin.value(),
            'front_concave': self.front_concave_check.isChecked(),
            'end_concave': self.end_concave_check.isChecked(),
            'custom_formula': self.custom_formula_edit.text(),
            'custom_params': getattr(self, 'custom_params', {}),
            'custom_duration': self.custom_duration_spin.value(),
            'custom_points': self.custom_points_spin.value(),
        }
        
        # 使用新的波形生成函数
        return generate_waveform(
            wave_params, 
            error_callback=self.show_error_message
        )

    def update_waveform_preview(self):
        """更新波形预览图"""
        waveform = self.generate_waveform()
        if waveform is None:
            return
            
        self.wave_preview.figure.clear()
        ax = self.wave_preview.figure.add_subplot(111)
        
        # 绘制波形
        n_pts = len(waveform)
        sampling_rate = 2e9  # 2 GHz采样率
        t0 = 0
        t = np.arange(n_pts) * 1/sampling_rate + t0
        ax.plot(t, np.abs(waveform), 'r-', label='包絡')
        ax.plot(t, np.real(waveform), 'b-', label='實部')
        ax.plot(t, np.imag(waveform), 'g-', label='虛部')
        
        # 设置标签和标题
        wave_type = self.wave_type_combo.currentText()
        ax.set_title(f"{wave_type} 預覽")
        ax.set_xlabel("時間 (ns)")
        ax.set_ylabel("振幅")
        ax.grid(True)
        ax.legend()
        
        self.wave_preview.draw()
        try:
            waveform = self.generate_waveform()
            if waveform is None:
                return
                
            self.wave_preview.figure.clear()
            ax = self.wave_preview.figure.add_subplot(111)
            
            # 绘制波形
            n_pts = len(waveform)
            sampling_rate = 2e9  # 2 GHz采样率
            t0 = 0
            t = np.arange(n_pts) * 1/sampling_rate + t0
            ax.plot(t, np.abs(waveform), 'r-', label='包絡')
            ax.plot(t, np.real(waveform), 'b-', label='實部')
            ax.plot(t, np.imag(waveform), 'g-', label='虛部')
            
            # 设置标签和标题
            wave_type = self.wave_type_combo.currentText()
            ax.set_title(f"{wave_type} 預覽")
            ax.set_xlabel("時間 (ns)")
            ax.set_ylabel("振幅")
            ax.grid(True)
            ax.legend()
            
            self.wave_preview.draw()
        except Exception as e:
            # 避免预览错误导致界面卡死
            print(f"預覽錯誤: {str(e)}")
    # endregion

    # region: 配置文件处理
    def load_settings(self):
        """加载配置文件"""
        self.config_handler.load(self)
    
    def save_settings(self):
        """保存配置文件"""
        self.config_handler.save(self)
    
    def closeEvent(self, event):
        """关闭窗口后保存配置"""
        self.save_settings()
        event.accept()
    # endregion

    # region: 测量功能
    def get_current_params(self):
        """从GUI获取当前参数"""
        if self.measure_plan == 0:  # 時域 {單張} 量測
            window_duration = self.window_dur_spin_time.value()
            trigger_delay = self.trigger_delay_spin_time.value()
            n_avg = self.num_avg_spin_time.value()
        elif self.measure_plan == 1:  # 時域 {振幅} 掃描
            window_duration = self.window_dur_spin_power.value()
            trigger_delay = self.trigger_delay_spin_power.value()
            n_avg = self.num_avg_spin_power.value()
        elif self.measure_plan == 2:  # 時域 {頻率} 掃描
            window_duration = self.window_dur_spin_freq.value()
            trigger_delay = self.trigger_delay_spin_freq.value()
            n_avg = self.num_avg_spin_freq.value()
        elif self.measure_plan == 3:  # 時域 {電流頻率} 掃描
            window_duration = self.window_dur_spin_current_freq.value()
            trigger_delay = self.trigger_delay_spin_current_freq.value()
            n_avg = self.num_avg_spin_current_freq.value()
        elif self.measure_plan == 4:  # 頻域 {單張} 量測
            window_duration = self.window_dur_spin_time.value()
            trigger_delay = self.trigger_delay_spin_time.value()
            n_avg = self.num_avg_spin_time.value()

        return {
            # 设备参数
            'input_range': self.input_range_combo.currentData(),
            'output_range': self.output_range_combo.currentData(),
            'center_freq': self.center_freq_spin.value(),
            'digital_lo': self.digital_lo_spin.value(),
            'gain': self.gain_spin.value(),

            # 波形参数
            'wave_type': self.wave_type_combo.currentText(),
            'pulse_length': self.pulse_length_spin.value(),
            'rise_samples': self.rise_samples_spin.value(),
            'fall_samples': self.fall_samples_spin.value(),
            'front_std': self.front_std_spin.value(),
            'end_std': self.end_std_spin.value(),
            'front_tau': self.front_tau_spin.value(),
            'end_tau': self.end_tau_spin.value(),
            'front_concave': self.front_concave_check.isChecked(),
            'end_concave': self.end_concave_check.isChecked(),
            'custom_formula': self.custom_formula_edit.text(),
            'custom_points': self.custom_points_spin.value(),
            'custom_duration': self.custom_duration_spin.value(),
            'custom_params': getattr(self, 'custom_params', {}),

            # 时域测量参数
            'window_duration': window_duration * 1e-9,
            'trigger_delay': trigger_delay * 1e-9,
            'n_avg': n_avg,

            # 频域测量参数
            'lo_start': self.lo_start_spin.value(),
            'lo_stop': self.lo_stop_spin.value(),
            'lo_points': self.lo_points_spin.value(),
            'avg_num': self.avg_num_spin.value(),
            'int_time': self.int_time_spin.value(),
            
            # 功率依赖测量参数
            'power_dep_start': self.power_start_spin.value(),
            'power_dep_stop': self.power_stop_spin.value(),
            'power_dep_points': self.power_points_spin.value(),
            
            # 频率依赖测量参数
            'freq_dep_start': self.freq_dep_start_spin.value(),
            'freq_dep_stop': self.freq_dep_stop_spin.value(),
            'freq_dep_points': self.freq_dep_points_spin.value(),

            # 电流-频率扫描参数
            'curr_freq_dep_curr_start': self.current_start_spin.value(),
            'curr_freq_dep_curr_stop': self.current_stop_spin.value(),
            'curr_freq_dep_curr_points': self.current_points_spin.value(),
            'curr_freq_dep_freq_start': self.freq_start_current_freq.value(),
            'curr_freq_dep_freq_stop': self.freq_stop_current_freq.value(),
            'curr_freq_dep_freq_point': self.freq_points_current_freq.value(),
        }

    def run_time_domain(self):
        """启动时域测量线程"""
        self.connect_device()
        params = self.get_current_params()
        self.measurement_controller.run_measurement('時域 {單張} 量測', params)
        self._toggle_controls(False)

    def run_frequency_sweep(self):
        """启动频域扫描"""
        params = self.get_current_params()
        self.measurement_controller.run_measurement('頻域 {單張} 量測', params)
        self._toggle_controls(False)

    def run_power_dependent(self):
        """功率依赖测量线程"""
        self.connect_device()
        params = self.get_current_params()
        self.measurement_controller.run_measurement('時域 {振幅} 掃描', params)
        self._toggle_controls(False)
        
    def run_frequency_dependent(self):
        """频率依赖测量线程"""
        self.connect_device()
        params = self.get_current_params()
        self.measurement_controller.run_measurement('時域 {頻率} 掃描', params)
        self._toggle_controls(False)

    def run_current_frequency_dependent(self):
        """电流-频率依赖测量线程"""
        self.connect_device()
        params = self.get_current_params()
        self.measurement_controller.run_measurement(
            '時域 {電流頻率} 掃描', 
            params,
            self.yokos
        )
        self._toggle_controls(False)

    def progress_update(self, progress, left_time):
        """更新进度条和剩余时间"""
        if progress < 100:
            self.progress_bar.setValue(int(progress))
            remaining_time_h = left_time // 3600
            left_time = left_time - remaining_time_h * 3600
            remaining_time_m = left_time // 60
            remaining_time_s = (left_time - remaining_time_m * 60) // 1
            self.time_label.setText(f"剩餘時間: {int(remaining_time_h):02}:{int(remaining_time_m):02}:{int(remaining_time_s):02}(h/m/s)")
        else:
            self.progress_bar.setValue(100)

    def update_time_data(self, data):
        """更新时域数据"""
        self.time_domain_data = data
        self.plot_manager.update_time_plot(data)
    
    def update_freq_data(self, data):
        """更新频域数据"""
        self.freq_domain_data = data
        self.plot_manager.update_freq_plot(data)
    
    def update_power_data(self, data):
        """更新功率依赖数据"""
        self.power_data = data['data']
        self.power_amplitudes = data['amp']
        self.plot_manager.update_power_plot(data)
    
    def update_freq_dep_data(self, data):
        """更新频率依赖数据"""
        self.freq_dep_data = data['data']
        self.freq_lo_values = data['lo_values']
        self.plot_manager.update_freq_dep_plot(data)
    
    def update_current_freq_data(self, data):
        """更新电流-频率数据"""
        self.current_freq_data = data['data']
        self.current_values = data['curr']
        self.freq_values = data['lo_values']
        self.plot_manager.update_current_freq_plot(data)

    def abort_measurement(self):
        """终止当前测量工作"""
        self.measurement_controller.abort_measurement()
        self.statusBar().showMessage("正在停止測量...", 2000)

    def measurement_finished(self):
        """测量完成后清除工作"""
        self._toggle_controls(True)
        self.statusBar().showMessage("測量完成", 2000)

    def _toggle_controls(self, enable):
        """切换控件状态"""
        self.run_measure_btn.setEnabled(False)
        self.run_sweep_btn.setEnabled(False)
        self.run_power_btn.setEnabled(False)
        self.run_freq_dep_btn.setEnabled(False)
        self.run_current_freq_btn.setEnabled(False)
        
        if enable is True:
            if self.measure_plan == 0:
                self.run_measure_btn.setEnabled(True)
            elif self.measure_plan == 1:
                self.run_power_btn.setEnabled(True)
            elif self.measure_plan == 2:
                self.run_freq_dep_btn.setEnabled(True)
            elif self.measure_plan == 3:
                self.run_current_freq_btn.setEnabled(True)
            elif self.measure_plan == 4:
                self.run_sweep_btn.setEnabled(True)
    # endregion

    # region: 仪器连接
    def connect_device(self):
        """连接SHFQC装置"""
        # 更新连接状态
        self._update_connection_status("連接中...", "orange")
        self.btn_connect.setEnabled(False)
        QApplication.processEvents()  # 强制刷新UI

        try:
            # 连接初始化
            self.session = Session("localhost")
            self.device = self.session.connect_device(self.device_id)  # 使用预设设备ID
            self.shfqc = SHFQC(self.device, self.session)  # 初始化SHFQC控制对象

            # 初始化测量控制器
            self.measurement_controller = MeasurementController(self, self.shfqc)
            # 连接测量控制器的信号
            self.measurement_controller.time_data_updated.connect(
                self.update_time_data)
            self.measurement_controller.freq_data_updated.connect(
                self.update_freq_data)
            self.measurement_controller.power_data_updated.connect(
                self.update_power_data)
            self.measurement_controller.freq_dep_data_updated.connect(
                self.update_freq_dep_data)
            self.measurement_controller.current_freq_data_updated.connect(
                self.update_current_freq_data)
            self.measurement_controller.progress_signal.connect(
                self.progress_update)
            self.measurement_controller.measurement_finished.connect(
                self.measurement_finished)
            self.measurement_controller.error_occurred.connect(
                self.show_error_message)

            # 基础设备检测报错
            if not hasattr(self.device, 'sgchannels'):
                raise ConnectionError("設備無SG頻道，可能型號不符")

            # 设置默认参数
            output_range = self.output_range_combo.currentData()
            self.device.sgchannels[0].output.range(output_range)
            self._update_connection_status(f"已連接 {self.device_id}", "green")

            # 启用UI测量准许开关
            self._toggle_measurement_controls(True)

            # 更新波型预览
            self.update_waveform_preview()
        
        except Exception as e:
            error_msg = f"連接失敗: {str(e)}"
            self._update_connection_status(f"錯誤: {str(e)}", "red")
            self.show_error_message(error_msg)
        finally:
            self.btn_connect.setEnabled(True)

    def _update_connection_status(self, text, color):
        """更新连线状态显示"""
        self.lbl_connect_status.setText(text)
        self.lbl_connect_status.setStyleSheet(f"color: {color};")

    def _toggle_measurement_controls(self, enable):
        """切换测量相关控制状态"""
        self.run_measure_btn.setEnabled(enable)
        self.run_sweep_btn.setEnabled(enable)
        self.run_power_btn.setEnabled(enable)
        self.run_freq_dep_btn.setEnabled(enable)

    # yokogawa 连接
    def check_yoko(self):
        """检查可用的YOKOGAWA设备"""
        while self.link_yoko_layout.count():
            item = self.link_yoko_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        try:
            self.rm = ResourceManager()
            devices = self.rm.list_resources()
            self.DC_id = {}
            for device in devices:
                if "USB" in device:  # 只显示USB设备
                    if "90ZC38697" in device:
                        self.dc1_check = QCheckBox("DC1")
                        self.link_yoko_layout.addWidget(self.dc1_check)
                        self.dc1_check.stateChanged.connect(self.contect_yoko)
                        self.DC_id["DC1"] = device
                    elif "90ZC38696" in device:
                        self.dc2_check = QCheckBox("DC2")
                        self.link_yoko_layout.addWidget(self.dc2_check)
                        self.dc2_check.stateChanged.connect(self.contect_yoko)
                        self.DC_id["DC2"] = device
                    elif "9017D5818" in device:
                        self.dc3_check = QCheckBox("DC3")
                        self.link_yoko_layout.addWidget(self.dc3_check)
                        self.dc3_check.stateChanged.connect(self.contect_yoko)
                        self.DC_id["DC3"] = device
                    elif "9017D5816" in device:
                        self.dc4_check = QCheckBox("DC4")
                        self.link_yoko_layout.addWidget(self.dc4_check)
                        self.dc4_check.stateChanged.connect(self.contect_yoko)
                        self.DC_id["DC4"] = device
        except Exception as e:
            self.yoko_status.append(f"掃描錯誤: {str(e)}")
    
    def contect_yoko(self):
        """连接选中的YOKOGAWA设备"""
        self.yokos = []
        try:
            if hasattr(self, 'dc1_check') and self.dc1_check.isChecked():  # DC1
                device_id = self.DC_id["DC1"]
                visa_resource = self.rm.open_resource(device_id)
                yoko = YOKOGAWA(device_id, visa_resource)
                self.yokos.append(yoko)

            if hasattr(self, 'dc2_check') and self.dc2_check.isChecked():  # DC2
                device_id = self.DC_id["DC2"]
                visa_resource = self.rm.open_resource(device_id)
                yoko = YOKOGAWA(device_id, visa_resource)
                self.yokos.append(yoko)

            if hasattr(self, 'dc3_check') and self.dc3_check.isChecked():  # DC3
                device_id = self.DC_id["DC3"]
                visa_resource = self.rm.open_resource(device_id)
                yoko = YOKOGAWA(device_id, visa_resource)
                self.yokos.append(yoko)

            if hasattr(self, 'dc4_check') and self.dc4_check.isChecked():  # DC4
                device_id = self.DC_id["DC4"]
                visa_resource = self.rm.open_resource(device_id)
                yoko = YOKOGAWA(device_id, visa_resource)
                self.yokos.append(yoko)
                
            for yoko in self.yokos:
                try:
                    yoko.operation_setting('CURR', 200e-3)
                except Exception as e:
                    self.yoko_status.append(f"{yoko.id} 設定錯誤: {str(e)}")
        except Exception as e:
            self.yoko_status.append(f"連接錯誤: {str(e)}")
    # endregion

    # region: 数据保存功能
    def save_data(self):
        """保存数据功能"""
        # 獲取當前數據
        time_data = self.time_domain_data
        freq_data = self.freq_domain_data
        power_data = self.power_data
        power_amps = self.power_amplitudes
        freq_dep_data = self.freq_dep_data
        freq_lo_values = self.freq_lo_values
        current_freq_data = self.current_freq_data
        current_values = self.current_values
        freq_values = self.freq_values
        
        # 創建保存對話框
        save_dialog = SaveDataDialog(
            self,
            time_data=time_data,
            freq_data=freq_data,
            power_data=power_data,
            power_amps=power_amps,
            freq_dep_data=freq_dep_data,
            freq_lo_values=freq_lo_values,
            current_freq_data=current_freq_data,
            freq_values=freq_values,
            current_values=current_values,
            plot_manager=self.plot_manager
        )
        
        if save_dialog.exec() == QDialog.DialogCode.Accepted:
            save_info = save_dialog.get_save_info()
            data_type = save_info['data_type']
            
            # 根據選擇的數據類型調用對應的保存方法
            if data_type == "時域 {單張} 量測":
                DataSaver.save_time_data(time_data, save_info, self)
            elif data_type == "時域 {振幅} 掃描":
                DataSaver.save_power_data(power_data, power_amps, save_info, self)
            elif data_type == "時域 {頻率} 掃描":
                DataSaver.save_freq_dep_data(freq_dep_data, freq_lo_values, save_info, self)
            elif data_type == "時域 {電流頻率} 掃描":
                DataSaver.save_current_freq_data(
                    current_freq_data, 
                    current_values, 
                    freq_values, 
                    save_info, 
                    self
                )
            elif data_type == "頻域 {單張} 量測":
                DataSaver.save_freq_data(freq_data, save_info, self)
            else:
                QMessageBox.warning(self, "警告", "沒有可用的數據或尚未測量")

    def load_data(self):
        """加载数据功能"""
        PlotManager
        dialog = FileLoader(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pass
    # endregion

    # region: Yokogawa 控制功能
    def open_yoko_control(self):
        """开启YOKOGAWA控制对话框"""
        dialog = YOKOGAWAControlDialog(self)
        dialog.show()
    # endregion

    # region: 其他功能
    def update_scheme_ui(self, index):
        """根据选择的方案更新UI显示"""
        self.scheme_stack.setCurrentIndex(index)
        self.measure_plan = index
        self._toggle_controls(True)  # 重新启用对应按钮

    def show_error_message(self, message):
        """显示错误消息"""
        error_dialog = QErrorMessage(self)
        error_dialog.showMessage(message)
        
        # 只在 measurement_controller 存在时调用清理
        if hasattr(self, 'measurement_controller'):
            self.measurement_finished()
    
    def update_power_slice(self, index):
        """更新功率切片图"""
        self.plot_manager.update_power_slice(index)
    
    def update_freq_dep_slice(self, index):
        """更新频率切片图"""
        self.plot_manager.update_freq_dep_slice(index)
    
    def current_freq_slide_valueget(self, notused):
        """处理电流-频率滑块变化"""
        current_index = self.current_slider.value()
        freq_index = self.freq_slider_current_freq.value()
        self.plot_manager.update_current_freq_slice(current_index, freq_index)
    # endregion


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OptimizedSHFQCGUI()
    window.show()
    sys.exit(app.exec())