Amay Bansal
5/7/2026
# Transcript Cleaning

This folder contains a simple transcript cleaning script for WebVTT-style interview transcripts for qualitative nterviews.

## What it does

`cleaning.py` will:
- parse transcript files from `data/raw`
- remove WebVTT timestamps and numbered cue lines
- merge consecutive lines from the same speaker
- normalize common misspellings specified in `words_to_correct.txt`
- remove filler phrases such as `you know`, `like`, and `so`
- collapse repeated ellipsis patterns like `x... x...`, `x... x`, and `x x...`
- write cleaned output to `data/processed`

## Configuration

### Spelling Corrections

Spelling corrections are configured in `words_to_correct.txt`. Each line should contain a misspelling and its correction in the format:

```
misspelling -> correction
```

For example:
```
mavim -> MAVIM
ifad -> IFAD
navte jaswini -> Nav Tejaswini
```

The script will automatically read these corrections and apply them during processing. Add, remove, or modify entries in this file to customize the spelling corrections for your transcripts.

## Requirements

- Python 3.8+

## Usage

From the repository root:

```bash
cd "...\Transcript_cleaning_EPAR"
python cleaning.py
```

This will process all `.txt` files in `data/raw` and save cleaned versions to `data/processed` with the `_cleaned.txt` suffix.

## Single-file use

To clean a single file manually, update the script call in the `if __name__ == "__main__"` section or import and call:

```python
from cleaning import clean_transcript
clean_transcript("./data/raw/IFAD Liaison.txt")
```

## Output

Cleaned transcripts are saved to the `data/processed` folder with names like:

- `[file]_cleaned.txt`

## Notes

- The script still needs to be processed to separate interviewer and interviewee text.
- The script is designed for txt files exported in WebVTT-like format.
- If you need to add new filler words, update `remove_filler_words()` in `cleaning.py`.
