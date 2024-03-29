#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idea:
https://habr.com/ru/post/86303/
"""

from functools import lru_cache
import re

try: from logHandler import log
except  ImportError: import logging as log


@lru_cache(16384)
def normalizer_replace_text(old, new, string, case_insensitive = False):
	if case_insensitive:
		return string.replace(old, new)
	else:
		return re.sub(re.escape(old), new, string, flags=re.IGNORECASE)


class TextNormalizer():
	"""Translates the letters of the alphabet mixed in normal"""

	lang = "?"
	Changes = False
	IsRu100percent = False
	IsEn100percent = False
	
	mixpattern = re.compile(r"\b([а-яё]+[a-z]+[а-яё]+|[a-z]+[а-яё]+[a-z]|[a-z]+[а-яё]|[а-яё]+[a-z])\b",
		flags=re.I)
	dgpattern = re.compile(
		"([0-9]+[k]|mln|mlrd|тыс|"
		"(дол|руб|евр|уе|тен|руп|гр?в)[а-я]+|млн|млрд|^[0-9]+(г|кг|т|ц|гц|мгц|"
		"мм|см|дм|м|(б|кб|мб|гб|тб)(ит|айт)?)$)",
		flags=re.IGNORECASE)

	def __init__(self):
		self.lettersstrng = {
			"α":"а",
			"ʍ":"м",
			"∂":"д",
			"ū":"о",
			"ū":"й"
		}
		self.OnlyRu = "БбвГгДдЁёЖжЗзИиЙйЛлмнПптУФфЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"
		self.OnlyEn = "DdFfGghIiJjLlNQqRrSstUVvWwYZz"
		self.Rus = "АаВЕеКкМНОоРрСсТуХхЗОтиапьбт"
		self.Eng = "AaBEeKkMHOoPpCcTyXx30mu@nb6m"
		self.patterns = [
			"[kк][аa][kк]",
			"[tт][aа][kк]",
			r"[a]([\s:,.?!_(){}=+-]+[а-яёА-ЯЁ])",
			"[cс][kк][oо][pр][еe][еe]",
			"[kк][yу][pр][сc]",
			"[kк][yу][pр][сc][eе]",
			"[s][kк][yу][pр][eе]",
			"[HН][eе][tт]",
			"тe",
			"eг",
			"дe",
			"[cс][pр][oо][kк]",
			"CCCP",
			"CCP",
			r"\b[HН][аa]\b",
			r"\b[HН][eе]\b",
			r"\b[HН][oо]\b",
			r"\b[HН][уy]\b",
			r"([а-яёА-ЯЁ])m",
			r"m([а-яёА-ЯЁ])",
			"∂",
			"α",
			"ū",
			"meх",
			r"\bom\b",
			r"([а-яёА-ЯЁ])pu"
		]
		self.replaces = [
			"как",
			"так",
			r"а\1",
			"скорее",
			"курс",
			"курсе",
			"skype",
			"нет",
			"те",
			"ег",
			"де",
			"срок",
			"СССР",
			"ССР",
			r"На",
			r"Не",
			r"Но",
			r"Ну",
			r"\1т",
			r"т\1",
			"д",
			"а",
			"й",
			"тех",
			"от",
			r"\1ри"
		]


	def CheckWord(self, word, change_case = True):
		"""Check the word

		Args:
			word (str): The source word

		Returns:
			str: The normalized word
		"""

		self.Changes = False
		self.lang = "?"

		# в VK часто стал использоваться символ "ë" как русская буква "е".
		newword = normalizer_replace_text("ë", "е", word, True)
		# остальные символы из постов VK
		for k, v in self.lettersstrng.items():
			newword = normalizer_replace_text(k, v, newword, True)
		# один символ не имеет смысла
		if len(newword.strip()) == 1:
			return newword

		# Пропускаем хештеги, по скольку там могут быть упоминания через значёк @
		if newword[0] == "#":
			return newword

		# обозначения чисел не меняем
		if re.search(self.dgpattern, newword):
			return newword
		# если есть цифры - не меняем
		if re.search("[124579]", newword):
			return newword
		# если в конце русского слова цифра - не меняем
		# если у английского слова цифра три - тоже не меняем
		if (re.search("^[а-яёА-ЯЁ]+[0-9]+$", newword)) or (re.search("^[a-zA-Z]+$", newword) and "3" in newword):
			return newword

		self.IsRu100percent = False
		for c1 in word:
			for c2 in self.OnlyRu:
				self.IsRu100percent = self.IsRu100percent or (c1 == c2)

		if self.IsRu100percent:
			self.lang = "ru"

			for i in range(0, len(self.Rus)):
				newword = normalizer_replace_text(self.Eng[i], self.Rus[i], newword, True)

		else:
			self.IsEn100percent = False
			for c1 in word:
				for c2 in self.OnlyEn:
					self.IsEn100percent = self.IsEn100percent or (c1 == c2)
			if self.IsEn100percent:
				self.lang = "en"

				for i in range(0, len(self.Eng)):
					newword = normalizer_replace_text(self.Rus[i], self.Eng[i], newword, True)

		# Были ли замены?
		self.Changes = newword != word
		newword = newword.lower()
		if self.Changes and change_case: newword = newword.capitalize()
		return newword

	def CheckText(self, text, change_case = True):
		"""Normalize the text

		Args:
			text (str): The source text

		Returns:
			str: The normalized text
		"""

		# сразу убираем символ "мягкий перенос"
		newText = text.replace("\u200d", "").replace(chr(173), "").replace(chr(8205), "")
		words = re.findall("[\\w\\@#]+", newText, re.IGNORECASE)
		words2 = words.copy()
		words2.reverse()
		for x in range(0, 3):
			words3 = re.findall("[\\w@#]+", newText, flags=re.IGNORECASE)
			words4 = [f for f in words3 if re.findall("[a-zA-Z]", f) and re.findall("[а-яА-ЯЁ]", f)]
			for word in (words, words2, words4)[x]:
				newWord = self.CheckWord(word, change_case)
				if self.Changes:
					newText = normalizer_replace_text(word, newWord, newText, False)
			Rus = ["с", "у", "нет", "ее"]
			Eng = ["c", "y", "heт", "ee"]
			if text != newText:
				newText = newText.replace("B", "В")
				newText = newText.replace(" o ", " о ")
				newText = newText.replace(" O ", " О ")
				newText = newText.replace(" c ", " с ")
				newText = newText.replace(" C ", " С ")
				for i in range(0, len(Rus)):
					newText = normalizer_replace_text(Eng[i], Rus[i], newText, False)
				for i in range(0, len(self.patterns)):
					if text != newText:
						newText = re.sub(self.patterns[i], self.replaces[i], newText, flags=re.IGNORECASE)
		newText = re.sub(r"([a-z])у([a-z])", r"\1y\2", newText)
		newText = re.sub(r"([a-z])у", r"\1y", newText)
		newText = re.sub(r"у([a-z])", r"y\1", newText)
		newText = normalizer_replace_text("сh", "ch", newText, True)
		newText = normalizer_replace_text("сe", "ce", newText, True)
		newText = normalizer_replace_text("Вo", "Bo", newText, True)
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
	
