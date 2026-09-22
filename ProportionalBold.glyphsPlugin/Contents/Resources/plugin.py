# encoding: utf-8
###########################################################################################################
#
#   Proportional Bold → New Master   (Glyphs 3 and Glyphs 4 General Plugin)
#
#   Takes the currently selected master and creates a NEW master in which every glyph is
#   emboldened by its OWN stem width:   d_g = (ratio - 1) / 2 * w_g
#   (w_g measured on the glyph with layer.intersectionsBetweenPoints, outlines offset with
#   Glyphs' own Offset Curve filter, GlyphsFilterOffsetCurve — all vector, no bitmaps).
#
#   Why: Filter > Offset Curve uses ONE number for the whole font, while a CJK Regular master already
#   encodes a stroke hierarchy (simple glyphs have thicker stems than dense ones); a constant offset
#   over-inks dense glyphs and closes their counters. A per-glyph offset proportional to the measured
#   stem keeps the hierarchy the designer already drew.
#
#   Measured effect, test setup and every figure: README.md, where each number names the run it comes
#   from. These comments deliberately state no figures, so they cannot go stale.
#   This plugin makes a DRAFT master for the designer to correct; it does not replace drawing.
#
###########################################################################################################

import objc
import traceback
import uuid

from GlyphsApp import Glyphs, EDIT_MENU
from GlyphsApp.plugins import GeneralPlugin
from AppKit import (
	NSMenuItem,
	NSAlert,
	NSTextField,
	NSView,
	NSMakeRect,
	NSClassFromString,
	NSAlertFirstButtonReturn,
	NSFont
)

DEFAULT_RATIO = 1.45        # suggested setting for Bold; suggested settings and measured designer ratios: README.md
PCT = 30                    # percentile of scan-line ink runs used as the glyph's stem width
N_LINES = 24                # scan lines per direction
MAX_RUN_FRAC = 0.35         # ignore ink runs longer than this fraction of the bbox (junctions, along-stroke runs)
D_CAP = 0.6                 # never offset more than 0.6 × stem (safety for tiny/odd glyphs)
BOX_GROWTH = 1.0            # 1.0 = plain offset, the value every verified run used. <1.0 shrinks the skeleton
                            # so the bbox grows only BOX_GROWTH × 2d (Canon US5959634 style); never verified.
# Unmeasurable glyphs (tiny dots, marks: fewer than 6 ink runs) get the font's median measured stem
# as a FALLBACK stem, counted separately as "fallback" — never as done, never as an offset of 0.


class NoStem(ValueError):
	"""The scan lines found fewer than 6 ink runs — a dot, a tiny mark, an empty-looking glyph."""


class ProportionalBold(GeneralPlugin):

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'Proportional Bold → New Master…',
			'zh-Hant': '比例加粗 → 新增母版…',
			'zh': '比例加粗 → 新建母版…',
			'ja': '比例太字 → 新規マスター…',
		})

	@objc.python_method
	def start(self):
		newMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.name, self.run_, "")
		newMenuItem.setTarget_(self)
		Glyphs.menu[EDIT_MENU].append(newMenuItem)

	# ------------------------------------------------------------------ UI: one number
	@objc.python_method
	def askRatio(self):
		alert = NSAlert.alloc().init()
		alert.setMessageText_("Proportional Bold → New Master")
		alert.setInformativeText_(
			"Target stem ratio (new stem / current stem), applied per glyph.\n"
			"suggested: Bold ≈ 1.45, Black ≈ 1.75\n"
			"A new master is added; the current master is not changed.")
		alert.addButtonWithTitle_("Create Master")
		alert.addButtonWithTitle_("Cancel")
		field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 120, 24))
		field.setStringValue_("%.2f" % DEFAULT_RATIO)
		field.setFont_(NSFont.systemFontOfSize_(13))
		view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 120, 24))
		view.addSubview_(field)
		alert.setAccessoryView_(view)
		alert.window().setInitialFirstResponder_(field)
		if alert.runModal() != NSAlertFirstButtonReturn:
			return None
		try:
			ratio = float(field.stringValue().replace(",", "."))
		except ValueError:
			return None
		if not (1.0 < ratio < 3.0):
			Glyphs.showNotification("Proportional Bold", "Ratio must be between 1.0 and 3.0.")
			return None
		return ratio

	# ------------------------------------------------------------------ measurement (vector)
	@objc.python_method
	def _cleanRuns(self, pts, axis, p1, p2):
		"""pts: NSPoints returned by intersectionsBetweenPoints. Drop the measurement-line end points,
		sort along the line, pair even-odd → ink run lengths."""
		vals = []
		for p in pts:
			v = p.x if axis == 0 else p.y
			# drop the two end points of the measurement line itself
			if (abs(p.x - p1[0]) < 1e-6 and abs(p.y - p1[1]) < 1e-6) or (abs(p.x - p2[0]) < 1e-6 and abs(p.y - p2[1]) < 1e-6):
				continue
			vals.append(v)
		vals.sort()
		n = len(vals) - (len(vals) % 2)
		return [vals[i + 1] - vals[i] for i in range(0, n, 2)]

	@objc.python_method
	def stemWidth(self, layer):
		"""Per-glyph stem width in font units: PCT-th percentile of ink-run lengths on N_LINES
		horizontal and N_LINES vertical scan lines (runs longer than MAX_RUN_FRAC × bbox ignored).
		Requires an overlap-free layer (call removeOverlap first)."""
		b = layer.bounds
		x0, y0, W, H = b.origin.x, b.origin.y, b.size.width, b.size.height
		if W < 1 or H < 1:
			return None
		runs = []
		layer = layer.copyDecomposedLayer()
		layer.flattenOutlinesRemoveOverlap_origHints_secondaryPath_extraHandles_error_(False, None, None, None, None)
		for i in range(N_LINES):
			f = 0.06 + 0.88 * i / (N_LINES - 1)
			y = y0 + f * H
			p1, p2 = (x0 - 10.0, y), (x0 + W + 10.0, y)
			runs += self._cleanRuns(layer.intersectionsBetweenPoints(p1, p2), 0, p1, p2)
			x = x0 + f * W
			p1, p2 = (x, y0 - 10.0), (x, y0 + H + 10.0)
			runs += self._cleanRuns(layer.intersectionsBetweenPoints(p1, p2), 1, p1, p2)
		limit = MAX_RUN_FRAC * max(W, H)
		runs = sorted(r for r in runs if 0 < r < limit)
		if len(runs) < 6:
			return None
		return runs[min(len(runs) - 1, int(len(runs) * PCT / 100.0))]

	# ------------------------------------------------------------------ offset (Glyphs' own)
	@objc.python_method
	def offsetLayer(self, layer, d):
		"""Offset all outlines outward by d with Glyphs' own Offset Curve engine.
		Uses the 12-argument class method that is declared identically in the Glyphs 3 and
		Glyphs 4 SDK stubs (GlyphsApp/plugins.pyi). No try/except fallback on purpose: a
		failure must surface as its own traceback, not be masked by a second call."""
		cls = NSClassFromString("GlyphsFilterOffsetCurve")
		if cls is None:
			raise RuntimeError("GlyphsFilterOffsetCurve not found in this Glyphs version")
		cls.offsetLayer_offsetX_offsetY_makeStroke_autoStroke_position_metrics_error_shadow_capStyleStart_capStyleEnd_keepCompatibleOutlines_(
			layer, d, d,     # offsetX, offsetY
			False,           # makeStroke
			False,           # autoStroke
			0.5,             # position
			None,            # metrics
			None,            # error
			None,            # shadow layer
			0, 0,            # cap styles
			False)           # keepCompatibleOutlines

	# ------------------------------------------------------------------ per-glyph
	@objc.python_method
	def emboldenLayer(self, srcLayer, ratio, newMasterId=None, fallbackStem=None):
		"""Returns (newLayer, info). newLayer is a decomposed, overlap-free copy offset by d_g.
		info["fallback"] is True when the glyph could not be measured and fallbackStem was used.

		The copy is ATTACHED to the glyph before anything is measured: a detached layer (the result of
		copy()/copyDecomposedLayer()) reports bounds 0,0,0,0 in Glyphs 3.5, so scan lines placed from
		its bounds hit nothing and the stem came back None (found with mac/diag_stem.py, 2026-09-20).
		With newMasterId the copy is attached as that master's layer (where it will live anyway);
		without it, it is attached temporarily and removed again.
		A stem measurement that yields None raises NoStem (a ValueError) unless fallbackStem is given,
		so the caller counts the glyph as failed or fallback instead of silently writing an un-emboldened copy."""
		glyph = srcLayer.parent
		work = srcLayer.copyDecomposedLayer()
		work.removeOverlap()
		temporary = False
		if newMasterId:
			work.layerId = newMasterId
			work.associatedMasterId = newMasterId
			glyph.layers[newMasterId] = work
			work = glyph.layers[newMasterId]
		else:
			glyph.layers.append(work)
			temporary = True
		try:
			w = self.stemWidth(work)
			fallback = False
			if w is None:
				if not fallbackStem:
					b = work.bounds
					raise NoStem(
						"stem measurement returned nothing (bounds %.0f,%.0f %.0fx%.0f, %d paths)"
						% (b.origin.x, b.origin.y, b.size.width, b.size.height, len(work.paths))
					)
				w = float(fallbackStem)
				fallback = True
			d = (ratio - 1.0) / 2.0 * w
			d = max(0.0, min(d, D_CAP * w))
			if BOX_GROWTH < 1.0:
				b = work.bounds
				W, H = b.size.width, b.size.height
				dW = BOX_GROWTH * 2.0 * d
				sx = max(0.85, min(1.1, (W + dW - 2 * d) / W)) if W > 0 else 1.0
				sy = max(0.85, min(1.1, (H + dW - 2 * d) / H)) if H > 0 else 1.0
				cx, cy = b.origin.x + W / 2.0, b.origin.y + H / 2.0
				work.applyTransform([sx, 0.0, 0.0, sy, cx * (1 - sx), cy * (1 - sy)])
			self.offsetLayer(work, d)
			work.removeOverlap()
			work.correctPathDirection()
			work.width = srcLayer.width
			return work, {"w": w, "d": d, "fallback": fallback}
		finally:
			if temporary:
				try:
					glyph.layers.remove(work)
				except Exception:
					pass

	# ------------------------------------------------------------------ whole font (no UI) — also the headless entry point
	@objc.python_method
	def emboldenFont(self, font, ratio, master=None, glyphLimit=None, log=print):
		"""Create a new master from `master` (default: the selected one) with every glyph emboldened.
		No dialogs, no notifications: mac/headless_check.py calls this from the Macro panel or remotely.
		Returns a dict: master, masterId, done, skipped, failed, failures, medianStem, medianStemOut, seconds."""
		import time
		t0 = time.time()
		src = master
		if src is None:
			try:
				src = font.selectedFontMaster      # None when the font has no window (headless)
			except Exception:
				src = None
		if src is None:
			src = font.masters[0]
		newMaster = src.copy()
		newMaster.id = str(uuid.uuid4()).upper()
		newMaster.name = "%s PropBold %.2f" % (src.name, ratio)
		try:
			if len(font.axes) and font.axes[0].axisTag == "wght" and src.axes[0] and src.axes[0] > 0:
				newMaster.axes[0] = round(src.axes[0] * ratio)
		except Exception:
			pass
		font.disableUpdateInterface()
		font.masters.append(newMaster)
		newId = newMaster.id
		done, skipped, failed, failures, stems = 0, 0, 0, [], []
		deferred = []                      # (glyph, srcLayer) with no measurable stem: get the median afterwards
		try:
			for i, glyph in enumerate(font.glyphs):
				if glyphLimit and i >= glyphLimit:
					break
				srcLayer = glyph.layers[src.id]
				if srcLayer is None or (len(srcLayer.paths) == 0 and len(srcLayer.components) == 0):
					skipped += 1
					continue
				try:
					newLayer, info = self.emboldenLayer(srcLayer, ratio, newMasterId=newId)
					newLayer.userData["proportionalBold"] = {
						"ratio": ratio, "stem": info["w"], "offset": info["d"]}
					stems.append(info["w"])
					done += 1
				except NoStem:
					deferred.append((glyph, srcLayer))
				except Exception:
					failed += 1
					failures.append(glyph.name)
					log("Proportional Bold: failed on %s\n%s" % (glyph.name, traceback.format_exc()))
				if i and i % 500 == 0:
					log("Proportional Bold: %d glyphs, %.0fs" % (i, time.time() - t0))
			# second phase: unmeasurable glyphs get the median stem of the measured ones
			stems.sort()
			med = stems[len(stems) // 2] if stems else 0
			fallback, fallbackGlyphs = 0, []
			for glyph, srcLayer in deferred:
				if not med:
					failed += 1
					failures.append(glyph.name)
					log("Proportional Bold: %s has no measurable stem and the font has no median stem either" % glyph.name)
					continue
				try:
					newLayer, info = self.emboldenLayer(srcLayer, ratio, newMasterId=newId, fallbackStem=med)
					newLayer.userData["proportionalBold"] = {
						"ratio": ratio, "stem": info["w"], "offset": info["d"], "fallback": True}
					fallback += 1
					fallbackGlyphs.append(glyph.name)
				except Exception:
					failed += 1
					failures.append(glyph.name)
					log("Proportional Bold: failed on %s (fallback)\n%s" % (glyph.name, traceback.format_exc()))
			if fallback:
				log("Proportional Bold: fallback stem %.1f used for %d unmeasurable glyphs: %s" % (med, fallback, fallbackGlyphs[:20]))
		finally:
			font.enableUpdateInterface()
		return {"master": newMaster.name, "masterId": newId, "done": done, "fallback": fallback, "fallbackGlyphs": fallbackGlyphs[:50],
				"skipped": skipped, "failed": failed, "failures": failures[:50],
				"medianStem": med, "medianStemOut": med * ratio, "seconds": time.time() - t0}

	# ------------------------------------------------------------------ menu entry
	def run_(self, sender):
		try:
			font = Glyphs.font
			if font is None:
				return
			ratio = self.askRatio()
			if ratio is None:
				return
			r = self.emboldenFont(font, ratio)
			msg = (
				"Master “%s” created in %.0f s.\n%d glyphs emboldened, %d unmeasurable glyphs given the median stem, %d empty skipped, %d failed.\n"
				"Median stem: %.0f → %.0f units (per-glyph offset = (ratio−1)/2 × own stem).\n"
				"This is a draft master: check junctions and dense glyphs, then edit as usual."
				% (r["master"], r["seconds"], r["done"], r["fallback"], r["skipped"], r["failed"], r["medianStem"], r["medianStemOut"])
			)
			print("Proportional Bold: " + msg.replace("\n", " "))
			Glyphs.showNotification("Proportional Bold", "Master “%s” created (%d glyphs)." % (r["master"], r["done"]))
			alert = NSAlert.alloc().init()
			alert.setMessageText_("Proportional Bold")
			alert.setInformativeText_(msg)
			alert.runModal()
		except Exception:
			print(traceback.format_exc())

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
