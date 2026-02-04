#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Levantine Arabic Phonetiser - Batch Processing Script
====================================================

This script phonetises Levantine Arabic text from various sources and outputs
the phoneme sequences in different formats.

Features:
- Process Hugging Face datasets, CSV files, or plain text files
- Save to CSV, plain text, or Hugging Face Hub
- Configurable column names
- Proper error handling

Usage:
    python run_levantine_phonetiser.py --input_type [huggingface|csv|text] \
                                       --input_path <input_data> \
                                       --output_type [csv|text|huggingface]
"""

import sys
import json
import argparse
import string
from pathlib import Path

# Import the phonetiser
try:
    from phonetiser.phonetise_levantine import get_phonemes, LevantinePhonetiser
except ImportError:
    print("Error: Could not import phonetiser module. Make sure you're running from the correct directory.")
    sys.exit(1)

# Import data processing libraries
try:
    from datasets import load_dataset, Dataset, DatasetDict
    import pandas as pd
except ImportError:
    print("Error: Required packages not installed. Run: pip install datasets pandas")
    sys.exit(1)


# =============================================================================
# TEXT PREPROCESSING FUNCTIONS
# =============================================================================

def remove_digits(text: str) -> str:
    """Remove all digits from the given text."""
    if not isinstance(text, str):
        return text
    return ''.join(char for char in text if not char.isdigit())


def remove_punctuation(text: str) -> str:
    """Remove common punctuation from the input text."""
    if not isinstance(text, str):
        return text
    # Create a translation table that maps each punctuation character to None
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator)


def clean_text(text: str) -> str:
    """Clean text by removing punctuation and digits."""
    if not isinstance(text, str):
        return text
    text = remove_punctuation(text)
    text = remove_digits(text)
    return text.strip()


# =============================================================================
# PHONETISATION FUNCTIONS
# =============================================================================

class LevantinePhonetiserProcessor:
    """Processor for batch phonetisation of Levantine Arabic."""

    def __init__(self, urban: bool = True, simplify_feminine: bool = True):
        """
        Initialize the processor.

        Args:
            urban: Use urban dialect (qaf → hamza)
            simplify_feminine: Simplify feminine plural endings
        """
        self.phonetiser = LevantinePhonetiser(
            urban=urban,
            simplify_feminine_endings=simplify_feminine
        )
        self.urban = urban
        self.simplify_feminine = simplify_feminine

    def phonetise_text(self, text: str) -> str:
        """
        Phonetically transcribe Arabic text.

        Args:
            text: Arabic text to phonetise

        Returns:
            Space-separated phoneme sequence
        """
        if text is None:
            return None

        # Clean text
        cleaned = clean_text(text)

        if not cleaned:
            return None

        try:
            # Get phonemes
            _, pronunciations = self.phonetiser.phonetise(cleaned)

            # Extract primary pronunciation
            phonemes = []
            for word_prons in pronunciations:
                if word_prons:
                    phonemes.append(word_prons[0])

            # Join and clean up
            result = ' '.join(phonemes)
            # Remove extra spaces
            result = ' '.join(result.split())

            return result

        except Exception as e:
            print(f"Error phonetising text: '{text}'. Error: {e}", file=sys.stderr)
            return f"[ERROR_PHONETISING: {e}]"

    def process_batch(self, batch: dict) -> dict:
        """
        Process a batch of text to generate phoneme sequences.
        Designed to be used with dataset.map().

        Args:
            batch: Dictionary containing a batch of data

        Returns:
            Dictionary with phoneme_sequence added
        """
        texts = batch['text_to_phonetise']
        phoneme_sequences = []

        for text in texts:
            result = self.phonetise_text(text)
            phoneme_sequences.append(result)

        batch['phoneme_sequence'] = phoneme_sequences
        return batch


# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

def load_huggingface_dataset(
    path: str,
    text_column: str = None,
    processor = None
) -> DatasetDict:
    """
    Load and process a Hugging Face dataset.

    Args:
        path: Hugging Face dataset path/name
        text_column: Name of the text column (auto-detected if None)
        processor: LevantinePhonetiserProcessor instance

    Returns:
        Processed DatasetDict
    """
    print(f"Loading Hugging Face dataset: '{path}'...")
    data_loaded = load_dataset(path)

    # Find text column
    first_split = next(iter(data_loaded.keys()))
    first_split_columns = data_loaded[first_split].column_names

    if text_column:
        if text_column not in first_split_columns:
            raise ValueError(
                f"Text column '{text_column}' not found in dataset '{path}'. "
                f"Available columns: {first_split_columns}"
            )
    else:
        # Auto-detect text column
        text_column = None
        for col in first_split_columns:
            if 'text' in col.lower() or 'sentence' in col.lower() or 'arabic' in col.lower():
                text_column = col
                break
        if text_column is None:
            # Try to find any column with Arabic text
            for col in first_split_columns:
                sample = data_loaded[first_split][0][col]
                if isinstance(sample, str) and any('\u0600' <= c <= '\u06FF' for c in sample):
                    text_column = col
                    break

        if text_column is None:
            raise ValueError(
                f"Could not auto-detect text column in dataset '{path}'. "
                f"Available columns: {first_split_columns}. "
                f"Use --hf_text_column to specify."
            )

    print(f"Using text column: '{text_column}'")

    # Process all splits
    processed_datasets = DatasetDict()
    for split_name, ds_split in data_loaded.items():
        print(f"Processing split: {split_name}...")

        # Rename text column
        ds_split = ds_split.rename_column(text_column, 'text_to_phonetise')

        # Add ID column if needed
        if 'ID' not in ds_split.column_names:
            ds_split = ds_split.add_column(
                'ID',
                [f"{split_name}_{i}" for i in range(len(ds_split))]
            )

        # Process
        ds_split = ds_split.map(
            processor.process_batch,
            batched=True,
            remove_columns=['text_to_phonetise']
        )
        processed_datasets[split_name] = ds_split

    return processed_datasets


def load_csv_dataset(
    path: str,
    column_id: str = 'ID',
    column_text: str = 'text',
    processor = None
) -> Dataset:
    """
    Load and process a CSV file.

    Args:
        path: Path to CSV file
        column_id: ID column name
        column_text: Text column name
        processor: LevantinePhonetiserProcessor instance

    Returns:
        Processed Dataset
    """
    print(f"Loading CSV file: '{path}'...")
    df = pd.read_csv(path)

    # Validate columns
    if column_id not in df.columns:
        raise ValueError(f"CSV missing ID column: '{column_id}'")
    if column_text not in df.columns:
        raise ValueError(f"CSV missing text column: '{column_text}'")

    # Create dataset
    data = Dataset.from_pandas(df[[column_id, column_text]])

    # Rename columns
    if column_id != 'ID':
        data = data.rename_column(column_id, 'ID')
    if column_text != 'text_to_phonetise':
        data = data.rename_column(column_text, 'text_to_phonetise')

    # Process
    print("Phonetising CSV data...")
    data = data.map(
        processor.process_batch,
        batched=True,
        remove_columns=['text_to_phonetise']
    )

    return data


def load_text_dataset(
    path: str,
    processor = None
) -> Dataset:
    """
    Load and process a plain text file.

    Args:
        path: Path to text file
        processor: LevantinePhonetiserProcessor instance

    Returns:
        Processed Dataset
    """
    print(f"Loading text file: '{path}'...")
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(lines)} lines")

    # Create dataset
    df = pd.DataFrame({
        'ID': [f"line_{i+1}" for i in range(len(lines))],
        'text_to_phonetise': lines
    })

    data = Dataset.from_pandas(df)

    # Process
    print("Phonetising text data...")
    data = data.map(
        processor.process_batch,
        batched=True,
        remove_columns=['text_to_phonetise']
    )

    return data


# =============================================================================
# OUTPUT FUNCTIONS
# =============================================================================

def save_to_csv(data, output_path: str):
    """Save processed data to CSV file."""
    print(f"Saving to CSV: '{output_path}'...")

    if isinstance(data, DatasetDict):
        # Combine all splits
        combined_df = pd.concat([ds.to_pandas() for ds in data.values()])
        combined_df = combined_df[['ID', 'phoneme_sequence']]
        combined_df.to_csv(output_path, index=False)
        print(f"Combined results from all splits saved to '{output_path}'")
    else:
        output_df = data.to_pandas()[['ID', 'phoneme_sequence']]
        output_df.to_csv(output_path, index=False)
        print(f"Results saved to '{output_path}'")


def save_to_text(data, output_path: str):
    """Save processed data to plain text file."""
    print(f"Saving to text file: '{output_path}'...")

    with open(output_path, 'w', encoding='utf-8') as f:
        if isinstance(data, DatasetDict):
            for split_name, ds_split in data.items():
                for entry in ds_split:
                    if entry['phoneme_sequence'] is not None:
                        f.write(entry['phoneme_sequence'] + '\n')
        else:
            for entry in data:
                if entry['phoneme_sequence'] is not None:
                    f.write(entry['phoneme_sequence'] + '\n')

    print(f"Results saved to '{output_path}' (one phoneme sequence per line)")


def save_to_huggingface(data, repo_id: str):
    """Save processed data to Hugging Face Hub."""
    print(f"Pushing to Hugging Face Hub: '{repo_id}'...")

    if isinstance(data, DatasetDict):
        for split_name, ds_split in data.items():
            print(f"Pushing split '{split_name}'...")
            ds_split.push_to_hub(repo_id, split=split_name)
    else:
        data.push_to_hub(repo_id)

    print("Dataset successfully pushed to Hugging Face Hub!")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phonetise Levantine Arabic text from various sources"
    )

    # Input arguments
    parser.add_argument(
        '--input_type',
        type=str,
        required=True,
        choices=['huggingface', 'csv', 'text'],
        help="Type of input data"
    )
    parser.add_argument(
        '--input_path',
        type=str,
        required=True,
        help="Path to input file or Hugging Face dataset name"
    )

    # Output arguments
    parser.add_argument(
        '--output_type',
        type=str,
        required=True,
        choices=['csv', 'text', 'huggingface'],
        help="Type of output"
    )
    parser.add_argument(
        '--output_path',
        type=str,
        help="Output file path (for csv/text)"
    )
    parser.add_argument(
        '--hf_output_repo_id',
        type=str,
        help="Hugging Face repo ID for output (for huggingface output)"
    )

    # CSV input arguments
    parser.add_argument(
        '--column_id',
        type=str,
        default='ID',
        help="CSV ID column name (default: ID)"
    )
    parser.add_argument(
        '--column_text',
        type=str,
        default='text',
        help="CSV text column name (default: text)"
    )

    # Hugging Face arguments
    parser.add_argument(
        '--hf_text_column',
        type=str,
        default=None,
        help="Hugging Face dataset text column name"
    )

    # Levantine dialect options
    parser.add_argument(
        '--rural',
        action='store_true',
        help="Use rural dialect (preserve qaf) instead of urban"
    )
    parser.add_argument(
        '--keep_feminine',
        action='store_true',
        help="Keep feminine plural endings (don't simplify)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.output_type in ['csv', 'text'] and not args.output_path:
        parser.error("--output_path is required for csv/text output")
    if args.output_type == 'huggingface' and not args.hf_output_repo_id:
        parser.error("--hf_output_repo_id is required for huggingface output")

    # Initialize processor
    urban = not args.rural
    simplify_feminine = not args.keep_feminine

    dialect_type = "urban" if urban else "rural"
    print(f"\nUsing Levantine {dialect_type} dialect settings")
    print(f"  Qaf → {'hamza' if urban else 'qaf'}")
    print(f"  Tha/Dhal/Dha → simplified")
    print(f"  Feminine endings → {'simplified' if simplify_feminine else 'preserved'}\n")

    processor = LevantinePhonetiserProcessor(
        urban=urban,
        simplify_feminine=simplify_feminine
    )

    # Load and process data
    try:
        if args.input_type == 'huggingface':
            data = load_huggingface_dataset(
                args.input_path,
                args.hf_text_column,
                processor
            )
        elif args.input_type == 'csv':
            data = load_csv_dataset(
                args.input_path,
                args.column_id,
                args.column_text,
                processor
            )
        else:  # text
            data = load_text_dataset(args.input_path, processor)

        print("\nPhonetisation complete!")

        # Save output
        if args.output_type == 'csv':
            save_to_csv(data, args.output_path)
        elif args.output_type == 'text':
            save_to_text(data, args.output_path)
        else:  # huggingface
            save_to_huggingface(data, args.hf_output_repo_id)

        print("\nScript finished successfully!")

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
