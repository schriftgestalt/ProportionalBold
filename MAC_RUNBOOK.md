# MAC_RUNBOOK.md — one rented Mac, one day: verify ProportionalBold in Glyphs 3 and Glyphs 4

Audience: **Claude Code running on this Mac**, executing top to bottom. Steps marked **HUMAN** need a
click that Claude Code cannot do; everything else is a shell command with an expected result.
Do not skip a check because it "should" work — the whole point of the day is the four things nobody
has run on a Mac yet. Record every result in `MAC_RESULTS.md`, put raw output in `mac/log/`, commit.

Stop rule: if a step fails, capture the full output to `mac/log/`, try the fix listed under that step,
and if that fails too, write the failure into `MAC_RESULTS.md` and continue with the next section.
Never edit `propbold-cli/`; only `ProportionalBold.glyphsPlugin/Contents/Resources/plugin.py` and the
files under `mac/` may change today. Every `plugin.py` change must be followed by
`cd propbold-cli && python3 -m pytest -q tests` (the parity tests read plugin.py).

---

## A. Before Claude Code exists (HUMAN, ~15 min)

1. macOS 13 or newer, Apple Silicon preferred. Sign in to iCloud is NOT needed.
2. Terminal → `xcode-select --install` → click *Install* in the dialog → wait until `git --version` works.
3. Install Claude Code (official native installer, per docs.claude.com/en/docs/claude-code/setup):
   ```
   curl -fsSL https://claude.ai/install.sh | bash
   exec zsh
   claude doctor
   ```
   `claude doctor` must report a healthy install. Then `claude` once to sign in (browser).
4. Clone the repo where every script expects it:
   ```
   git clone https://github.com/fanzhixiang777/ProportionalBold.git ~/ProportionalBold
   cd ~/ProportionalBold && git checkout -b mac-verification
   ```
5. Start Claude Code in the repo and give it this first task:
   `Read MAC_RUNBOOK.md and execute it from section B. Ask me only for the HUMAN steps.`

---

## B. Machine setup (Claude Code)

```
cd ~/ProportionalBold
sw_vers; uname -m                                   # record in MAC_RESULTS.md
mkdir -p mac/log
```

Python for the CLI tests and for the remote runner (system `python3` from the CLT has no PyObjC):
```
python3 -m venv ~/pb-venv
~/pb-venv/bin/pip install -q --upgrade pip
~/pb-venv/bin/pip install -q -e ./propbold-cli pytest pyobjc-framework-Cocoa opentype-sanitizer
cd propbold-cli && ~/pb-venv/bin/python -m pytest -q tests && cd ..
```
Expected: `12 passed, 1 skipped`. If `skia-pathops` has no wheel for this Python, install
`brew install python@3.12` and rebuild the venv with `/opt/homebrew/bin/python3.12`.

---

## C. Install Glyphs 3 and Glyphs 4 side by side

Direct downloads (verified 2026-09-19; both are zips containing the .app; 30-day trials, no license needed):
```
cd ~/Downloads
curl -L -o Glyphs3.zip https://updates.glyphsapp.com/latest3.php     # Glyphs3.5-3532.zip, ~35 MB
curl -L -o Glyphs4.zip https://updates.glyphsapp.com/latest4.php     # Glyphs4.1-4107.zip, ~38 MB
ditto -xk Glyphs3.zip /Applications && ditto -xk Glyphs4.zip /Applications
xattr -dr com.apple.quarantine "/Applications/Glyphs 3.app" "/Applications/Glyphs 4.app"
ls /Applications | grep Glyphs
defaults read "/Applications/Glyphs 3.app/Contents/Info.plist" CFBundleVersion
defaults read "/Applications/Glyphs 4.app/Contents/Info.plist" CFBundleVersion
```
Expected: two apps, `Glyphs 3.app` and `Glyphs 4.app` (different names, they coexist), build numbers
printed (3532 / 4107 or newer). Record them.

First launch of each — **HUMAN**: `open -a "Glyphs 3"`, choose *Try* / continue the trial, close the
start window; same for `open -a "Glyphs 4"`. Quit both afterwards (`osascript -e 'quit app "Glyphs 3"'`).

---

## D. Python inside each Glyphs (Plugin Manager > Modules)

Each app needs its own Python module: Glyphs 3 uses **Python 3.11**, Glyphs 4 needs **Python 3.14+**
(source: forum post "Updating Python scripts and plug-ins for Glyphs 4", 2026-07-26).

**HUMAN**, for Glyphs 3 and then for Glyphs 4:
1. `Window > Plugin Manager` → tab **Modules** → **Python** → *Install*.
2. `Glyphs > Settings…` (Cmd-,) → **Addons** → *Python version* → pick the entry labelled **(Glyphs)**.
3. Quit and relaunch the app.

Verify from Terminal (Glyphs running):
```
cd ~/ProportionalBold
cat > mac/pyversion.py <<'EOF2'
import sys; print("PYVERSION", sys.version.split()[0])
EOF2
~/pb-venv/bin/python mac/glyphs_remote.py 3 mac/pyversion.py    # expected: connected … PYVERSION 3.11.x
```
For Glyphs 4 the remote port name is unverified. Find it once — **HUMAN** runs this in Glyphs 4's
Macro panel (`Window > Macro Panel`, Cmd-Opt-M, paste, Run):
```
from Foundation import NSBundle; print(NSBundle.mainBundle().bundleIdentifier())
```
Put the printed identifier first in `PORTS["4"]` in `mac/glyphs_remote.py`, then:
```
~/pb-venv/bin/python mac/glyphs_remote.py 4 mac/pyversion.py    # expected: PYVERSION 3.14.x
```
If no NSConnection can be made to either app, everything below still works by pasting the script
files into the Macro panel by hand (HUMAN); note that in MAC_RESULTS.md.

---

## E. Install the plugin bundle

Same bundle for both versions (the `Contents/MacOS/plugin` loader is byte-identical in the SDK's
Glyphs3 and Glyphs4 templates; the code is plain Python 3.11/3.14):
```
cd ~/ProportionalBold
for v in 3 4; do
  d="$HOME/Library/Application Support/Glyphs $v/Plugins"
  mkdir -p "$d"; rm -rf "$d/ProportionalBold.glyphsPlugin"
  cp -R ProportionalBold.glyphsPlugin "$d/"
  xattr -dr com.apple.quarantine "$d/ProportionalBold.glyphsPlugin"
done
```

### Where plugin load errors appear (three places, use all three)
1. **Launch log** (most reliable, captures Python tracebacks that never reach the UI):
   ```
   osascript -e 'quit app "Glyphs 3"'; sleep 2
   "/Applications/Glyphs 3.app/Contents/MacOS/Glyphs 3" > mac/log/glyphs3-launch.log 2>&1 &
   sleep 25; grep -n -i -E "proportional|traceback|error" mac/log/glyphs3-launch.log | head
   ```
   Expected: no line mentioning ProportionalBold. Same for Glyphs 4 (`glyphs4-launch.log`).
2. **Macro panel** (`Window > Macro Panel`, Cmd-Opt-M): failed plugin imports are printed there at
   startup; scroll to the top. Script `print()` output also lands here.
3. **Console.app**: select the Mac in the sidebar, search field `process:Glyphs 3` (or `Glyphs 4`),
   then filter for `Traceback` or `plugin`. From Terminal:
   `log show --last 10m --predicate 'process CONTAINS "Glyphs"' --style compact | grep -i -E "plugin|traceback"`.
   To route plugin `print()` output to Console.app instead of the Macro panel:
   `Settings > Addons > Use system console for script output`.
   Crash reports: `ls ~/Library/Logs/DiagnosticReports/ | grep Glyphs`.

Menu check without clicking: the headless script's CHECK 0 lists the Filter menu. By eye (HUMAN):
`Filter` menu shows "Proportional Bold → New Master…".

---

## F. Headless verification — the three unknowns as checks

`mac/headless_check.py` runs inside Glyphs, opens `testdata/NotoSansCJKtc-Regular-sub415.otf`
(415-glyph subset of Noto Sans CJK TC Regular) without a window, calls the plugin's
`emboldenFont(font, 1.45)` — no menu, no dialog — and compares against `testdata/expected_sub415.json`,
which the CLI produced for the same glyphs. It writes `mac/results-<build>.json`.

```
cd ~/ProportionalBold
~/pb-venv/bin/python mac/glyphs_remote.py 3 mac/headless_check.py | tee mac/log/check-glyphs3.log
```
Fallback (no remote connection): HUMAN pastes the file into the Macro panel and runs it; copy the
panel output into `mac/log/check-glyphs3.log`.

Expected output, and what each line settles:

| line | expected | this is unknown # | if it fails |
|---|---|---|---|
| `PASS 0.plugin_loaded  class found; menu item present` | plugin loaded by Glyphs itself, not by the fallback | — | read section E logs; fix plugin.py; reinstall; relaunch |
| `PASS 1.no_failures  done 4xx skipped x failed 0` | every glyph offset without exception | **U1** `GlyphsFilterOffsetCurve` 12-arg call works in this build | traceback is printed per glyph; the signature is declared in the SDK stubs of both versions, so a failure means the stub lies — try `NSClassFromString("GSOffsetCurve")` with the 13-arg `..._join_keepCompatibleOutlines_` signature (`join` = 0) and record which one worked |
| `PASS 1.median_stem  65.x vs expected 65.0` | measurement identical to the CLI (±2 units) | — | `intersectionsBetweenPoints` returned something unexpected: print `layer.intersectionsBetweenPoints((-10,400),(1010,400), components=True)` for glyph uni4E00 and compare with the 4 points the CLI would compute |
| `PASS 1.bounds_match_cli  tolerance 3 units` | Glyphs' Offset Curve grows each glyph like pathops' stroke∪fill | **U1** same engine result | a consistent offset of a few units means Glyphs positions the offset differently (e.g. `position` 0.5 vs 1); record the numbers, then try `position=1.0` and `makeStroke=False` unchanged — do not chase below 3 units |
| `PASS 1.corners_not_rounded  on-curve nodes … unchanged within 30%` | 一 keeps ~4 corner nodes; no curve segments added at convex corners | **U1** join style: does Glyphs' 12-arg call use miter (square corners, like the CLI)? | if node counts roughly double, corners are rounded → use the 13-arg call with an explicit `join` and record which value gives square corners; if none does, document "Glyphs output has rounded corners; CLI has square" as a known engine difference |
| `PASS 2.master_added  masters 1 -> 2, ids distinct True` | `master.copy()` + new id accepted by `font.masters.append` | **U2** | if the id collides or the append silently makes a second layer set, replace `src.copy()` with `GSFontMaster()` and copy `name/ascender/capHeight/xHeight/descender/italicAngle/metrics/customParameters` by hand |
| `PASS 2.layers_have_paths  new-master layers without paths: 0` | `glyph.layers[newId] = layer` attached the offset outlines | **U2** | if 0 paths: the layer was assigned before `layerId` was set, or `copyDecomposedLayer()` returned a detached layer whose `parent` is nil — set `newLayer.parent = glyph` before assignment |
| `PASS 2.save_reopen  saved ~/Desktop/propbold-check-3.x.glyphs; masters 2` | the file round-trips with both masters | **U2** | open the saved file in Glyphs by hand and look at Font Info > Masters; if the new master is missing, the id was not stored — check the `.glyphs` text for the id |
| `PASS 3.timing  … ms/glyph -> ~N min for 65,535 (limit 30)` | ≤ 30 min extrapolated (Linux CLI: 429 s for 65,535; Windows: 311 s) | **U3** | if > 30 min, the two `removeOverlap()` calls per glyph are the suspects: time them separately (`time.time()` around each in `emboldenLayer`) and record; do not optimise today |

Then Glyphs 4, same command with `4`, log to `mac/log/check-glyphs4.log`. Expected: identical PASS
set, `python` field `3.14.x`, no deprecation output in the Macro panel. If Glyphs 4 fails where 3
passes, the difference is the Glyphs 4 API; consult
https://forum.glyphsapp.com/t/updating-python-scripts-and-plug-ins-for-glyphs-4/36793 before
changing anything, and keep the fix version-guarded with `Glyphs.versionNumber >= 4`.

### Optional (if the day has hours left): the real 65,535-glyph run in Glyphs 3
```
curl -L -o ~/Downloads/NotoSansCJKtc-Regular.otf \
  https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf
cat > mac/full_run.py <<'EOF2'
import time, objc
from GlyphsApp import Glyphs
t=time.time(); font=Glyphs.open("/Users/%s/Downloads/NotoSansCJKtc-Regular.otf" % __import__("os").getlogin(), showInterface=False)
print("IMPORT %.0fs, %d glyphs" % (time.time()-t, len(font.glyphs)))
p=objc.lookUpClass("ProportionalBold").alloc().init()
r=p.emboldenFont(font, 1.45, log=print); print("RUN", r)
font.save("/Users/%s/Desktop/noto-propbold145.glyphs" % __import__("os").getlogin()); font.close()
EOF2
~/pb-venv/bin/python mac/glyphs_remote.py 3 mac/full_run.py | tee mac/log/full-glyphs3.log
```
Expected: import takes minutes on its own (record), run ≤ 30 min, `failed 0`. Watch memory in
Activity Monitor; record peak. This is the only way to close U3 for real.

---

## G. Font Book validation of the Windows-verified TTF

Get the file: copy `A-65535-full.ttf` (24.5 MB, the exact file that installed on Windows 11) into
`~/ProportionalBold/mac/`, or regenerate the identical thing (~7 min):
```
~/pb-venv/bin/propbold ~/Downloads/NotoSansCJKtc-Regular.otf --ratio 1.45
mv ~/Downloads/NotoSansCJKtc-Regular-propbold145.ttf mac/A-65535-full.ttf
~/pb-venv/bin/python -m ots mac/A-65535-full.ttf        # expected: File sanitized successfully!
```

1. **HUMAN**: `open -a "Font Book" mac/A-65535-full.ttf` → the preview window shows CJK sample text →
   *Install*. Then `Font Book > File > Validate File…` (or *Validate Font* on the installed font).
   Expected: green "passed" / no red errors; yellow warnings are recorded verbatim, not fixed today.
2. System view (no clicking):
   ```
   system_profiler SPFontsDataType 2>/dev/null | grep -B3 -A14 "PropBold145" | tee mac/log/fontbook.log
   ```
   Expected block contains `Valid: Yes`, `Enabled: Yes`, `Family: Noto Sans CJK TC PropBold145`,
   `Style: Regular`.
3. Render check (machine-readable, CoreText via PyObjC, no app needed):
   ```
   cat > mac/render_check.py <<'EOF2'
   from AppKit import (NSFont, NSImage, NSBitmapImageRep, NSColor, NSColorSpace, NSAttributedString,
                       NSFontAttributeName, NSForegroundColorAttributeName, NSBitmapImageFileTypePNG, NSRectFill)
   from Foundation import NSMakeRect, NSMakePoint
   f = NSFont.fontWithName_size_("NotoSansCJKTCPropBold145-Regular", 72)
   assert f is not None, "font not found by PostScript name: not installed, or name table wrong"
   img = NSImage.alloc().initWithSize_((900, 120)); img.lockFocus()
   NSColor.whiteColor().set(); NSRectFill(NSMakeRect(0, 0, 900, 120))
   s = NSAttributedString.alloc().initWithString_attributes_("臺灣鬱鑿籲龜體", {NSFontAttributeName: f, NSForegroundColorAttributeName: NSColor.blackColor()})
   s.drawAtPoint_(NSMakePoint(10, 20)); img.unlockFocus()
   rep = NSBitmapImageRep.imageRepWithData_(img.TIFFRepresentation())
   W, H = rep.pixelsWide(), rep.pixelsHigh()
   srgb = NSColorSpace.sRGBColorSpace()
   dark = sum(1 for x in range(0, W, 4) for y in range(0, H, 4)
              if rep.colorAtX_y_(x, y).colorUsingColorSpace_(srgb).redComponent() < 0.5)
   rep.representationUsingType_properties_(NSBitmapImageFileTypePNG, None).writeToFile_atomically_("mac/log/render.png", True)
   print("RENDER dark samples:", dark, "of", (W // 4) * (H // 4))
   assert dark > 300, "glyphs did not render"
   EOF2
   ~/pb-venv/bin/python mac/render_check.py
   ```
   Expected: `RENDER dark samples: <several thousand>` and `mac/log/render.png` shows the seven bold
   characters. If the font is found but nothing renders, the glyf/loca data is not what CoreText
   expects — record and stop; that would contradict the Windows result and needs a second look.

---

## H. Wrap up

```
cd ~/ProportionalBold
git add MAC_RESULTS.md mac/ ProportionalBold.glyphsPlugin/Contents/Resources/plugin.py
git commit -m "Mac verification: Glyphs 3 build ____, Glyphs 4 build ____, Font Book"
git push -u origin mac-verification
```
`MAC_RESULTS.md` must contain every number the checks printed, the two build numbers, the two Python
versions, and the verbatim text of any FAIL. Leave the trial apps installed; the Mac is rented.
