# Proportional Bold → New Master（比例加粗 → 新增母版）

Glyphs 3 與 Glyphs 4 的外掛。你只給一個數字——目標筆畫比例——它就在字型裡新增一個**母版**，每個字依「自己的筆畫粗細」按比例加粗。得到的是 Bold 或 Black 母版的**草稿**，不是完成的字重。

![Regular、單一 Offset Curve、比例加粗、設計師手繪 Bold — 八個密集字](docs/before-after.png)

四行分別是：Regular 母版；Filter > Offset Curve 對整套字型用同一個值；本外掛 ratio 1.45（實際輸出）；思源黑體 TC 設計師手繪的 Bold，供對照。

## 為什麼

`Filter > Offset Curve` 對每個字加同樣的量。CJK 的 Regular 母版本來就有筆畫層級——在思源黑體 TC 裡，一 的筆畫 82 units，灣 只有 46——同一個常數會讓密集字相對粗得多、把 counter 糊死。本外掛用掃描線量每個字的筆畫粗細，用 Glyphs 自己的 Offset Curve 引擎外推 `(ratio − 1) / 2 × 該字筆寬`。這條規則很舊（Sharp 1998、Canon 1993 的專利，皆已失效）；外掛只是把它放進字型編輯器。

## 值多少，用數據講

實際外掛輸出，思源黑體 TC Regular → ratio 1.45，與設計師手繪的 Bold 比較（[run 35503951963](mac/results/35503951963/)）：

| | 本外掛 | 單一 Offset Curve 值 |
|---|---|---|
| 與設計師 Bold 的 IoU，412 字 | 0.831 | 0.829 |
| counter 被封死（比設計師少）的字，412 字 | 18.4 % | 22.1 % |
| 同上，318 個 CJK 漢字 | 23.9 % | 28.6 % |

也就是：整體吻合度與單一外推值相同，密集字 counter 糊掉的比例少了大約六分之一。沒有比這更強的說法。設計師仍然要重畫交叉處、重新分配筆畫間距、逐字修密集字；這個外掛省的是第一遍。

## 安裝

- Plugin Manager：上架之後從 *Window > Plugin Manager* 安裝。
- 手動：把 `ProportionalBold.glyphsPlugin` 複製到 `~/Library/Application Support/Glyphs 3/Plugins/`（或 `Glyphs 4/Plugins/`），重新啟動 Glyphs。
- 需要 *Window > Plugin Manager > Modules* 裡的 Python 模組：Glyphs 3 用它的 Python 3.11 模組，Glyphs 4 用它的 Python 3.14 模組（見下方驗證）。不需要其他模組。

## 使用

選好要加粗的母版，*Filter > 比例加粗 → 新增母版…*，輸入比例（Bold ≈ 1.45、Black ≈ 1.75，思源黑體實測），按 *Create Master*。會新增一個名為 `<目前母版> PropBold <ratio>` 的母版；其中的組件已拆解；每個新圖層的 `userData["proportionalBold"]` 記錄量到的筆寬與外推量。量不到筆畫的字（點、極小符號）用全字型的中位筆寬，並列在報告裡。新增母版不能復原——反悔就到 Font Info 刪掉它。

## 驗證環境

Glyphs 3.5（build 3532）與 Glyphs 4.1（build 4107），GitHub Actions 的 macOS runner，無頭與 GUI 都跑：外掛載入、選單項目出現、415 個測試字中 413 個加粗、1 個 fallback、0 個失敗，兩個版本輸出完全相同，與命令列工具的 IoU 0.994。紀錄與數字：[mac/results/](mac/results/)。

## 已知限制

- 掃描線找到的墨段不足六段的字（點、極小符號）用中位筆寬，不是自己的。
- 尖銳的斜筆尖端（撇、捺）比命令列工具的短，因為兩邊的外推引擎不同；面積差異 1 % 以內。
- 密集字仍然要手工修；交叉處沒有處理。
- 65,535 字在 3 核心的 runner 上約 13–17 分鐘。

## 命令列

`propbold`（0.2.0）在 Glyphs 之外套用同一條規則，Windows、macOS、Linux 皆可：`.glyphs` 進 → 同一個檔加一個母版、`.ufo` → 新 UFO、`.otf`/`.ttf` → 新的 TrueType 字型。`propbold-compare` 把外掛做的母版與命令列輸出對照。

    pip install "git+https://github.com/fanzhixiang777/ProportionalBold.git#subdirectory=propbold-cli"
    propbold NotoSansCJKtc-Regular.otf --ratio 1.45

TTF 輸出在 Windows 11 安裝已用 0.1.2 驗證；0.2.0 的重新驗證待辦（[propbold-cli/WINDOWS_CHECK.md](propbold-cli/WINDOWS_CHECK.md)）。細節：[propbold-cli/README.md](propbold-cli/README.md)。

## 代工服務

不想自己跑也可以：把 Regular 母版寄來，我用這套工具做出 Bold 或 Black 的草稿母版，並依上面的數據逐字檢查後交回。每一套字重 NT$20,000。先免費做 50 個字的樣本，你親眼看過再決定要不要付費。來信 proportionalbold@gmail.com。

If you would rather not run it yourself: send a Regular master and I return the Bold or Black draft master prepared with this tool, checked glyph by glyph against the numbers above. NT$20,000 per weight set. A 50-glyph sample comes first, free, so you can judge it by eye before paying. Write to proportionalbold@gmail.com.

ご自身で実行されない場合はこちらへ。Regular マスターをお送りいただければ、このツールで Bold または Black の下書きマスターを作成し、上記の数値に照らして一字ずつ確認してお返しします。ウェイト一式につき NT$20,000 です。まず 50 字のサンプルを無料でお作りしますので、目でご確認のうえご判断ください。連絡先は proportionalbold@gmail.com。

## 授權

MIT。測試資料：思源黑體（SIL Open Font License）。
