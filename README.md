# Waymo 2025 Vision-based End-to-End Driving

本專案對應 https://waymo.com/intl/zh-tw/open/challenges/2025/e2e-driving/ 。
模型以相機影像、歷史狀態及路線資訊預測未來 5 秒軌跡，4 Hz，共 `(20, 2)` 個 XY 座標；第一點為未來 0.25 秒。

## Ubuntu（主要執行環境）

官方教學指定 `waymo-open-dataset-tf-2-12-0==1.6.7`，PyPI 僅提供 Linux x86_64 wheel。
該版本實際相依 TensorFlow 2.13；本專案使用 Python 3.10，先以 CPU 跑通資料流程。
GPU 訓練環境需另外依 Ubuntu 主機顯示卡配置，目前未配置 CUDA。

在 Ubuntu 的專案資料夾執行：

```bash
# 僅在缺少這些系統套件時安裝。
sudo apt update
sudo apt install -y python3-venv libgomp1 libglib2.0-0
bash scripts/setup-ubuntu.sh
source .venv-ubuntu/bin/activate
python -m jupyterlab --no-browser --ip=127.0.0.1
```

安裝腳本會建立獨立環境、安裝官方套件、檢查相依套件、測試 TFRecord／protobuf 序列化及相機原生模組載入，成功後輸出 `requirements-ubuntu-resolved.txt`。
首次安裝需要網路與數 GB 空間。若透過 SSH 使用 Jupyter，可在本機執行 `ssh -L 8888:127.0.0.1:8888 YOUR_HOST`，再開啟終端機顯示的 token 網址。
環境放在 `.venv-ubuntu`，請在 Ubuntu 建立；勿從其他作業系統複製虛擬環境。

## 官方教學與資料

`notebooks/official_vision_based_e2e_driving.ipynb` 是官方原始教學的副本：
https://github.com/waymo-research/waymo-open-dataset/blob/master/tutorial/tutorial_vision_based_e2e_driving.ipynb

先至 https://waymo.com/open/download/ 取得資料權限與資料；資料尚未下載。
請選擇 **E2E Driving proto** 格式，放入 `data/`，再修改 notebook 的 `DATASET_FOLDER` 與檔案匹配方式。
Notebook 原本為 Colab 設計；已完成環境安裝時可略過 `!pip install` 儲存格。請依序執行，並以實際資料驗證。
提交檔案為 `E2EDChallengeSubmission` protobuf，再封裝成 `.tar.gz`；本專案不會自動提交。

## 可選 Docker 環境

```bash
docker compose up --build
```

使用 Jupyter 日誌顯示的 token 開啟 http://localhost:8888 。容器建置包含官方環境 smoke test。
Docker 設定以 CPU 為基礎，尚未在本機建置驗證。

正式的 Ubuntu 安裝與測試結果，需在可連線的 Ubuntu 主機執行後確認。
