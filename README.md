# Levantine Arabic Phonetiser

A rule-based phonetiser for Levantine Arabic dialects (Lebanese, Syrian, Jordanian, Palestinian).

## Features

- **Rule-based phonetisation** following Levantine Arabic phonological rules
- **Urban vs Rural dialect support** - handles qaf → hamza (urban) or qaf (rural)
- **Fixed words dictionary** - common Levantine words with correct pronunciations
- **Batch processing** - process Hugging Face datasets, CSV files, or plain text
- **Multiple output formats** - CSV, plain text, or Hugging Face Hub

## Key Phonological Features

### Levantine Consonant Changes (from MSA)

| MSA | MSA Sound | Levantine | Levantine Sound |
|-----|-----------|-----------|-----------------|
| ق (qaf) | q | → | ' (glottal stop) in urban |
| ث (tha) | θ | → | s or t |
| ذ (dhal) | ð | → | d or z |
| ظ (dha) | ð̣ | → | z or d |

### Fixed Words Support

Common Levantine words with irregular pronunciations:
- Demonstratives: هادا (hada - this), هاي (hay - this), هادول (hadol - these)
- Pronouns: أنا (ana - I), إنتة (enta - you), هوه (huwwa - he), هيه (hiyye - she)
- Question words: شو (shu - what), ليش (leish - why), وين (wein - where)
- Particles: ما (ma - not), مو (mu - not), بس (bas - but/only)

## Installation

```bash
git clone https://github.com/yourusername/lev_phonetiser.git
cd lev_phonetiser
pip install -r requirements.txt
```

## Usage

### Python API

```python
from phonetiser.phonetise_levantine import phonetise, get_phonemes

# Get phonemes for a single word or phrase
text = "كيف حالك"
phonemes = get_phonemes(text)
print(phonemes)  # Output: k y f H aa l k

# Get all possible pronunciations
text = "هادا"
original, pronunciations = phonetise(text)
print(pronunciations[0])  # Output: ['h', 'aa', 'd', 'aa']

# Use urban vs rural dialect
from phonetiser.phonetise_levantine import LevantinePhonetiser

urban = LevantinePhonetiser(urban=True)  # qaf → '
rural = LevantinePhonetiser(urban=False)  # qaf → q

_, urban_prons = urban.phonetise("قال")
_, rural_prons = rural.phonetise("قال")
```

### Command Line - Batch Processing

Process a text file:
```bash
python3 run_levantine_phonetiser.py \
    --input_type text \
    --input_path examples/sample_levantine.txt \
    --output_type csv \
    --output_path output.csv
```

Process a CSV file:
```bash
python3 run_levantine_phonetiser.py \
    --input_type csv \
    --input_path input.csv \
    --column_id id \
    --column_text arabic_text \
    --output_type csv \
    --output_path phonemes.csv
```

Process a Hugging Face dataset:
```bash
python3 run_levantine_phonetiser.py \
    --input_type huggingface \
    --input_path "username/dataset-name" \
    --hf_text_column "text" \
    --output_type csv \
    --output_path phonemes.csv
```

Use rural dialect (preserve qaf):
```bash
python3 run_levantine_phonetiser.py \
    --input_type text \
    --input_path input.txt \
    --output_type csv \
    --output_path output.csv \
    --rural
```

### Run Tests

```bash
python3 test_phonetiser.py
```

## Project Structure

```
lev_phonetiser/
├── phonetiser/
│   ├── __init__.py                 # Package initialization
│   └── phonetise_levantine.py      # Main phonetiser module
├── examples/
│   └── sample_levantine.txt        # Example Levantine text
├── run_levantine_phonetiser.py     # Batch processing script
├── test_phonetiser.py              # Test suite
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Phoneme Notation

The phonetiser uses ASCII phoneme symbols:

| Symbol | IPA | Description |
|--------|-----|-------------|
| ' | ʔ | Glottal stop |
| b | b | Voiced bilabial plosive |
| t | t | Voiceless alveolar plosive |
| s | s | Voiceless alveolar fricative |
| $ | ʃ | Voiceless postalveolar fricative (sh) |
| S | sˁ | Voiceless alveolar emphatic fricative |
| D | dˁ | Voiced alveolar emphatic plosive |
| T | tˁ | Voiceless alveolar emphatic plosive |
| E | ʕ | Voiced pharyngeal fricative (ayin) |
| H | ħ | Voiceless pharyngeal fricative (ha) |
| x | x | Voiceless velar fricative (kh) |
| g | ɣ | Voiced velar fricative (ghayn) |
| q | q | Voiceless uvular plosive (qaf) |
| aa | aː | Long a |
| ii | iː | Long i |
| uu | uː | Long u |

## Dialect Options

### Urban Levantine (default)
- ق (qaf) → ' (glottal stop)
- Simplified feminine endings

### Rural Levantine
- ق (qaf) → q (preserved)
- Optional: preserve feminine endings

Use `--rural` flag or `LevantinePhonetiser(urban=False)`

## Limitations

1. **Diacritics**: Input should be diacritized for best results
2. **Context**: Some words require context for accurate phonetisation
3. **Regional variation**: Levantine has sub-dialects that may vary
4. **MSA borrowings**: Some formal/religious terms may retain MSA pronunciation

## Comparison with MSA Phonetiser

This phonetiser is based on the [MSA phonetiser](https://github.com/nawarhalabi/Arabic-Phonetiser) by Nawar Halabi, with adaptations for Levantine phonology:

| Feature | MSA Phonetiser | Levantine Phonetiser |
|---------|----------------|---------------------|
| qaf (ق) | q | ' (urban) or q (rural) |
| tha (ث) | θ (theta) | s |
| dhal (ذ) | ð (eth) | z |
| dha (ظ) | ð̣ (emphatic eth) | z |
| Fixed words | MSA-specific | Levantine-specific |
| Vowel reduction | MSA patterns | Levantine patterns |

## Acknowledgments

- Based on [nawarhalabi/Arabic-Phonetiser](https://github.com/nawarhalabi/Arabic-Phonetiser)
- Inspired by [MSA_phonetiser](https://github.com/Iqra-Eval/MSA_phonetiser)

