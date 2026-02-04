#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Levantine Arabic Phonetiser
"""

import sys
from phonetiser.phonetise_levantine import phonetise, get_phonemes, LevantinePhonetiser


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def test_single_words():
    """Test phonetisation of single words."""
    print_section("Testing Single Words")

    test_words = [
        (u'بيت', 'house'),
        (u'كبير', 'big'),
        (u'صغير', 'small'),
        (u'شادر', 'tent / spreading'),
        (u'ماشاء', 'doing'),
        (u'عم', 'progressive marker'),
        (u'بدي', 'I want'),
        (u'بتي', 'you (f) want'),
        (u'بيع', 'he wants / selling'),
        (u'هادا', 'this (m)'),
        (u'هاي', 'this (f)'),
        (u'هاييه', 'this is'),
        (u'شو', 'what'),
        (u'ليش', 'why'),
        (u'وين', 'where'),
        (u'إيه', 'how'),
        (u'مو', 'not (copula)'),
        (u'بس', 'but / only'),
        (u'بكرا', 'tomorrow'),
        (u'الحين', 'now'),
        (u'زعلان', 'sad/angry (m)'),
        (u'زعلانة', 'sad/angry (f)'),
    ]

    print(f"{'Word':<20} {'Meaning':<25} {'Phonemes'}")
    print("-" * 60)

    for word, meaning in test_words:
        _, prons = phonetise(word)
        # Join phonemes for the word
        phoneme = ' '.join(prons[0]) if prons and prons[0] else '(empty)'
        print(f"{word:<20} {meaning:<25} {phoneme}")


def test_phrases():
    """Test phonetisation of common phrases."""
    print_section("Testing Common Phrases")

    test_phrases = [
        (u'كيف حالك', 'How are you (m)'),
        (u'كيف حالكي', 'How are you (f)'),
        (u'شو أخبارك', 'What\'s your news'),
        (u'الحمد لله', 'Thank God / Praise God'),
        (u'بخير', '(I am) fine'),
        (u'الحمد لله بخير', 'Praise God, (I am) fine'),
        (u'بدي إروح', 'I want to go'),
        (u'عالبيت', 'to the house'),
        (u'بدي إروح عالبيت', 'I want to go home'),
        (u'إيشرب القهوة', 'He drinks coffee'),
        (u'بالصباح', 'in the morning'),
        (u'إيشرب القهوة بالصباح', 'He drinks coffee in the morning'),
        (u'لسة بدك شيء', 'Do you still need something'),
        (u'عم بفكر', 'thinking / I am thinking'),
        (u'إذا بدك', 'if you want'),
        (u'خدها', 'take it (f)'),
        (u'ما بعرف', 'I don\'t know'),
        (u'شو اسمك', 'What is your name (m)'),
        (u'شو إسمكي', 'What is your name (f)'),
        (u'إسمي...', 'My name is...'),
        (u'فرصة سعيدة', 'Nice to meet you (opportunity happiness)'),
        (u'من وين إنت', 'Where are you from (m)'),
        (u'من وين إنتي', 'Where are you from (f)'),
        (u'أنا من...', 'I am from...'),
        (u'الله يعطيك العافية', 'God give you health (thank you)'),
        (u'هالقديم جديد', 'This old thing is new / familarity breeds contempt'),
    ]

    print(f"{'Phrase':<30} {'Meaning':<30} {'Phonemes'}")
    print("-" * 80)

    for phrase, meaning in test_phrases:
        phoneme = get_phonemes(phrase)
        # Truncate if too long
        display_phoneme = phoneme if len(phoneme) < 30 else phoneme[:27] + '...'
        print(f"{phrase:<30} {meaning:<30} {display_phoneme}")


def test_urban_vs_rural():
    """Test urban vs rural dialect differences."""
    print_section("Urban vs Rural Dialect Comparison")

    # Words where qaf is pronounced differently
    qaf_words = [
        (u'قلب', 'heart'),
        (u'قال', 'he said'),
        (u'قريب', 'near/close'),
        (u'بق/QAF', 'to stay'),
        (u'بقر', 'cows'),
    ]

    print(f"{'Word':<15} {'Urban (qaf→ʔ)':<25} {'Rural (qaf→q)'}")
    print("-" * 60)

    urban_phonetiser = LevantinePhonetiser(urban=True)
    rural_phonetiser = LevantinePhonetiser(urban=False)

    for word, meaning in qaf_words:
        _, urban_prons = urban_phonetiser.phonetise(word)
        _, rural_prons = rural_phonetiser.phonetise(word)

        urban_phoneme = ' '.join(urban_prons[0]) if urban_prons and urban_prons[0] else '(empty)'
        rural_phoneme = ' '.join(rural_prons[0]) if rural_prons and rural_prons[0] else '(empty)'

        print(f"{word:<15} {urban_phoneme:<25} {rural_phoneme}")


def test_msa_vs_levantine():
    """Compare MSA vs Levantine pronunciations."""
    print_section("MSA vs Levantine Comparison")

    # Words that differ between MSA and Levantine
    comparisons = [
        (u'ثلاثة', 'three', 'θalθaː', 'talate'),
        (u'ذاهب', 'going', 'ðaːhib', 'daahib'),
        (u'ظرف', 'condition/envelope', 'ðarf', 'zarf'),
        (u'قال', 'he said', 'qaːla', 'qaal / aal'),
        (u'هذا', 'this (m)', 'haːða', 'hada / hayda'),
    ]

    print(f"{'Word':<12} {'Meaning':<20} {'MSA':<15} {'Levantine'}")
    print("-" * 70)

    for word, meaning, msa, expected in comparisons:
        _, lev_prons = phonetise(word)
        lev = ' '.join(lev_prons[0]) if lev_prons and lev_prons[0] else '(empty)'
        print(f"{word:<12} {meaning:<20} {msa:<15} {lev}")


def test_fixed_words():
    """Test the fixed words dictionary."""
    print_section("Testing Fixed Words Dictionary")

    # Fixed words that should match dictionary entries
    fixed = [
        u'هادا', u'هاي', u'هادول', u'أنا', u'إنتة', u'إنتي',
        u'هوه', u'هيه', u'همه', u'هن', u'شو', u'ليش', u'وين',
        u'ما', u'مو', u'بس', u'ألحين', u'أليوم', u'بكرة',
    ]

    print(f"{'Word':<12} {'Phonemes'}")
    print("-" * 40)

    for word in fixed:
        _, prons = phonetise(word)
        phoneme = ' '.join(prons[0]) if prons and prons[0] else '(empty)'
        print(f"{word:<12} {phoneme}")


def test_from_file():
    """Test reading from file."""
    print_section("Testing from File (examples/sample_levantine.txt)")

    try:
        with open('examples/sample_levantine.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        print(f"Read {len(lines)} lines from file\n")
        print(f"{'Line':<35} {'Phonemes'}")
        print("-" * 60)

        for line in lines:
            phoneme = get_phonemes(line)
            display = phoneme if len(phoneme) < 30 else phoneme[:27] + '...'
            print(f"{line:<35} {display}")

    except FileNotFoundError:
        print("File not found: examples/sample_levantine.txt")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print(" Levantine Arabic Phonetiser - Test Suite")
    print("="*60)

    # Run tests
    test_single_words()
    test_phrases()
    test_urban_vs_rural()
    test_msa_vs_levantine()
    test_fixed_words()
    test_from_file()

    print_section("All Tests Complete")


if __name__ == '__main__':
    main()
