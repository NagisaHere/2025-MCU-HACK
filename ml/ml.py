import requests
import numpy as np
import time
import re
import os
import sys
import cv2
import subprocess
import tempfile
from collections import Counter

# Ensure required packages are installed
def ensure_package(pkg_name, import_name=None):
    try:
        __import__(import_name or pkg_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])

ensure_package("pyspellchecker", "spellchecker")
ensure_package("language-tool-python", "language_tool_python")
ensure_package("googletrans", "googletrans")
ensure_package("gtts", "gtts")
ensure_package("easyocr", "easyocr")

from spellchecker import SpellChecker
import language_tool_python
from googletrans import Translator
from gtts import gTTS
import easyocr

# Initialize tools
spell         = SpellChecker()
grammar_tool  = language_tool_python.LanguageTool('en-US')
translator    = Translator()
dest_lang     = 'pt'
reader        = easyocr.Reader(['en'], gpu=False)  # set gpu=True if you have CUDA

# Burst settings
URL          = "http://192.168.139.201/image" # replace with ip of your server
BURST_COUNT  = 5
BURST_DELAY  = 0.01  # seconds

# arduino button settings
RUN_WITH_BUTTON = False # for button presses
ARDUINO_PORT = "/dev/ttyUSB0" # replace with your port
BUTTON_PIN = 2

def speak_natural(text: str, lang: str = 'pt'):
    """Generate a temporary MP3 via gTTS and play it."""
    if not text.strip():
        return
    fd, tmp_path = tempfile.mkstemp(suffix='.mp3')
    os.close(fd)
    gTTS(text=text, lang=lang, slow=False).save(tmp_path)
    # macOS:
    subprocess.run(['afplay', tmp_path], check=False)
    # Linux alternative:
    # subprocess.run(['mpg123', tmp_path], check=False)
    os.remove(tmp_path)

def fetch_frame(url: str) -> np.ndarray:
    """GET a JPEG from URL and decode to an OpenCV image."""
    try:
        resp = requests.get(url, timeout=2)
    except requests.RequestException as e:
        print(f"  → HTTP error: {e}")
        return None
    if resp.status_code != 200:
        print(f"  → HTTP {resp.status_code} fetching image")
        return None
    arr = np.frombuffer(resp.content, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        print("  → Failed to decode JPEG")
    return img

def ocr_with_easyocr(img: np.ndarray) -> list[str]:
    """Use EasyOCR to extract and filter text tokens from an image."""
    # 1) Preprocessing
    h, w = img.shape[:2]
    small = cv2.resize(img, (w//2, h//2), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
    gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # 2) OCR
    texts = reader.readtext(gray, detail=0, paragraph=True)

    # 3) Filtering & cleanup
    tokens = []
    for line in texts:
        for w in re.findall(r"[A-Za-z]{3,}", line):
            tokens.append(w)
    return tokens

# --- Burst-capture via HTTP GET with display ---

if (RUN_WITH_BUTTON):
    import pyfirmata
    print("initialising board")
    board = pyfirmata.Arduino(ARDUINO_PORT);
    board.digital[BUTTON_PIN].mode = pyfirmata.INPUT
    iter8 = pyfirmata.util.Iterator(board);
    iter8.start()

    while (1):
        # print("reading for button inputs")
        if board.digital[BUTTON_PIN].read() == 1:
            # flush the first couple of images
            for i in range(10):
                response = requests.get(URL)
            break

cv2.namedWindow('Burst Capture', cv2.WINDOW_NORMAL)
print(f"Grabbing {BURST_COUNT} frames via HTTP…")
captures = []

for i in range(BURST_COUNT):
    img = fetch_frame(URL)
    if img is not None:
        captures.append(img)
        print(f"  → frame {i+1} captured")
        # show it
        cv2.imshow('Burst Capture', img)
        # waitKey in ms; multiplies BURST_DELAY by 1000
        if cv2.waitKey(int(BURST_DELAY * 1000)) & 0xFF == ord('q'):
            print("Display window closed by user.")
            break
    else:
        print(f"  → frame {i+1} failed, skipping")
    time.sleep(BURST_DELAY)

cv2.destroyAllWindows()

if not captures:
    raise RuntimeError("No frames captured; aborting.")

# --- OCR + token fusion pipeline ---
all_tokens = []
for idx, img in enumerate(captures, 1):
    toks = ocr_with_easyocr(img)
    print(f"Frame {idx}: {len(toks)} tokens via EasyOCR")
    all_tokens.extend(toks)

# Keep only words seen ≥2 times
freq = Counter(all_tokens)
final_tokens = [w for w, cnt in freq.items() if cnt >= 2]

# Spell-correct & capitalize
corrected = []
for w in final_tokens:
    c = spell.correction(w.lower()) or w.lower()
    corrected.append(c.capitalize())
final_tokens = corrected

# Build sentence and grammar-correct
result_text = ' '.join(final_tokens)
result_text = grammar_tool.correct(result_text)

# Translate
translation = ''
if result_text.strip():
    try:
        translation = translator.translate(result_text, dest=dest_lang).text
    except Exception as e:
        print(f"  → Translation error: {e}")

# Output & save
output = (
    f"Fused {len(final_tokens)} words (≥2 appearances):\n"
    f"OCR (corrected): {result_text}\n"
    f"Translated ({dest_lang}): {translation}\n"
)
print(output)
with open('results.txt', 'w', encoding='utf-8') as f:
    f.write(output)

# Speak the translation
speak_natural(translation, lang=dest_lang)

print("Done – results saved to results.txt")
