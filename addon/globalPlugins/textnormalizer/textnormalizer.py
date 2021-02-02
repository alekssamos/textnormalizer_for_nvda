#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Idea:
https://habr.com/ru/post/86303/
"""

import re

def replace(old, new, str, caseinsentive = False):
	if caseinsentive:
		return str.replace(old, new)
	else:
		return re.sub(re.escape(old), new, str, flags=re.IGNORECASE)

class TextNormalizer():
	"""Translates the letters of the alphabet mixed in normal"""

	lang = "?"
	Changes = False
	def CheckWord(self, word):
		"""Check the word

		Args:
			word (str): The source word

		Returns:
			str: The normalized word
		"""

		newword = word
		# если есть цифры - не меняем
		if re.match("[24579]", newword):
			return newword
		OnlyRu = "БбвГгДдЁёЖжЗзИиЙйЛлмнПптУФфЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"
		OnlyEn = "DdFfGghIiJjLlNQqRrSstUVvWwYZz"
		Rus = "АаВЕеКкМНОоРрСсТуХхЗО1тиапьб"
		Eng = "AaBEeKkMHOoPpCcTyXx30imu@nb6"

		IsRu100percent = False
		for c1 in word:
			for c2 in OnlyRu:
				IsRu100percent = IsRu100percent or (c1 == c2)

		if IsRu100percent:
			self.lang = "ru"

			#  конвертируем все сомнительные символы в русские
			for i in range(0, len(word)):
				if word[i] in Eng:
					# помечаем word[i] как "фальшивый"
					pass

			for i in range(0, len(Rus)):
				newword = newword.replace(Eng[i], Rus[i])

		else:
			IsEn100percent = False
			for c1 in word:
				for c2 in OnlyEn:
					IsEn100percent = IsEn100percent or (c1 == c2)
			if IsEn100percent:
				self.lang = "en"
				# конвертируем все сомнительные символы в английские
				for i in range(0, len(word)):
					if word[i] in Rus:
						# помечаем word[i] как "фальшивый"
						pass

				for i in range(0, len(Eng)):
					newword = newword.replace(Rus[i], Eng[i])

		# Были ли замены?
		self.Changes = newword != word
		newword = newword.lower()
		return newword

	def CheckText(self, text):
		"""Normalize the text

		Args:
			text (str): The source text

		Returns:
			str: The normalized text
		"""

		newText = text
		for word in re.findall("[\\w\\@]+", text, re.DOTALL + re.IGNORECASE):
			newWord = self.CheckWord(word)
			if self.Changes:
				newText = newText.replace(word, newWord)
		Rus = ["с", "у", "нет", "ее"]
		Eng = ["c", "y", "heт", "ee"]
		if text != newText:
			newText = newText.replace("B", "В").replace("H", "Н")
			for i in range(0, len(Rus)):
				newText = replace(Eng[i], Rus[i], newText, False)
			patterns = [
				"[cс][kк][oо][pр][еe]",
				"[kк][yу][pр][сc]",
				"[kк][yу][pр][сc][eе]",
				"[s][kк][yу][pр][eе]",
				r"[a]([a-zа-яё\s,:.?!]+)"
			]
			replaces = [
			"скорее",
			"курс",
			"курсе",
			"skype",
			r"а\1"
			]
			for i in range(0, len(patterns)):
				newText = re.sub(patterns[i], replaces[i], newText, flags=re.IGNORECASE)
		return newText

def main():
	import sys
	args = sys.argv
	if len(args) < 2:
		print("usage:", args[0], "Need text")
		sys.exit()
	tn = TextNormalizer()
	print(tn.CheckText(args[1]))

if __name__ == "__main__":
	main()
	