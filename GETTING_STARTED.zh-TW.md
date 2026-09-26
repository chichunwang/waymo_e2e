# Waymo E2E Challenge 入門手冊

本手冊以 **2025 Vision-based End-to-End Driving Challenge** 為範圍，說明要解決什麼問題、如何理解資料、如何建立第一個實驗，以及如何判斷模型是否有進步。

第一次做這個挑戰，建議先完成「讀一筆資料 → 畫出軌跡 → 建立簡單基準 → 訓練小模型 → 驗證 → 封裝預測」的完整流程，再增加模型規模。

## 1. 這個挑戰到底在做什麼？

給定某個駕駛時刻之前可取得的相機影像、車輛歷史狀態與行駛意圖，預測自車接下來應該如何移動。挑戰特別關注少見且難處理的駕駛情境，例如施工、突發障礙物與不尋常的道路參與者行為。[官方挑戰說明](https://waymo.com/intl/zh-tw/open/challenges/2025/e2e-driving/)

在這個任務中，模型的輸出是一串**自車未來位置**，不是方向盤角度、油門或煞車指令，也不是其他車輛的軌跡。

```text
相機影像 ───────┐
自車歷史狀態 ───┼──→ 模型 ──→ 未來 20 個 (x, y) 位置
行駛意圖 ───────┘
```

「End-to-End」描述從感測輸入到駕駛結果的學習方式，並不強制使用某個網路架構。你可以先使用簡單影像編碼器與軌跡回歸頭，之後再研究時序、多視角或其他更複雜的方法。

## 2. 先記住輸出的精確定義

| 項目 | 定義 |
| --- | --- |
| 預測對象 | 自車，也稱 ego vehicle |
| 預測長度 | 未來 5 秒 |
| 採樣頻率 | 4 Hz，每 0.25 秒一點 |
| 輸出形狀 | 每筆 `(20, 2)`，每點為 `(x, y)` |
| 時間點 | 0.25、0.50、…、5.00 秒，不含當下 0 秒 |
| 單位 | 公尺 |
| 座標方向 | x 向前、y 向左；是車體座標，不是像素座標 |

提交 proto 將當下自車位置定為原點；資料 proto 進一步定義原點在後軸中央。不要直接拿經緯度、世界座標或影像像素當輸出。[資料座標定義](https://raw.githubusercontent.com/waymo-research/waymo-open-dataset/master/src/waymo_open_dataset/protos/end_to_end_driving_data.proto)、[提交軌跡定義](https://raw.githubusercontent.com/waymo-research/waymo-open-dataset/master/src/waymo_open_dataset/protos/end_to_end_driving_submission.proto)

例如，以每秒 2 公尺直行的簡單預測，第一點是 `(0.5, 0)`，最後一點是 `(10, 0)`。這只是幫助理解單位與時間，不代表好的駕駛策略。

## 3. 一筆資料裡有什麼？

本專案官方 notebook 使用 **E2E Driving proto** 格式：TFRecord 裝著序列化的 `E2EDFrame`。TFRecord 是外層儲存容器，protobuf 定義每筆資料有哪些欄位。

| 欄位 | 內容 | 在實驗中的角色 |
| --- | --- | --- |
| `frame.context.name` | 這筆 frame 的唯一識別名稱 | 對應預測、標註與提交結果 |
| `frame.images` | 多個相機的影像與相關資訊 | 模型的視覺輸入 |
| `frame.context.camera_calibrations` | 相機標定資訊 | 幾何投影或幾何感知模型 |
| `past_states` | 過去 4 秒、4 Hz 的自車狀態 | 歷史輸入 |
| `intent` | 未知、直行、左轉或右轉 | 行駛意圖輸入 |
| `future_states` | 未來 5 秒的位置 | 訓練／驗證目標，不能當推論輸入 |
| `preference_trajectories` | 部分 frame 的候選軌跡與人工評分 | RFS 評估或合適的訓練監督 |

歷史欄位包括位置、速度與加速度；`future_states` 的 z 值可用於視覺化，但提交目標只用 x、y。評分軌跡只存在於部分 frame，空值或分數 `-1` 代表無有效評分，不可當成 0 分。[E2EDFrame schema](https://raw.githubusercontent.com/waymo-research/waymo-open-dataset/master/src/waymo_open_dataset/protos/end_to_end_driving_data.proto)

載入影像時應依相機名稱排列，不要假設容器中的順序就是固定相機順序。同樣地，相機影像與 calibration 應以名稱對應。

### Segment 和 frame 的差別

Segment 是一段連續駕駛片段；frame 是片段中的一個時刻。官方資料包含 4,021 段片段，training 2,037 段、validation 479 段，其餘為 test。訓練與驗證片段提供 20 秒資料；test 提供前 12 秒，後續部分留供評估。挑戰的環視影像來自 8 個相機。[資料分割說明](https://waymo.com/intl/zh-tw/open/challenges/2025/e2e-driving/)

不要把同一段片段的相鄰 frames 隨機拆到 train 與 validation；兩者高度相似，會讓驗證結果過度樂觀。先沿用官方分割。若只用子集，也要記錄片段／frame 清單。

此外，`frame.context.name` 在 E2E schema 中是 **frame ID**，不要因為一般 Waymo 資料集的習慣而直接當成 segment ID。

## 4. 要如何評估「開得好」？

### ADE：預測位置離參考位置多遠

對相同時間點的預測與參考 XY 計算歐氏距離，再取平均：

```text
ADE = 所有有效時間點的 sqrt((預測 x − 參考 x)² + (預測 y − 參考 y)²) 的平均
```

單位是公尺，越低越好。它容易實作，適合先檢查資料與訓練流程，但不能完整代表駕駛品質。例如，兩種避障路徑都可能合理，卻與某一條參考軌跡距離不同。

請在報告寫清楚 ADE 的參考對象。官方教學中的 logged-future ADE 可做開發指標；排行榜描述的次要 ADE 則對照最高人工評分的軌跡，兩者不可直接混稱。[官方教學](https://github.com/waymo-research/waymo-open-dataset/blob/master/tutorial/tutorial_vision_based_e2e_driving.ipynb)、[排行榜指標](https://waymo.com/intl/zh-tw/open/challenges/2025/e2e-driving/)

### RFS：預測接近哪種人工評價的駕駛行為

Rater Feedback Score 使用人工評分軌跡與容許區域判斷預測品質，容許範圍會考慮速度，以及縱向／橫向差異；它不是單純的 L2 距離。官方以 3 秒與 5 秒的 RFS、跨情境類型的彙總結果排名。[RFS 說明](https://waymo.com/intl/zh-tw/open/challenges/2025/e2e-driving/)

入門時先使用官方評估函式，不要自行猜測公式。計算 RFS 需要有效的人工評分標註；報告時同時記錄可評估 frame 數與聚合方式，單一分片的簡單平均未必等同排行榜。

## 5. 第一個實驗：先不訓練模型

**目標：證明你正確理解資料和評估。**

環境操作另見 [Ubuntu 操作附錄](UBUNTU_SETUP.zh-TW.md)。完成安裝後，開啟 `notebooks/official_vision_based_e2e_driving.ipynb`，先取得一個 validation 分片並修改資料路徑。

以下是你應該完成的資料檢查：

1. 印出 frame ID、各相機名稱、各欄位長度與 intent。
2. 顯示前方相機影像，確認影像能解碼。
3. 畫出歷史 XY 與未來 XY，使用相同比例的座標軸。
4. 確認未來標註有 20 個點、時間方向正確且數值合理。
5. 檢查是否有有效 `preference_trajectories`；沒有就先做 logged-future ADE。

### 建立兩個最簡單的基準線

在 notebook 已經讀出 `data` 後執行：

```python
import numpy as np

t = np.arange(1, 21, dtype=np.float32) / 4.0
stop_prediction = np.zeros((20, 2), dtype=np.float32)

if not data.past_states.vel_x or not data.past_states.vel_y:
    raise ValueError('這筆資料缺少歷史速度，不能建立定速基準')
velocity = np.array([
    data.past_states.vel_x[-1],
    data.past_states.vel_y[-1],
], dtype=np.float32)
constant_velocity_prediction = t[:, None] * velocity[None, :]

target = np.stack([
    data.future_states.pos_x,
    data.future_states.pos_y,
], axis=-1)
assert target.shape == (20, 2), target.shape
assert np.isfinite(target).all()

for name, pred in [('stop', stop_prediction),
                   ('constant_velocity', constant_velocity_prediction)]:
    assert pred.shape == (20, 2) and np.isfinite(pred).all()
    ade = np.linalg.norm(pred - target, axis=-1).mean()
    print(f'{name}: logged-future ADE = {ade:.3f} m')
```

停車基準永遠輸出原點；定速基準假設當下速度在未來保持不變。它們沒有理解道路與影像，主要用途是抓出單位、座標、時間對齊與評估錯誤。

上面程式只評估單筆、完整的未來標註，尚未處理缺失時間點，也不計算官方排行榜 ADE。把它擴展到固定 validation 子集後，保存每筆結果，才有可比較的基準。

建議輸出一張圖：以 x 作橫軸、y 作縱軸，畫出標註、停車及定速三條軌跡，設定 `plt.axis('equal')`，並標示公尺。先確認哪個方向是前方，再解讀左轉／右轉。

## 6. 第二個實驗：建立最小可訓練模型

下面是建議的起步設計，不是官方指定架構，也尚未包含在目前專案程式中。

```text
多相機影像 → 共用影像 encoder → 各相機特徵串接 ─┐
歷史位置／速度／加速度 → MLP ──────────────────┼→ MLP → 40 個值 → (20, 2)
intent → one-hot 或 embedding ─────────────────┘
```

先固定相機順序、影像尺寸、歷史長度與缺失欄位策略。可先用當下影像加上提供的歷史狀態跑通，再增加多時刻影像。縮放影像後，若模型或投影使用相機內參，內參也需要同步調整。

第一版可用 Smooth L1 或 L1 作為 XY 回歸 loss，並另外回報 ADE。Loss 是訓練用的最佳化目標，不等於排行榜 RFS。

### 訓練順序

| 階段 | 做法 | 通過條件 |
| --- | --- | --- |
| 單一 batch | 重複訓練同一小批資料 | loss 明顯下降，軌跡接近標註 |
| 小型子集 | 固定 training 子集與 validation 子集 | 能完成 train/eval，沒有資料混用 |
| 比較基準 | 同一驗證集評估停車、定速與模型 | 能說明改善或退步出現在哪些情境 |
| 擴大實驗 | 增加資料、時序或模型容量 | 改善能重現，不只是更換驗證集造成 |

如果單一 batch 都無法擬合，先檢查梯度、資料正規化、輸出形狀與標註對齊，不要直接換更大的模型。

**資料洩漏是這個任務最需要避免的實作錯誤之一：**未來影像、`future_states`、人工候選軌跡及分數可以作為合適的監督或評估資訊，不能混入測試時不可取得的模型輸入。

## 7. 每次實驗應留下什麼？

建議以每次實驗一個資料夾管理：

```text
outputs/experiment_001/
├── config.json          # 輸入欄位、相機順序、影像尺寸、種子與超參數
├── split_manifest.json  # 實際使用的資料／frame 清單
├── metrics.json         # 指標定義、樣本數與結果
├── predictions.npz      # 可追溯到 frame ID 的預測
├── checkpoint/          # 模型權重
└── plots/               # 軌跡疊圖與失敗案例
```

這是建議目錄，尚未自動建立。也請記錄資料版本、程式版本及套件版本。比較兩個模型時，使用相同驗證資料與相同指標實作。

除平均值外，至少查看一些誤差最大的 frame、停車／移動案例、轉彎與障礙物案例。平均誤差降低不保證每種情境都改善。

## 8. 從模型輸出走到正式提交

流程為：

```text
官方指定的 test frame 清單
  → 模型逐筆推論
  → frame ID + 20 個 XY 點
  → FrameTrajectoryPredictions
  → E2EDChallengeSubmission
  → protobuf 檔案
  → tar.gz
```

每個 `FrameTrajectoryPredictions.frame_name` 必須對應原始 `frame.context.name`。提交 proto 還包含作者、帳號、方法與預訓練模型等資訊；`submission_type`、預訓練宣告與模型參數量等要求應依實際 schema／網站填寫。[提交 schema](https://raw.githubusercontent.com/waymo-research/waymo-open-dataset/master/src/waymo_open_dataset/protos/end_to_end_driving_submission.proto)

提交前檢查：

- 官方要求的 frame 全部涵蓋，沒有重複、漏掉或額外誤配的 ID。
- 每筆 x、y 各 20 個有限數值，沒有 NaN／Inf。
- 第一點是未來 0.25 秒，單位與車體座標一致。
- 已切換模型至推論模式，沒有使用未來標註。
- protobuf 可以重新讀回，封裝檔的內容正確。
- 方法資訊是真實設定，沒有保留 notebook 的範例作者與名稱。

官方 notebook 中的全零預測只是在示範序列化，不是已完成的模型。先在本地驗證，再依網站當時開放的流程提交；2025 規格可用於研究復現，但不代表目前仍開放該年度競賽。

## 9. 容易誤解的地方

| 誤解 | 正確理解 |
| --- | --- |
| 能顯示影像就完成 challenge | 這只是資料流程通過，還需要模型、評估與測試推論 |
| ADE 下降就一定排行榜更高 | 排名主要依 RFS，兩者反映的品質不同 |
| 20 個點包含現在的位置 | 不包含；從未來 0.25 秒開始 |
| 用 future states 當歷史輸入更準 | 這是資料洩漏，測試時不可用 |
| 把所有 frames 隨機切分就好 | 相鄰 frame 高度相關，應沿用官方切分 |
| 每筆都可以算 RFS | 只有具有效評分標註的資料可算 |
| 跑完 notebook 就有訓練模型 | 官方 notebook 主要示範資料、視覺化、提交及評估 |

## 10. 你現在應該從哪裡開始？

第一個里程碑是：**對同一筆 validation 資料，顯示相機畫面、標註軌跡、停車預測、定速預測，並算出兩個 logged-future ADE。**

接著依序完成：

1. 把單筆評估擴展到固定 validation 子集，保存基準結果。
2. 寫出 dataset loader，明確區分模型輸入與監督標註。
3. 建立最小模型，完成單 batch 擬合測試。
4. 進行小規模訓練，與相同資料上的基準線比較。
5. 在有效標註上加入官方 RFS，檢查失敗案例。
6. 最後才建立完整 test 推論與提交封裝流程。

目前這個資料夾已具備環境設定、環境 smoke test 及官方教學副本；上述基準批次評估、dataset loader 與訓練流程仍是下一階段要實作的內容。

### 參考入口

- [2025 挑戰規格與評估](https://waymo.com/intl/zh-tw/open/challenges/2025/e2e-driving/)
- [官方 E2E notebook](https://github.com/waymo-research/waymo-open-dataset/blob/master/tutorial/tutorial_vision_based_e2e_driving.ipynb)
- [官方資料下載入口](https://waymo.com/open/download/)
- [環境與 Jupyter 操作附錄](UBUNTU_SETUP.zh-TW.md)
