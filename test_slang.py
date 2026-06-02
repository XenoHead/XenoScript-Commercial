from spellchecker import SpellChecker

spell = SpellChecker()
words = ["kinda", "yer"]

for w in words:
    print(f"'{w}' in spell: {w in spell}")
