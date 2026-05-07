import re
import os
from pathlib import Path
from collections import defaultdict


def correct_misspellings(text):
    """
    Correct commonly misspelled words and organization names by reading from words_to_correct.txt
    """
    
    corrections = {}
    
    with open('words_to_correct.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if ' -> ' in line:
                misspelling, correction = line.split(' -> ', 1)
                if correction not in corrections:
                    corrections[correction] = []
                corrections[correction].append(misspelling)
    
    # Build regex patterns for each correction
    patterns = {}
    for correction, misspellings in corrections.items():
        # Escape misspellings and replace spaces with \s+ for flexible matching
        escaped_misspellings = []
        for m in misspellings:
            # Escape special regex characters and replace literal spaces with \s+
            m_escaped = re.escape(m).replace(r'\ ', r'\s+')
            escaped_misspellings.append(m_escaped)
        pattern = r'\b(' + '|'.join(escaped_misspellings) + r')\b'
        patterns[pattern] = correction
    
    # Apply each correction pattern
    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def clean_transcript(input_file, output_file=None):
    """
    Clean transcript file by:
    1. Removing timestamps
    2. Removing redundant/empty lines
    3. Grouping consecutive lines from the same speaker
    
    Args:
        input_file: Path to input transcript file
        output_file: Path to output file (optional, defaults to input_file with _cleaned suffix in processed directory)
    """
    
    if output_file is None:
        # Extract filename from input path and create output path in processed directory
        input_filename = Path(input_file).name
        base = input_filename.rsplit('.', 1)[0] if '.' in input_filename else input_filename
        output_file = f"./data/processed/{base}_cleaned.txt"
    
    # Parse the transcript
    entries = parse_webvtt(input_file)
    
    # Group consecutive entries by speaker
    grouped_entries = group_by_speaker(entries)
    
    # Write cleaned transcript
    write_cleaned_transcript(grouped_entries, output_file)
    
    print(f"✓ Cleaned transcript saved to: {output_file}")
    return grouped_entries


def parse_webvtt(file_path):
    """Parse WEBVTT format transcript file and extract speaker and text."""
    entries = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip header and empty lines
        if line in ['WEBVTT', ''] or '-->' in line:
            i += 1
            continue
        
        # Skip numbered entries (just the number)
        if line.isdigit():
            i += 1
            continue
        
        # Extract speaker and text
        if ':' in line:
            speaker, text = line.split(':', 1)
            speaker = speaker.strip()
            text = text.strip()
            
            # Collect all consecutive text from this speaker (handle wrapped lines)
            while i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.isdigit() and '-->' not in next_line and ':' not in next_line and next_line != 'WEBVTT':
                    text += ' ' + next_line
                    i += 1
                else:
                    break
            
            # Remove extra whitespace and filter out very short/redundant lines
            text = ' '.join(text.split())
            
            if text and len(text) > 2:  # Skip empty or very short lines
                # Apply spelling corrections to speaker name
                speaker = correct_misspellings(speaker)
                entries.append({'speaker': speaker, 'text': text})
        
        i += 1
    
    return entries


def group_by_speaker(entries):
    """
    Group consecutive entries from the same speaker.
    Returns a list of entries where consecutive same-speaker entries are combined.
    """
    if not entries:
        return []
    
    grouped = []
    current_speaker = entries[0]['speaker']
    current_text = entries[0]['text']
    
    for i in range(1, len(entries)):
        if entries[i]['speaker'] == current_speaker:
            # Same speaker, append text
            current_text += ' ' + entries[i]['text']
        else:
            # Different speaker, save previous and start new
            grouped.append({'speaker': current_speaker, 'text': current_text})
            current_speaker = entries[i]['speaker']
            current_text = entries[i]['text']
    
    # Don't forget the last entry
    grouped.append({'speaker': current_speaker, 'text': current_text})
    
    return grouped


def remove_redundancy(text):
    """Remove common redundancy patterns from text."""
    # Remove repeated words (simple case)
    # e.g., "the the" -> "the"
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
    
    return text


def remove_filler_words(text):
    """Remove common filler phrases from transcript text."""
    # Replace repeated filler-like patterns such as "x... x...", "x... x", and "x x..." with x
    text = re.sub(
        r'\b([A-Za-z]+)\b\s*(?:\.{2,}|…)+\s*,?\s*\1\b\s*(?:\.{2,}|…)+\s*,?\s*\1\b',
        r'\1',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\b([A-Za-z]+)\b\s*(?:\.{2,}|…)+\s*,?\s*\1\b',
        r'\1',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\b([A-Za-z]+)\b\s+\1\b\s*(?:\.{2,}|…)+\s*,?',
        r'\1',
        text,
        flags=re.IGNORECASE,
    )

    patterns = [
        r'\byou\s+know\b\s*,?',
        r'\blike\b\s*,?',
        r'\bso\b\s*,?',
    ]

    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Collapse extra whitespace and clean punctuation spacing
    text = re.sub(r'\s{2,}', ' ', text).strip()
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)

    return text


def write_cleaned_transcript(entries, output_file):
    """Write cleaned transcript to file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in entries:
            speaker = entry['speaker']
            text = remove_redundancy(entry['text'])
            text = remove_filler_words(text)
            text = correct_misspellings(text)
            f.write(f"{speaker}:\n{text}\n\n")


def process_all_transcripts(input_dir='./data/raw', output_dir='./data/processed'):
    """
    Process all transcript files from raw directory to processed directory.
    
    Args:
        input_dir: Directory containing raw transcript files
        output_dir: Directory to save processed transcript files
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        print(f"Directory {input_dir} does not exist.")
        return
    
    # Find all .txt files in input directory
    txt_files = list(input_path.glob('*.txt'))
    
    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        return
    
    print(f"Found {len(txt_files)} transcript files to process:")
    
    for txt_file in txt_files:
        print(f"\nProcessing: {txt_file.name}")
        try:
            # Create output filename in processed directory
            base_name = txt_file.stem  # filename without extension
            output_file = output_path / f"{base_name}_cleaned.txt"
            clean_transcript(str(txt_file), str(output_file))
        except Exception as e:
            print(f"  ✗ Error processing {txt_file.name}: {e}")


if __name__ == "__main__":
    # Process all raw transcripts to processed directory
    print("Starting transcript cleaning process...")
    process_all_transcripts()
    
    # Example usage for single file:
    # input_file = "./data/raw/Gayatri Mahr_IFAD_GTM Liaison.txt"
    # output_file = "./data/processed/Gayatri Mahr_IFAD_GTM Liaison_cleaned.txt"
    # if os.path.exists(input_file):
    #     print(f"Processing single file: {input_file}")
    #     clean_transcript(input_file, output_file)
    # else:
    #     print(f"File not found: {input_file}")
    #     print("\nUsage:")
    #     print("  Single file: clean_transcript('path/to/file.txt', 'path/to/output.txt')")
    #     print("  All files: process_all_transcripts('./data/raw', './data/processed')")
