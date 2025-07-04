from PyQt6.QtWidgets import (
    QVBoxLayout, QGroupBox, QLineEdit, QPushButton, QWidget,
    QLabel, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox,
    QVBoxLayout, QSlider, QTextEdit, QProgressBar, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas
)

import math
class init_components:

    @staticmethod
    def init_components(self):
        #* 設備配置
            #SHFQC
            self.shfqc = None # 提前定義
            self.device_id = "DEV12594" 
            #連接狀態顯示
            self.lbl_connect_status = QLabel("未連接")
            self.lbl_connect_status.setStyleSheet("color: gray;")
            
            #* SHFQC主要參數控制
            #I/O range
            self.input_range_combo = QComboBox()
            self.output_range_combo = QComboBox()
            range_options = [10, 5, 0, -5, -10, -15, -20, -25, -30, -35, -40, -45, -50]
            for value in range_options:
                self.input_range_combo.addItem(f"{value} dBm", userData=value)
                self.output_range_combo.addItem(f"{value} dBm", userData=value)
            self.input_range_combo.setCurrentIndex(6)  # -10 dBm
            self.output_range_combo.setCurrentIndex(6)  # -15 dBm
            #中心頻率
            self.center_freq_spin = ScientificDoubleSpinBox()
            #混頻頻率
            self.digital_lo_spin = ScientificDoubleSpinBox()
            #波型振福增益
            self.gain_spin = QDoubleSpinBox()
            self.gain_spin.setRange(0.0, 1.0)
            self.gain_spin.setSingleStep(0.01)
            self.gain_spin.setValue(1.0)
            self.gain_spin.setDecimals(2)
            
            
            #? 波形生成组件
            #* 波型選擇
            self.wave_type_combo = QComboBox()
            #* 通用波型設置
            #中段波型程度
            self.pulse_length_spin = QSpinBox()
            self.pulse_length_spin.setRange(10, 10000)
            self.pulse_length_spin.setSingleStep(10)
            #前段波型長度
            self.rise_samples_spin = QSpinBox()
            self.rise_samples_spin.setRange(0, 1000)
            self.rise_samples_spin.setSingleStep(10)
            #後段波型長度
            self.fall_samples_spin = QSpinBox()
            self.fall_samples_spin.setRange(0, 1000)
            self.fall_samples_spin.setSingleStep(10)

            #* 高斯波型設置
            #前段標準差
            self.front_std_spin = QSpinBox()
            self.front_std_spin.setRange(1, 100)
            self.front_std_spin.setValue(12)
            #後段標準差
            self.end_std_spin = QSpinBox()
            self.end_std_spin.setRange(1, 100)
            self.end_std_spin.setValue(5)

            #* 指數波型設置
            #前段時間常數
            self.front_tau_spin = QDoubleSpinBox()
            self.front_tau_spin.setRange(0.1, 100.0)
            self.front_tau_spin.setValue(5.0)
            self.front_tau_spin.setSingleStep(0.1)
            #後段時間常數
            self.end_tau_spin = QDoubleSpinBox()
            self.end_tau_spin.setRange(0.1, 100.0)
            self.end_tau_spin.setValue(10.0)
            self.end_tau_spin.setSingleStep(0.1)
            #前段上下開關
            self.front_concave_check = QCheckBox("前端凹面方向")
            self.front_concave_check.setChecked(False)
            #前段上下開關
            self.end_concave_check = QCheckBox("末端凹面方向")
            self.end_concave_check.setChecked(True)

            #* 自訂義波型設置
            #波型輸入窗
            self.custom_formula_edit = QLineEdit("t*exp(-g*t)")
            self.custom_formula_edit.setPlaceholderText("輸入數學公式 (使用變量 t 表示時間)")
            #波型長度設置
            self.custom_points_spin = QSpinBox()
            self.custom_points_spin.setRange(10, 100000)
            self.custom_points_spin.setValue(1000)
            #採樣點數設置
            self.custom_duration_spin = QDoubleSpinBox()
            self.custom_duration_spin.setRange(0, 1e9)
            self.custom_duration_spin.setValue(1)
            self.custom_duration_spin.setDecimals(9)
            self.custom_duration_spin.setSingleStep(0.01)
            #參數值顯示標籤
            self.custom_params_label = QLabel("參數: 無")

            #? 實驗方案選擇
            #* 實驗量測方案選擇控件
            self.scheme_combo = QComboBox()
            self.scheme_combo.addItems([
                "時域 {單張} 量測", 
                "時域 {振幅} 掃描", 
                "時域 {頻率} 掃描",
                "時域 {電流頻率} 掃描",
                "頻域 {單張} 量測"
            ])
            self.measure_plan = 0
            #* 時域 {單張} 量測
            #量測時長
            self.window_dur_spin_time = QSpinBox()
            self.window_dur_spin_time.setRange(0, 100000)
            self.window_dur_spin_time.setSingleStep(100)
            self.window_dur_spin_time.setSuffix(" ns")
            #觸發延遲
            self.trigger_delay_spin_time = QSpinBox()
            self.trigger_delay_spin_time.setRange(0, 10000)
            self.trigger_delay_spin_time.setSingleStep(10)
            self.trigger_delay_spin_time.setSuffix(" ns")
            #平均次數
            self.num_avg_spin_time = QSpinBox()
            self.num_avg_spin_time.setRange(1, 100000)
            self.num_avg_spin_time.setSingleStep(10)
            #* 時域 {振幅} 掃描
            #起始振幅
            self.power_start_spin = QDoubleSpinBox()
            self.power_start_spin.setRange(0.0, 1.0)
            self.power_start_spin.setSingleStep(0.01)
            self.power_start_spin.setValue(0.1)
            #終點振幅
            self.power_stop_spin = QDoubleSpinBox()
            self.power_stop_spin.setRange(0.0, 1.0)
            self.power_stop_spin.setSingleStep(0.01)
            self.power_stop_spin.setValue(1.0)
            #量測次數
            self.power_points_spin = QSpinBox()
            self.power_points_spin.setRange(2, 2000)
            self.power_points_spin.setValue(10)
            #量測時長
            self.window_dur_spin_power = QSpinBox()
            self.window_dur_spin_power.setRange(0, 100000)
            self.window_dur_spin_power.setSingleStep(100)
            self.window_dur_spin_power.setSuffix(" ns")
            #觸發延遲
            self.trigger_delay_spin_power = QSpinBox()
            self.trigger_delay_spin_power.setRange(0, 10000)
            self.trigger_delay_spin_power.setSingleStep(10)
            self.trigger_delay_spin_power.setSuffix(" ns")
            #平均次數
            self.num_avg_spin_power = QSpinBox()
            self.num_avg_spin_power.setRange(1, 100000)
            self.num_avg_spin_power.setSingleStep(10)
            #* 時域 {頻率} 掃描
            #掃頻起點終點頻率
            self.freq_dep_start_spin = ScientificDoubleSpinBox()
            self.freq_dep_stop_spin = ScientificDoubleSpinBox()
            #量測點數
            self.freq_dep_points_spin = QSpinBox()
            self.freq_dep_points_spin.setRange(2, 2000)
            self.freq_dep_points_spin.setValue(10)
            #量測時長
            self.window_dur_spin_freq = QSpinBox()
            self.window_dur_spin_freq.setRange(0, 10000)
            self.window_dur_spin_freq.setSingleStep(100)
            self.window_dur_spin_freq.setSuffix(" ns")
            #觸發延遲
            self.trigger_delay_spin_freq = QSpinBox()
            self.trigger_delay_spin_freq.setRange(0, 10000)
            self.trigger_delay_spin_freq.setSingleStep(10)
            self.trigger_delay_spin_freq.setSuffix(" ns")
            #平均次數
            self.num_avg_spin_freq = QSpinBox()
            self.num_avg_spin_freq.setRange(1, 100000)
            self.num_avg_spin_freq.setSingleStep(10)
            #* 時域 {電流頻率} 掃描
            # 起始電流
            self.current_start_spin = QDoubleSpinBox()
            self.current_start_spin.setRange(-200, 200)
            self.current_start_spin.setSingleStep(0.001)
            self.current_start_spin.setDecimals(3)
            self.current_start_spin.setValue(0.0)
            # 終點電流
            self.current_stop_spin = QDoubleSpinBox()
            self.current_stop_spin.setRange(-200, 200)
            self.current_stop_spin.setSingleStep(0.001)
            self.current_stop_spin.setDecimals(3)
            self.current_stop_spin.setValue(1.0)
            # 電流量測點數
            self.current_points_spin = QSpinBox()
            self.current_points_spin.setRange(2, 1000)
            self.current_points_spin.setValue(10)
            #掃頻起點終點頻率
            self.freq_start_current_freq = ScientificDoubleSpinBox()
            self.freq_stop_current_freq = ScientificDoubleSpinBox()
            #量測點數
            self.freq_points_current_freq = QSpinBox()
            self.freq_points_current_freq.setRange(2, 100)
            self.freq_points_current_freq.setValue(10)
            #量測時長
            self.window_dur_spin_current_freq = QSpinBox()
            self.window_dur_spin_current_freq.setRange(0, 10000)
            self.window_dur_spin_current_freq.setSingleStep(100)
            self.window_dur_spin_current_freq.setSuffix(" ns")
            #觸發延遲
            self.trigger_delay_spin_current_freq = QSpinBox()
            self.trigger_delay_spin_current_freq.setRange(0, 10000)
            self.trigger_delay_spin_current_freq.setSingleStep(10)
            self.trigger_delay_spin_current_freq.setSuffix(" ns")
            #平均次數
            self.num_avg_spin_current_freq = QSpinBox()
            self.num_avg_spin_current_freq.setRange(1, 100000)
            self.num_avg_spin_current_freq.setSingleStep(10)
            #* 頻域 {單張} 量測
            #掃頻起始結束頻率
            self.lo_start_spin = ScientificDoubleSpinBox()
            self.lo_stop_spin = ScientificDoubleSpinBox()
            #量測點數
            self.lo_points_spin = QSpinBox()
            self.lo_points_spin.setRange(2, 100000)
            self.lo_points_spin.setSingleStep(100)
            #平均次數
            self.avg_num_spin = QSpinBox()
            self.avg_num_spin.setRange(1, 200)
            self.avg_num_spin.setSingleStep(5)
            #積分時間
            self.int_time_spin = QSpinBox()
            self.int_time_spin.setRange(10, 16700)
            self.int_time_spin.setSingleStep(10)
            #* Yokogawa控制
            self.yoko_status = QTextEdit()
            self.yoko_status.setReadOnly(True)
            self.yoko_status.setMaximumHeight(100)
            self.link_yoko_devices_group = QGroupBox("選擇YOKOGAWA設備")
            self.link_yoko_layout = QVBoxLayout(self.link_yoko_devices_group)
            self.yokos = []
            #* 量測進度條
            self.time_label = QLabel("等待實驗進行")
            self.progress_bar = QProgressBar()
            self.progress_bar.setValue(0)

            #? 按鈕
            #連接SHFQC 按鈕
            self.btn_connect = QPushButton("連接設備")
            #公式解析按鈕
            self.parse_formula_btn = QPushButton("解析公式")
            #參數設置按鈕
            self.custom_params_btn = QPushButton("設置參數")
            #電流-頻率掃描DC連線按鈕
            self.yoko_devices_contect = QPushButton("DC連線")
            #實驗量測按鈕
            self.run_measure_btn = QPushButton("時域{單張}量測")
            self.run_power_btn = QPushButton("時域{振幅}掃描")
            self.run_freq_dep_btn = QPushButton("時域{頻率}掃描")
            self.run_current_freq_btn = QPushButton("時域{電流頻率}掃描")
            self.run_sweep_btn = QPushButton("頻域{單張}量測")
            self.abort_btn = QPushButton("中止")
            #數據保存按鈕
            self.save_data_btn = QPushButton("保存數據")
            self.load_data_btn = QPushButton("加載數據")
            self.save_config_btn = QPushButton("保存配置")
            #其他儀器控制按鈕
            self.btn_control_yoko = QPushButton("控制YOKOGAWA")
            
            #? 繪圖區組件 
            #* 波型預覽畫布
            self.wave_preview = FigureCanvas(Figure(figsize=(6, 4)))
            #* 時域量測數據畫布
            self.time_plot = FigureCanvas(Figure(figsize=(10, 6)))
            #* 頻域量測數據畫布
            self.freq_plot = FigureCanvas(Figure(figsize=(10, 6)))
            #* 功率掃描量測數據畫布
            self.power_overview = FigureCanvas(Figure(figsize=(10, 4)))
            self.power_slice = FigureCanvas(Figure(figsize=(10, 4)))
            #功率選擇滑塊
            self.power_slider = QSlider(Qt.Orientation.Horizontal)
            self.power_slider.setRange(0, 100)
            self.power_slider.setEnabled(False)
            self.power_label = QLabel("選定功率: 0.0")
            #* 頻率掃描量測數據畫布        
            self.freq_dep_overview = FigureCanvas(Figure(figsize=(10, 4)))
            self.freq_dep_slice = FigureCanvas(Figure(figsize=(10, 4)))
            #頻率選擇滑塊
            self.freq_dep_slider = QSlider(Qt.Orientation.Horizontal)
            self.freq_dep_slider.setRange(0, 100)
            self.freq_dep_slider.setEnabled(False)
            self.freq_dep_label = QLabel("選定頻率: 0.0 MHz")
            #* 電流-頻率掃描量測數據畫布   
            self.current_freq_overview = FigureCanvas(Figure(figsize=(10, 4)))
            self.current_freq_slice = FigureCanvas(Figure(figsize=(10, 4)))
            #電流選擇滑塊
            self.current_slider = QSlider(Qt.Orientation.Horizontal)
            self.current_slider.setRange(0, 100)
            self.current_slider.setEnabled(False)
            self.current_label = QLabel("0.0 mA")
            #頻率選擇滑塊
            self.freq_slider_current_freq = QSlider(Qt.Orientation.Horizontal)
            self.freq_slider_current_freq.setRange(0, 100)
            self.freq_slider_current_freq.setEnabled(False)
            self.freq_label_current_freq = QLabel("0.0 MHz")


class ScientificDoubleSpinBox(QWidget):
    valueChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._unit_map = {
            "k": 1, "M": 2, "G": 3
        }
        self._unit_list = ["k", "M", "G"]
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.coeff_spin = QDoubleSpinBox()
        self.coeff_spin.setRange(-1000, 1000)
        self.coeff_spin.setSingleStep(0.1)
        self.coeff_spin.setDecimals(3)
        self.coeff_spin.valueChanged.connect(self._emit_value_changed)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(self._unit_list)
        self.unit_combo.setCurrentText("")  # 預設 base
        self.unit_combo.currentIndexChanged.connect(self._emit_value_changed)

        unit_label = QLabel("Hz")

        layout.addWidget(self.coeff_spin)
        layout.addWidget(self.unit_combo)
        layout.addWidget(unit_label)
        layout.addStretch()

    def value(self):
        """取得完整數值"""
        coeff = self.coeff_spin.value()
        unit = self.unit_combo.currentText()
        exponent = self._unit_map.get(unit, 0)
        return coeff * (1000 ** exponent)

    def setValue(self, value):
        """設置完整數值"""
        if value == 0:
            self.coeff_spin.setValue(0)
            self.unit_combo.setCurrentText("")
            return

        exponent = math.floor(math.log(abs(value), 1000))
        coeff = value / (1000 ** exponent)

        if abs(coeff) >= 1000:
            coeff /= 1000
            exponent += 1
        elif abs(coeff) < 1:
            coeff *= 1000
            exponent -= 1

        best_unit = min(self._unit_map, key=lambda k: abs(self._unit_map[k] - exponent))
        self.unit_combo.setCurrentText(best_unit)
        self.coeff_spin.setValue(coeff)

    def _emit_value_changed(self):
        self.valueChanged.emit(self.value())