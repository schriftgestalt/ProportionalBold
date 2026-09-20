# Plugin Manager submission (open the PR on GitHub's web editor)

Repository to edit: https://github.com/schriftgestalt/glyphs-packages — branch **glyphs3**, file **packages.plist**.
Insert this entry inside the `plugins = ( … );` list (keep the tab indentation the file uses):

```
			{
				titles = {
					en = "Proportional Bold";
					zh-Hant = "比例加粗";
					zh-Hans = "比例加粗";
					ja = "比例太字";
				};
				url = "https://github.com/fanzhixiang777/ProportionalBold";
				path = "ProportionalBold.glyphsPlugin";
				descriptions = {
					en = "*Filter > Proportional Bold → New Master…* adds a new master in which every glyph is emboldened in proportion to its own measured stem, using Glyphs' Offset Curve engine — a draft Bold/Black master for CJK fonts that keeps the stroke hierarchy of the Regular instead of one constant offset. One setting: the target ratio (Bold ≈ 1.45, Black ≈ 1.75). Verified on Glyphs 3.5 and 4.1. See [the readme](https://github.com/fanzhixiang777/ProportionalBold) for measured results.";
					zh-Hant = "*Filter > 比例加粗 → 新增母版…* 新增一個母版，每個字依自己量到的筆畫粗細按比例加粗（用 Glyphs 的 Offset Curve 引擎）——CJK 字型的 Bold/Black 母版草稿，保留 Regular 的筆畫層級，而不是一個常數外推到底。只有一個設定：目標比例（Bold ≈ 1.45、Black ≈ 1.75）。Glyphs 3.5 與 4.1 已驗證。實測數據見 [readme](https://github.com/fanzhixiang777/ProportionalBold)。";
					zh-Hans = "*Filter > 比例加粗 → 新建母版…* 新建一个母版，每个字按自己测得的笔画粗细等比加粗（使用 Glyphs 的 Offset Curve 引擎）——CJK 字体 Bold/Black 母版的草稿，保留 Regular 的笔画层级而不是一个常数外推到底。只有一个设置：目标比例（Bold ≈ 1.45、Black ≈ 1.75）。已在 Glyphs 3.5 与 4.1 验证。实测数据见 [readme](https://github.com/fanzhixiang777/ProportionalBold)。";
					ja = "*Filter > 比例太字 → 新規マスター…* は、各グリフをそれ自身の計測ステム幅に比例して太らせた新しいマスターを追加します（Glyphs の Offset Curve エンジンを使用）。定数オフセットではなく Regular のストローク階層を保つ、CJK フォント向け Bold/Black マスターの下書きです。設定はひとつ、目標比率のみ（Bold ≈ 1.45、Black ≈ 1.75）。Glyphs 3.5 と 4.1 で検証済み。計測結果は [readme](https://github.com/fanzhixiang777/ProportionalBold) を参照。";
				};
				minVersion = 3200;
				screenshot = "https://raw.githubusercontent.com/fanzhixiang777/ProportionalBold/main/docs/before-after.png";
			},
```

PR title:

    Add Proportional Bold (CJK per-glyph emboldening, new master)

PR body:

    Adds the Proportional Bold plugin (MIT), repository https://github.com/fanzhixiang777/ProportionalBold.

    What it does: Filter > Proportional Bold → New Master… appends a master in which every glyph is offset by
    (ratio − 1)/2 × its own scan-line-measured stem, with Glyphs' own Offset Curve, so dense CJK glyphs are not
    over-inked by a single constant. One setting (the ratio). Draft master, not a finished weight — the readme states
    the measured effect against a designer-drawn Bold (Noto Sans CJK TC): same IoU as one Offset Curve value,
    23.9 % vs 28.6 % of CJK glyphs with a closed counter.

    Verified on Glyphs 3.5 (3532) and Glyphs 4.1 (4107) on GitHub Actions macOS runners (headless via glyphs-cli and
    in the GUI); logs are in the repository under mac/results/. Requires only the Python module from Plugin Manager.
    Bundle is plain Python (3.11 and 3.14), General Plugin, minVersion 3200.
