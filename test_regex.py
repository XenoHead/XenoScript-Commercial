import re

words = ["don't", "INT.", "CONT.", "I'm"]
for w in words:
    w_clean = re.sub(r'[^\w\s\']', '', w.lower())
    print(f"Original: {w} -> Clean: {w_clean}")
