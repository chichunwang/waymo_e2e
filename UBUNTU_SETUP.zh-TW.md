# Waymo E2E Driving：Ubuntu 入門操作手冊

這份手冊帶你從現有專案資料夾開始，完成環境安裝、讀取第一筆資料及執行官方範例。**第一次的目標是看到相機影像並成功讀出軌跡**，之後再進入模型訓練。

目前專案已有安裝腳本與官方教學副本，尚未在你的 Ubuntu 實際安裝測試，尚未下載資料，也沒有訓練程式、訓練完成的模型或 CUDA 設定。以下成功訊息是驗收標準，不代表已在你的機器上通過。

## 1. 把專案帶到 Ubuntu

目前 Windows 位置：

```text
C:\Users\ricky\Downloads\Project\waymo_e2e
```

將整個 `waymo_e2e` 資料夾透過隨身碟、共用硬碟或網路複製到 Ubuntu。以下假設你放在：

```text
~/projects/waymo_e2e
```

雙系統也建議先複製到 Ubuntu 的家目錄，再建立虛擬環境。隱藏設定檔如 `.gitignore`、`.dockerignore` 可以一起複製；不需搬移 `.tools` 或任何已建好的虛擬環境。

開啟 Ubuntu 終端機，執行：

```bash
cd ~/projects/waymo_e2e
pwd
ls
uname -m
df -h .
```

你應該看到 `README.md`、`requirements-linux.txt`、`scripts`、`notebooks`、`data`、`outputs` 等項目。`uname -m` 應輸出 `x86_64`；本設定不適用 ARM／aarch64。

如果資料夾在其他位置，將本手冊所有 `~/projects/waymo_e2e` 改成實際路徑。Ubuntu 不使用 `C:\...` 路徑。

## 2. 首次安裝環境

在專案根目錄依序執行：

```bash
sudo apt update
sudo apt install -y python3-venv libgomp1 libglib2.0-0
bash scripts/setup-ubuntu.sh
```

輸入 sudo 密碼時，終端機不會顯示字元，這是正常現象。首次安裝需要網路，會下載 Python 和較大的科學運算套件，請等指令完成。

腳本會建立下列內容：

| 項目 | 用途 |
| --- | --- |
| `.bootstrap/` | 安裝工具 uv 的隔離環境 |
| `.venv-ubuntu/` | 本專案 Python 3.10 執行環境 |
| `requirements-ubuntu-resolved.txt` | 安裝及檢查成功後記錄的套件版本 |

主要官方套件為 `waymo-open-dataset-tf-2-12-0==1.6.7`。雖然名稱含 `2-12-0`，此版本套件相依指定的是 TensorFlow 2.13；不要自行改成 TensorFlow 2.12。套件版本依據 [PyPI 1.6.7 metadata](https://pypi.org/pypi/waymo-open-dataset-tf-2-12-0/1.6.7/json)。

安裝成功時，應看到類似：

```text
PASS: TFRecord / E2EDFrame / submission round trip; camera ops imported.
Ready: source .venv-ubuntu/bin/activate ...
```

這項檢查使用人工建立的資料，驗證套件載入與檔案格式，不代表真實資料、模型準確度或 GPU 已驗證。

如果出錯，先閱讀最後一段錯誤，參考第 9 節；不要忽略錯誤繼續下一步。

## 3. 啟用環境並再次確認

```bash
source .venv-ubuntu/bin/activate
which python
python --version
python scripts/check_environment.py --official
```

`which python` 應指向本專案 `.venv-ubuntu/bin/python`，版本應為 Python 3.10。`GPUs: []` 表示目前 TensorFlow 沒有偵測到可用 GPU；可以先完成讀檔與範例操作。

本專案尚未配置 GPU 訓練環境。之後若要配置，先提供 Ubuntu 版本、顯示卡型號，以及 NVIDIA 主機的 `nvidia-smi` 輸出，再決定驅動與 CUDA 組合。

## 4. 取得第一份資料

在瀏覽器開啟 [Waymo 資料下載入口](https://waymo.com/open/download/)，使用你的帳號登入並完成頁面要求的存取程序。

選擇對應 2025 挑戰的 End-to-End Driving 資料，且必須是官方 notebook 支援的 **E2E Driving proto** 格式。不要直接以其他 Waymo 資料集或不同格式取代。[官方教學](https://github.com/waymo-research/waymo-open-dataset/blob/master/tutorial/tutorial_vision_based_e2e_driving.ipynb)以這種格式讀取資料。

第一次先取得一個 validation TFRecord 分片，確認流程能跑通，再擴大下載。下載的實際網址與權限取決於登入後的頁面，本手冊不假設固定的儲存桶路徑。

建議目錄如下，檔名保留下載時的原名：

```text
waymo_e2e/
└── data/
    ├── training/
    ├── validation/
    │   └── 實際下載的 TFRecord 檔案
    └── test/
```

可先建立目錄：

```bash
mkdir -p data/training data/validation data/test
find data/validation -type f | head
```

若取得的是封裝的壓縮檔，請依下載頁說明解開；下文使用未壓縮的 TFRecord。不要把 HTML 登入頁或 `.tar.gz` 壓縮包當成 TFRecord。

## 5. 開啟 Jupyter 與官方 notebook

在 Ubuntu 的專案根目錄執行：

```bash
source .venv-ubuntu/bin/activate
python -m jupyterlab --no-browser --ip=127.0.0.1
```

保持終端機開啟，在同一台 Ubuntu 的瀏覽器開啟它顯示的 `http://127.0.0.1:8888/...token=...` 網址。若 8888 已被占用，以終端機實際顯示的連接埠為準。

在左側檔案列表進入 `notebooks`，將 `official_vision_based_e2e_driving.ipynb` 複製成 `01_first_sample.ipynb` 再操作，保留原始範例供比對。

選擇 Python 3 kernel。新增一格並執行：

```python
import sys
print(sys.executable)
```

輸出應包含 `.venv-ubuntu/bin/python`。每次按 `Shift + Enter` 執行目前的儲存格；左側顯示 `[*]` 代表執行中。

### 修改資料路徑

略過官方 notebook 最前面的 `!pip install ...` 儲存格，因為已由安裝腳本處理。先執行 imports，再將 `DATASET_FOLDER` 與三個檔案樣式改為：

```python
from pathlib import Path

# 若你使用不同位置，請修改這行。
PROJECT_ROOT = Path.home() / 'projects' / 'waymo_e2e'
DATASET_FOLDER = str(PROJECT_ROOT / 'data')
TRAIN_FILES = str(PROJECT_ROOT / 'data/training/*.tfrecord*')
VALIDATION_FILES = str(PROJECT_ROOT / 'data/validation/*.tfrecord*')
TEST_FILES = str(PROJECT_ROOT / 'data/test/*.tfrecord*')
```

這個範例假設檔名含 `.tfrecord`。若真實檔名不同，請調整樣式，或先使用單一檔案的完整路徑。

在建立 dataset 前加入：

```python
filenames = tf.io.matching_files(VALIDATION_FILES)
print('找到檔案數：', len(filenames))
assert len(filenames) > 0, f'找不到資料：{VALIDATION_FILES}'
print(filenames[:3].numpy())
```

若數量為 0，先修正路徑，不要往下執行。

## 6. 讀出第一筆資料並顯示影像

依序執行 notebook 的 dataset 建立與 `E2EDFrame` 解析儲存格。你也可以用下面這段確認：

```python
dataset = tf.data.TFRecordDataset(filenames, compression_type='')
dataset_iter = dataset.as_numpy_iterator()
data = wod_e2ed_pb2.E2EDFrame()
data.ParseFromString(next(dataset_iter))
print('frame：', data.frame.context.name)
print('相機影像數：', len(data.frame.images))
print('future X 點數：', len(data.future_states.pos_x))
```

接著執行官方 notebook 的 `return_front3_cameras` 函式與顯示影像儲存格，預期能看到前方三個相機的拼接圖。之後才執行投影函式與軌跡疊圖。

第一次做到以下三件事就完成資料流程驗收：

1. 環境檢查顯示 PASS。
2. 能讀取真實 TFRecord 並列出 frame 名稱與影像數。
3. 能在 notebook 顯示相機影像。

若找不到 future states，請先確認使用的是 validation 資料與正確格式；不要假設 test 檔案具備相同標註。

## 7. 範例提交檔與模型開發的差別

官方 notebook 的 `Submission generation` 使用全零軌跡，示範停車預測的封裝方式。這不是訓練好的自動駕駛模型，也不是完整測試集的有效參賽結果。

挑戰要求每筆預測提供未來 5 秒、每秒 4 個 XY 座標，共 `(20, 2)`，第一點在未來 0.25 秒。提交格式為 `E2EDChallengeSubmission` protobuf，封裝成 `.tar.gz`；需涵蓋官方指定的 test frames。評估以 RFS 為主、ADE 作為次要指標。[挑戰規格](https://waymo.com/intl/zh-tw/open/challenges/2025/e2e-driving/)

要測試封裝，可將 notebook 的輸出目錄改為：

```python
submission_file_base = str(PROJECT_ROOT / 'outputs' / 'demo_submission')
```

執行提交範例的序列化儲存格後，在 Ubuntu 終端機的專案根目錄執行：

```bash
tar -czf outputs/demo_submission.tar.gz -C outputs demo_submission
tar -tzf outputs/demo_submission.tar.gz
```

先把這份封裝留在本機。正式提交前，需以模型產生的全部預測取代全零範例，填入真實作者與方法資訊、核對 frame 清單與軌跡格式，並查看當時網站的提交狀態。此專案不會自動上傳。

資料流程成功後，建議依序開發：

| 階段 | 要完成的工作 |
| --- | --- |
| 基準線 | 產生停車／定速軌跡，建立可重複的驗證結果 |
| 資料載入 | 整理影像、歷史狀態、路線與目標軌跡；保持 train/validation 分離 |
| 第一個模型 | 建立影像與狀態輸入到 20 個 XY 點的模型，先確認小批資料可訓練 |
| 驗證 | 檢查座標系、時間點、遮罩與評估對象是否一致；保存預測與視覺化 |
| 正式推論 | 對指定 test frames 推論、驗證 protobuf 並封裝 |

以上模型與訓練工作尚未實作。不要以未來影像、future states 或評分者軌跡作為模型的推論輸入。

### 官方 notebook 的 RFS 段落注意事項

單一分片不一定包含具有評分標註的 frame。搜尋後若 `data_contain_label is None`，先略過 RFS 段落，不要直接存取 `.frame`。

目前下載的官方範例在 RFS 迴圈中以 `data.past_states` 取得初速；若你修改範例為多筆資料，應改從當前的 `data_list[i].past_states` 取得，避免用到其他 frame 的速度。比較 RFS 前也要確認軌跡、分數與速度屬於同一筆資料。

## 8. 日常啟動與關閉

完成首次安裝後，每次工作只需要：

```bash
cd ~/projects/waymo_e2e
source .venv-ubuntu/bin/activate
python -m jupyterlab --no-browser --ip=127.0.0.1
```

不需要每天重跑安裝腳本。完成工作時先儲存 notebook，再回終端機按 `Ctrl + C`，依提示結束 Jupyter，最後執行 `deactivate`。

若 Ubuntu 在另一台電腦且已配置 SSH，可從 Windows 終端機建立通道：

```powershell
ssh -L 8888:127.0.0.1:8888 使用者名稱@Ubuntu主機位址
```

在該 SSH 連線內啟動 Jupyter，再於 Windows 瀏覽器使用它顯示的 localhost token 網址。不使用 SSH 的雙系統情況，直接在 Ubuntu 瀏覽器操作即可。

## 9. 常見問題

| 現象 | 處理方式 |
| --- | --- |
| `cd: No such file or directory` | 專案位置不同；在檔案管理員確認位置，改用實際路徑 |
| `ensurepip is not available` | 安裝 `python3-venv`；若仍失敗，按 Ubuntu 錯誤訊息安裝對應 Python 版本的 venv 套件 |
| `No matching distribution` | 確認是 Linux x86_64、Python 3.10，並保留完整套件名稱與錯誤訊息 |
| `ModuleNotFoundError` | 確認環境已啟用，且 notebook 的 `sys.executable` 指向 `.venv-ubuntu` |
| 找不到 TFRecord／`StopIteration` | 檢查檔案樣式與資料是否為空；迭代器用完時重新建立 dataset iterator |
| `DataLossError` | 核對是否下載完整、是否為正確格式，以及 TFRecord 壓縮設定；不要直接跳過損壞資料 |
| 找不到 `libgomp`／相機模組載入失敗 | 確認系統相依套件已裝，再執行官方環境檢查並保留完整錯誤 |
| `GPUs: []` | CPU 起步可繼續；GPU 訓練需另行配置，安裝 Python 套件不等於已配置 CUDA |
| `Killed`／kernel 自動重啟 | 可能記憶體不足；先只讀一個分片及一筆資料，避免把整個 dataset 轉成 list |
| `bash` 出現 `\r`／bad interpreter | shell 檔案被轉成 Windows CRLF；將 `scripts/setup-ubuntu.sh` 儲存為 LF 後重試 |
| 安裝中斷或相依衝突 | 保存完整錯誤；先釐清原因，避免逐一升級套件而破壞官方相依版本 |

需要協助排錯時，請提供：執行的指令、完整錯誤最後約 50 行，以及下面資訊。token 網址不需要提供。

```bash
cat /etc/os-release
uname -m
df -h .
free -h
.venv-ubuntu/bin/python --version
```

## 10. 第一次操作清單

- [ ] 專案已放入 Ubuntu，且 `uname -m` 為 `x86_64`。
- [ ] 安裝腳本成功結束，官方環境檢查顯示 PASS。
- [ ] 下載至少一個 validation TFRecord 分片。
- [ ] 啟動 Jupyter，確認 kernel 使用專案虛擬環境。
- [ ] 修改資料路徑，檔案匹配數大於 0。
- [ ] 讀到第一筆 frame，顯示前方相機影像。
- [ ] 儲存操作 notebook，記錄資料版本與套件版本。

先完成這份清單，再開始模型開發。
