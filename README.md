# Proportional Bold → New Master (Glyphs 3 plugin)

Creates a **new master** from the current one in which every glyph is emboldened by
**its own stem width**:

    d_g = (ratio − 1) / 2 × w_g        (one-sided offset, font units)

`w_g` is measured per glyph with `layer.intersectionsBetweenPoints()` (30th percentile of ink-run
lengths on 24 horizontal + 24 vertical scan lines), the outline is offset with Glyphs' own
`GSOffsetCurve`, then `removeOverlap()` + `correctPathDirection()`. No bitmaps anywhere.

The plugin exposes exactly one number: the target ratio. Bold ≈ **1.45**, Black ≈ **1.75**
(median Bold/Regular stem ratio measured on Noto Sans CJK TC is 1.52; Black/Regular ≈ 1.8).

## Why per glyph

CJK Regular masters already carry a stroke hierarchy: in Noto Sans CJK TC the stem of 一 is
82 units, of 灣 46 units. `Filter > Offset Curve` adds the same constant to both, so dense glyphs
get relatively much bolder and their counters close ("糊成一片"). A proportional offset keeps the
hierarchy the designer drew.

## Measured on Noto Sans CJK TC (400 held-out ideographs, vector IoU vs the designer's weight)

| target | method | mean IoU | worst-decile IoU | glyphs with closed counters |
|---|---|---|---|---|
| Bold | Offset Curve, best single value (d=16) | 0.8535 | 0.820 | 31.5 % |
| Bold | **this plugin, ratio 1.45** | 0.8537 | 0.822 | **22.0 %** |
| Bold, dense glyphs only (stem 39–60) | single value / plugin | 0.8495 / 0.8528 | | 53 % / **36 %** |
| Black | Offset Curve, best single value (d=24) | 0.8221 | 0.787 | 40.3 % |
| Black | **this plugin, ratio 1.75** | 0.8246 | 0.789 | **37.8 %** |

Read this honestly: against a *well-chosen* single offset the mean IoU does not improve.
What improves is the failure mode designers complain about — closed counters in dense glyphs
(−30 % relative for Bold). The remaining ~15 % IoU error is the designer moving strokes apart
(re-spacing) and reshaping junctions, which this plugin does not attempt. The output is a
**draft master** to correct, not a finished weight.

Two internal constants were fitted on 40 key glyphs and are left in the code:
`BOX_GROWTH = 1.0` (a Canon-1993-style "shrink so the box stays fixed" step was tested and made
IoU worse on Noto) and plain proportionality (an exponent 2 on the stem, tested, no gain).

## Mac verification (not yet done)

`MAC_RUNBOOK.md` is the step-by-step for a fresh Mac: Glyphs 3 + Glyphs 4 side by side, plugin install,
headless checks of the three unknowns (`mac/headless_check.py` via `mac/glyphs_remote.py`), Font Book.

## Install

Copy `ProportionalBold.glyphsPlugin` to `~/Library/Application Support/Glyphs 3/Plugins/`, restart
Glyphs. Requires Glyphs 3 with Python installed via Plugin Manager > Modules. No other module needed.

## Use

Select the master you want to embolden (Font view or Edit view), then
`Filter > Proportional Bold → New Master…`, enter the ratio, `Create Master`.
A master named `<current> PropBold <ratio>` is appended; components are decomposed in the new
master; each new layer stores `userData["proportionalBold"] = {ratio, stem, offset}` so you can see
what was measured. Creating a master is not undoable — remove the master in Font Info if needed.

## Prior art (why this is a convenience, not an invention)

Per-glyph stroke-count-dependent line width: Sharp JP3481136B2 (1998, expired).
Complexity-dependent widths at render time: Otsuka JP2909273B2 (1991, expired).
Outline thickening with frame-size correction: Canon US5959634 (1993, expired).
None of these ever reached a font editor; this plugin only puts the expired rule into Glyphs.

## Plugin Manager listing (entry for `glyphs-packages/packages.plist`, `plugins` list)

```
{
  titles = { en = "Proportional Bold"; "zh-Hant" = "比例加粗"; };
  url = "https://github.com/fanzhixiang777/ProportionalBold";
  path = "ProportionalBold.glyphsPlugin";
  descriptions = {
    en = "Creates a new master emboldened per glyph in proportion to each glyph's measured stem (CJK-friendly alternative to a single Offset Curve value).";
    "zh-Hant" = "依每個字自己的筆畫粗細比例加粗，產生新母版；避免 Offset Curve 單一數值把密集字糊掉。";
  };
  screenshot = "https://raw.githubusercontent.com/fanzhixiang777/ProportionalBold/main/propbold_demo.png";
  minGlyphsVersion = "3.2";
},
```

Listing requirements (from the SDK README and the handbook): public Git repository, the bundle
at `path` inside it, a screenshot URL, an open-source license file in the repo, and a pull request
against `schriftgestalt/glyphs-packages` (branch `glyphs3`). Version updates are picked up from the
`UpdateFeedURL` in Info.plist (must serve the plist with `CFBundleVersion` and `productPageURL`).

## License

MIT
