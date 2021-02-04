#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import logging
logging.basicConfig(level=logging.DEBUG)

from textnormalizer import TextNormalizer

tn = TextNormalizer()
text = """нa WP. Компaния большaя и cepьёзнaя. Понятно."""
text2 = """
cпокойно гдe-то зa гоpодом. Звонит нeзнaкомый номep. Бepy тpyбкy. Дeвочкa c cильным yкpaинcким aкцeнтом пpeдcтaвляeтcя и говоpит, что очeнь зaинтepecовaло иx моё peзюмe
"""

print(tn.CheckText(text2))
