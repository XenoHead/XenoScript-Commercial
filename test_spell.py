from spellchecker import SpellChecker
import re

spell = SpellChecker()
words = ["don't", "dont", "I'm", "im", "int", "ext", "cont"]

for w in words:
    print(f"'{w}' in spell: {w in spell}")
