# -*- coding: utf-8 -*-
import config
import braille
import scriptHandler
import os
import wx
import threading
import sys

import globalPluginHandler
import gui
import globalVars
import speech
import api
import textInfos
import ui
import addonHandler
import languageHandler
from logHandler import log

from .textnormalizer import TextNormalizer

addonHandler.initTranslation()
if "TextNormalizer" not in config.conf: config.conf["TextNormalizer"]={}
default_conf = {
	"copyToClipBoard": True,
	"autoNormalize": True,
	"change_case": True
}

for t in default_conf:
	if t not in config.conf["TextNormalizer"]:
		config.conf["TextNormalizer"][t] = default_conf[t]

def tobool(s):
	if s == "True" or s == "on" or str(s) == "1" or s == "yes": return True
	if s == "False" or s == "off" or str(s) == "0" or s == "no": return False
	return not not s

tn = TextNormalizer()

class TextNormalizerSettingsDialog(gui.SettingsDialog):
	title = _("Text Normalizer Settings")

	def makeSettings(self, sizer):
		settingsSizerHelper = gui.guiHelper.BoxSizerHelper(self, sizer=sizer)
		self.copyToClipBoard = wx.CheckBox(self, label=_("&Copy text to clipboard"))
		self.copyToClipBoard.SetValue(tobool(config.conf["TextNormalizer"]["copyToClipBoard"]))
		settingsSizerHelper.addItem(self.copyToClipBoard)

		self.autoNormalize = wx.CheckBox(self, label=_("&Instant normalizing"))
		self.autoNormalize.SetValue(tobool(config.conf["TextNormalizer"]["autoNormalize"]))
		settingsSizerHelper.addItem(self.autoNormalize)

		self.change_case_checkbox = wx.CheckBox(self, label=_("&Capitalize first letter"))
		self.change_case_checkbox.SetValue(tobool(config.conf["TextNormalizer"]["change_case"]))
		settingsSizerHelper.addItem(self.change_case_checkbox)

		self.source_text = settingsSizerHelper.addLabeledControl(_("&Source text:"), wx.TextCtrl, value="")
		self.normalize_text = wx.Button(self, label=_("&Normalize entered text"))
		self.normalize_text.Bind(wx.EVT_BUTTON, self.onNormalize_text)
		settingsSizerHelper.addItem(self.normalize_text)
		self.normalized_text = settingsSizerHelper.addLabeledControl(_("N&ormalized text:"), wx.TextCtrl, value="",
			style=wx.TE_READONLY)

	def postInit(self):
		self.source_text.SetFocus()

	def onNormalize_text(self, event):
		config.conf["TextNormalizer"]["change_case"] = self.change_case_checkbox.Value
		change_case = config.conf["TextNormalizer"]["change_case"]
		self.normalized_text.Value = tn.CheckText(self.source_text.Value, change_case)
		self.normalized_text.SetFocus()

	def _save_settings(self):
		try:
			# config.conf.save();
			pass
		except (IOError, OSError) as e:
			gui.messageBox(e.strerror, _("Error saving settings"), style=wx.OK | wx.ICON_ERROR)

	def onReset(self, event):
		config.conf["TextNormalizer"] = default_conf.copy()
		# self._save_settings()
		self.Close()

	def onOk(self, event):
		config.conf["TextNormalizer"]["copyToClipBoard"] = self.copyToClipBoard.Value
		config.conf["TextNormalizer"]["autoNormalize"] = self.autoNormalize.Value
		config.conf["TextNormalizer"]["change_case"] = self.change_case_checkbox.Value
		# self._save_settings()
		super(TextNormalizerSettingsDialog, self).onOk(event)

class TextNormalizerThr(threading.Thread):
	def __init__(self, callback, **kwargs):
		super(TextNormalizerThr, self).__init__()
		self._callback = callback
		self._kwargs = kwargs
		self.daemon = True
		self.start()

	def run(self):
		change_case = config.conf["TextNormalizer"]["change_case"]
		if isinstance(self._kwargs["text"], str):
			self._kwargs["text"] = tn.CheckText(self._kwargs["text"], change_case)
		else:
			self._kwargs["text"] = [tn.CheckText(txt, change_case) for txt in self._kwargs["text"]]

		wx.CallAfter(self._callback, self._kwargs["text"])

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Text Normalizer")

	lastnormalizedText = ""
	def __init__(self):
		super(GlobalPlugin, self).__init__()
		if globalVars.appArgs.secure: return

		try:
			speech.speech.speak = self.speakDecorator(speech.speech.speak)
		except:
			speech.speak = self.speakDecorator(speech.speak)
		try:
			try:
				speech.speechWithoutPauses.SpeechWithoutPauses.speakWithoutPauses = speech.speechWithoutPauses.SpeechWithoutPauses(speakFunc=speech.speech.speak).speakWithoutPauses
			except AttributeError:
				speech.speakWithoutPauses=speech.SpeechWithoutPauses(speakFunc=speech.speak).speakWithoutPauses
		except:
			pass

		# Creates submenu of addon
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU,
			lambda e: gui.mainFrame._popupSettingsDialog(TextNormalizerSettingsDialog),
			gui.mainFrame.sysTrayIcon.toolsMenu.Append(wx.ID_ANY, _("Text Normalizer")))

	def speakDecorator(self, speak):
		def my_speak(speechSequence, *args, **kwargs):
			return speak(speechSequence, *args, **kwargs)
		def wrapper(speechSequence, *args, **kwargs):
			self.speechSequence = speechSequence
			def is_not_str(ss):
				for i in speechSequence:
					if not isinstance(i, str): return True
				return False
			if not tobool(config.conf["TextNormalizer"]["autoNormalize"]):
				return speak(speechSequence, *args, **kwargs)
			change_case = config.conf["TextNormalizer"]["change_case"]
			list_speechSequence = []
			for i in speechSequence:
				if isinstance(i, str):
					list_speechSequence.append(tn.CheckText(i, change_case))
				else:
					list_speechSequence.append(i)
			txt = " ".join([i for i in list_speechSequence if isinstance(i, str)])
			self.lastnormalizedText = txt
			try:
				braille.handler.message(txt)
			except:
				pass
			return speak(list_speechSequence, *args, **kwargs)
		return wrapper


	def normalizeHandler(self, text):
		self.lastnormalizedText = "".join(text)
		ui.message(self.lastnormalizedText)

		if config.conf["TextNormalizer"]["copyToClipBoard"]:
			api.copyToClip(self.lastnormalizedText)

	def getSelectedText(self):
		obj = api.getCaretObject()
		try:
			info = obj.makeTextInfo(textInfos.POSITION_SELECTION)
			if info or not info.isCollapsed:
				return info.text
		except (RuntimeError, NotImplementedError):
			return None

	@scriptHandler.script(
		description=_("Normalize text from the clipboard")
	)
	def script_normalize_clip(self, gesture):
		try:
			text = api.getClipData()
		except Exception:
			ui.message(_("No text to normalize"))
			return

		TextNormalizerThr(self.normalizeHandler, text=text)

	@scriptHandler.script(
		description=_("Normalizes the selected text.")
	)
	def script_normalize_sel(self, gesture):
		text = self.getSelectedText()
		if not text:
			ui.message(_("No text to normalize"))
			return

		TextNormalizerThr(self.normalizeHandler, text=text)

	@scriptHandler.script(
		description=_("Normalizes the last spoken phrase")
	)
	def script_normalizeSpokenPhrase(self, gesture):
		text = "\n".join([i for i in self.speechSequence if isinstance(i, str)])

		TextNormalizerThr(self.normalizeHandler, text=text)

	@scriptHandler.script(
		description=_("Normalizes text from navigator object")
	)
	def script_normalizeNavigatorObject(self, gesture):
		obj = api.getNavigatorObject()
		text = obj.name

		if not text:
			try:
				text = obj.makeTextInfo(textInfos.POSITION_ALL).clipboardText
				if not text: raise RuntimeError()
			except (RuntimeError, NotImplementedError):
				ui.message(_("No text to normalize"))
				return

		TextNormalizerThr(self.normalizeHandler, text=text)

	def script_copyLastNormalizedText(self, gesture):
		if self.lastnormalizedText:
			api.copyToClip(self.lastnormalizedText)
			ui.message(_("Copy to clipboard"))
		else:
			ui.message(_("No normalization to copy"))
	script_copyLastNormalizedText.__doc__ = _("Copy last normalization to clipboard")

	def script_showSettingsDialog(self, gesture):
		gui.mainFrame._popupSettingsDialog(TextNormalizerSettingsDialog)
	script_showSettingsDialog.__doc__ = _("Shows the settings dialog")

	@scriptHandler.script(
		description=_("Switches the function of automatic normalization")
	)
	def script_switchAutoNormalize(self, gesture):
		if not tobool(config.conf["TextNormalizer"]["autoNormalize"]):
			ui.message(_("Automatic normalization enabled"))
			config.conf["TextNormalizer"]["autoNormalize"] = True
		else:
			config.conf["TextNormalizer"]["autoNormalize"] = False
			ui.message(_("Automatic normalization disabled"))
