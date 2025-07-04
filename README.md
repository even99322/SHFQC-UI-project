# SHFQC-UI-project

此專案提供以 PyQt6 建立的 Zurich Instruments SHFQC 控制介面，
可進行波形產生、量測控制、結果繪圖與資料儲存等功能。

## 功能簡介
- **波形產生**：支援高斯脈衝、方波脈衝、指數脈衝以及自訂波形。
- **量測流程**：包含單次時域量測、功率掃描、頻率掃描及電流/頻率雙重掃描。
- **即時監控**：量測過程可於對話框即時顯示進度與當前參數。
- **資料管理**：量測結果可儲存為 CSV，並支援再次載入與繪圖。
- **設定檔**：使用 `shfqc_config.ini` 儲存主要參數與波形設定。

## 安裝方式
1. 安裝 Python 3.10 以上版本。
2. 安裝相依套件：
   ```bash
   pip install PyQt6 matplotlib numpy scipy zhinst-toolkit pyvisa
   ```
3. 連接 SHFQC 與必要的儀器 (如 YOKOGAWA) 後，即可執行程式。

## 執行方法
在專案根目錄下執行：
```bash
python "SHFQC UI/SHFQC 穩定版本.py"
```
程式啟動後即可透過圖形介面進行各項設定與量測。

## 專案結構
```
SHFQC-UI-project/
├── README.md               本說明文件
└── SHFQC UI/
    ├── SHFQC 穩定版本.py    主程式入口
    ├── icon.png             介面圖示
    ├── shfqc_config.ini     預設設定檔
    └── library/             功能模組
        ├── device_control.py        儀器控制
        ├── waveform_generation.py   波形產生
        ├── measurement_controller.py 量測執行緒控制
        ├── plot_manager.py          繪圖管理
        ├── File_Storage.py          資料儲存/載入
        ├── RealTimeMonitorDialog.py 即時監控對話框
        ├── config_handler.py        設定檔處理
        ├── Formula_Parser.py        自訂波形公式解析
        └── init_UI/                 介面組件建構
```

## 重構建議
依照現有模組職能，可將專案整理為單一套件，例如 `shfqc_ui`：
1. **gui**：放置 `init_UI`、`gui_components`、`RealTimeMonitorDialog` 等與介面相關的模組。
2. **core**：包含 `device_control`、`measurement_controller`、`waveform_generation` 等核心邏輯。
3. **data**：負責 `File_Storage`、`config_handler` 等資料處理與設定管理。
4. **utils**：如 `plot_manager`、`Formula_Parser` 等工具類別。
5. 重新命名主程式為 `main.py`，並在套件根目錄提供啟動腳本。
6. 引入單元測試 (pytest) 以確保各模組穩定。

藉由上述調整，可提升程式的可維護性與擴充性，也方便未來封裝發佈。
