# -*- coding: utf-8 -*-
"""
Levantine Arabic Phonetiser
============================
A rule-based phonetiser for Levantine Arabic dialects (Lebanese, Syrian, Jordanian, Palestinian)

Based on the MSA phonetiser by Nawar Halabi, adapted for Levantine phonological rules.
"""

import re
import sys
from typing import List, Tuple, Dict, Optional, Union


class LevantinePhonetiser:
    """
    Levantine Arabic Phonetiser class.

    Handles the conversion of Arabic text to phonetic representations
    following Levantine dialect phonological rules.
    """

    #==========================================================================
    # LEVANTINE CONSONANT MAPPINGS
    #==========================================================================

    # Unambiguous consonants with their phoneme mappings
    # Key differences from MSA:
    # - ق (qaf) → ' (glottal stop) in urban dialects
    # - ث (tha) → s (in most contexts) or t
    # - ذ (dhal) → d or z
    # - ظ (dha) → z or d
    unambiguousConsonantMap = {
        u'\u0628': u'b',   # ب
        u'\u062a': u't',   # ت
        u'\u062b': u's',   # ث → s (Levantine: MSA θ → s)
        u'\u062c': u'j',   # ج
        u'\u062d': u'H',   # ح
        u'\u062e': u'x',   # خ
        u'\u062f': u'd',   # د
        u'\u0630': u'z',   # ذ → z (Levantine: MSA ð → z)
        u'\u0631': u'r',   # ر
        u'\u0632': u'z',   # ز
        u'\u0633': u's',   # س
        u'\u0634': u'$',   # ش
        u'\u0635': u'S',   # ص
        u'\u0636': u'D',   # ض
        u'\u0637': u'T',   # ط
        u'\u0638': u'z',   # ظ → z (Levantine: MSA ã → z)
        u'\u0639': u'E',   # ع
        u'\u063a': u'g',   # غ
        u'\u0641': u'f',   # ف
        u'\u0642': u"'",   # ق → ' (Levantine: MSA q → glottal stop)
        u'\u0643': u'k',   # ك
        u'\u0645': u'm',   # م
        u'\u0646': u'n',   # ن
        u'\u0647': u'h',   # ه
        # Hamza variations
        u'\u0623': u"'",   # أ
        u'\u0621': u"'",   # ء
        u'\u0626': u"'",   # ئ
        u'\u0624': u"'",   # ؤ
        u'\u0625': u"'",   # إ
    }

    # Ambiguous consonants (context-dependent)
    ambiguousConsonantMap = {
        u'\u0644': [u'l', u''],      # ل - can be omitted in definite article
        u'\u0648': u'w',             # و
        u'\u064a': u'y',             # ي
        u'\u0629': [u't', u''],      # ة - context-dependent
    }

    #==========================================================================
    # VOWEL MAPPINGS
    #==========================================================================

    # Vowel mappings with emphatic/non-emphatic variants
    # Levantine has different vowel reduction patterns
    vowelMap = {
        u'\u0627': [[u'aa', u''], [u'AA', u'']],  # ا - long alif
        u'\u0649': [[u'aa', u''], [u'AA', u'']],  # ى - alif maqsura
        u'\u0648': [[u'uu', u''], [u'UU', u'']],  # و - waw
        u'\u064a': [[u'ii', u''], [u'II', u'']],  # ي - ya
        u'\u064e': [u'a', u'A'],  # fatHa
        u'\u064f': [u'u', u'U'],  # Damma
        u'\u0650': [u'i', u'I'],  # kasra
    }

    # Madda (آ) mappings
    maddaMap = {
        u'\u0622': [[u"'", u'aa'], [u"'", u'AA']]
    }

    # Nunation (tanwin) - mostly not used in Levantine except in MSA borrowings
    nunationMap = {
        u'\u064b': [[u'a', u'n'], [u'A', u'n']],  # fatHatayn
        u'\u064c': [[u'u', u'n'], [u'U', u'n']],  # Dammatan
        u'\u064d': [[u'i', u'n'], [u'I', u'n']],  # kasratayn
    }

    #==========================================================================
    # DIACRITICS AND SPECIAL CHARACTERS
    #==========================================================================

    diacritics = [u'\u0652', u'\u064e', u'\u064f', u'\u0650',  # sukun, fatHa, Damma, kasra
                  u'\u064b', u'\u064c', u'\u064d', u'\u0651']    # tanwin, shadda

    diacriticsWithoutShadda = [u'\u0652', u'\u064e', u'\u064f', u'\u0650',
                                u'\u064b', u'\u064c', u'\u064d']

    # Emphatic consonants (affect neighboring vowels)
    emphatics = [u'\u0636', u'\u0635', u'\u0637', u'\u0638',  # D, S, T, Z (z in Levantine)
                 u'\u063a', u'\u062e', u'\u0642']

    # All consonants for reference
    consonants = [u'\u0623', u'\u0625', u'\u0626', u'\u0624', u'\u0621',  # hamza variants
                  u'\u0628', u'\u062a', u'\u062b', u'\u062c', u'\u062d',   # b, t, th, j, H
                  u'\u062e', u'\u062f', u'\u0630', u'\u0631', u'\u0632',   # x, d, dh, r, z
                  u'\u0633', u'\u0634', u'\u0635', u'\u0636', u'\u0637',   # s, sh, S, D, T
                  u'\u0638', u'\u0639', u'\u063a', u'\u0641', u'\u0642',   # z, E, g, f, q
                  u'\u0643', u'\u0644', u'\u0645', u'\u0646', u'\u0647',   # k, l, m, n, h
                  u'\u0629', u'\u0627']                                   # t, a

    #==========================================================================
    # LEVANTINE FIXED WORDS DICTIONARY
    #==========================================================================
    # Common Levantine words with their pronunciations
    # These words have irregular or fixed pronunciations that override rules

    fixedWords = {
        # Demonstratives
        u'\u0647\u0627\u062f\u0627': [u"h aa d a"],             # hada
        u'\u0647\u0627\u062f\u064a': [u"h aa d i"],             # hadi
        u'\u0647\u0627\u062f\u0648\u0644': [u"h aa d o l"],     # hadol
        u'\u0647\u0627\u064a': [u"h ay"],                       # hay
        
        # Pronouns
        u'\u0627\u0646\u0627': [u"' a n a"],                    # ana
        u'\u0627\u0646\u062a\u0647': [u"' a n t e"],            # ente
        u'\u0627\u0646\u062a\u064a': [u"' a n t i"],            # enti
        u'\u0647\u0648\u0647': [u"h u ww e"],                   # huwwe
        u'\u0647\u064a\u0647': [u"h i yy e"],                   # hiyye
        
        # Verbs & Particles (CORRECTED PRONUNCIATIONS)
        u'\u0628\u062f\u064a': [u"b i dd i"],                   # biddi (Corrected from b di)
        u'\u0634\u0648': [u"$ uu"],                             # shuu (Corrected from $u)
        u'\u0644\u064a\u0634': [u"l ei $"],                     # leish
        u'\u0648\u064a\u0646': [u"w ein"],                      # wein
        u'\u0645\u0648': [u"m uu"],                             # muu
        u'\u0628\u0633': [u"b a s"],                            # bas
        
        # Common
        u'\u0627\u0644\u0644\u0647': [u"' a ll a"],             # Allah
        u'\u064a\u0644\u0627': [u"y a ll a"],                   # Yalla
    }

    #==========================================================================
    # BUCKWALTER TRANSLITERATION
    #==========================================================================

    buckwalter = {
        u'\u0627': u'A', u'\u0628': u'b', u'\u062a': u't', u'\u062b': u'^',
        u'\u062c': u'j', u'\u062d': u'H', u'\u062e': u'x', u'\u062f': u'd',
        u'\u0630': u'*', u'\u0631': u'r', u'\u0632': u'z', u'\u0633': u's',
        u'\u0634': u'$', u'\u0635': u'S', u'\u0636': u'D', u'\u0637': u'T',
        u'\u0638': u'Z', u'\u0639': u'E', u'\u063a': u'g', u'\u0641': u'f',
        u'\u0642': u'q', u'\u0643': u'k', u'\u0644': u'l', u'\u0645': u'm',
        u'\u0646': u'n', u'\u0647': u'h', u'\u0648': u'w', u'\u064a': u'y',
        u'\u0622': u'|', u'\u0623': u'>', u'\u0621': u"'", u'\u0626': u'}',
        u'\u0624': u'&', u'\u0625': u'<', u'\u0629': u'p',
        u'\u064b': u'F', u'\u064c': u'N', u'\u064d': u'K', u'\u064e': u'a',
        u'\u064f': u'u', u'\u0650': u'i', u'\u0651': u'~', u'\u0652': u'o',
    }

    #==========================================================================
    # SPECIAL LEVANTINE RULES
    #==========================================================================

    # Words where qaf should NOT be converted to hamza
    # (MSA borrowings, religious terms, etc.)
    preserveQafWords = {
        u'\u0642\u0631\u0622\u0646',     # Quran
        u'\u0642\u062f\u0633',          # Quds (Jerusalem)
        u'\u0642\u0627\u0647\u0631',     # Cairo
        u'\u0627\u0644\u0642\u0627\u0647\u0631\u0629',  # Cairo (with article)
    }

    # Words where th/dh/dh should be preserved as MSA sounds
    preserveInterdentalWords = {
        u'\u062b\u0644\u0627\u062b',     # thawra (revolution) - sometimes preserved
        u'\u0627\u0633\u0645\u0627\u0639\u064a\u0644',  # Isma'il
        u'\u062e\u0627\u0644\u062f',     # Khalid
    }

    def __init__(self, urban: bool = True, simplify_feminine_endings: bool = True):
        """
        Initialize the Levantine phonetiser.

        Args:
            urban: If True, use urban dialect (qaf → hamza). If False, preserve qaf.
            simplify_feminine_endings: If True, simplify feminine plural endings.
        """
        self.urban = urban
        self.simplify_feminine_endings = simplify_feminine_endings

        # Create modified consonant map based on urban setting
        self.consonantMap = self.unambiguousConsonantMap.copy()
        if not urban:
            self.consonantMap[u'\u0642'] = u'q'  # Keep qaf in rural/bedouin

    def arabic_to_buckwalter(self, word: str) -> str:
        """Convert Arabic text to Buckwalter transliteration."""
        result = ''
        for letter in word:
            result += self.buckwalter.get(letter, letter)
        return result

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess Arabic text before phonetisation.

        Handles:
        - Tatweel removal
        - Diacritic normalization
        - Hamza normalization
        """
        # Remove tatweel (ـ)
        text = text.replace(u'\u0640', u'')

        # Normalize hamza forms
        text = text.replace(u'\u0627\u064b', u'\u064b')  # alif + fatHatayn
        text = text.replace(u'\u064e\u0627', u'\u0627')  # fatHa + alif → alif
        text = text.replace(u'\u064e\u0649', u'\u0649')  # fatHa + alif maqsura
        text = text.replace(u' \u0627', u' ')            # standalone alif

        # Convert nunation to vowel + nun
        text = text.replace(u'\u064b', u'\u064e\u0646')  # fatHatayn → fatHa + nun
        text = text.replace(u'\u064c', u'\u064f\u0646')  # Dammatan → Damma + nun
        text = text.replace(u'\u064d', u'\u0650\u0646')  # kasratayn → kasra + nun

        # Expand madda
        text = text.replace(u'\u0622', u'\u0623\u0627')

        return text

    def check_fixed_word(self, word: str, orthography: str) -> Optional[List[str]]:
        """
        Check if a word is in the fixed words dictionary.

        Returns list of pronunciations if found, None otherwise.
        """
        # Remove diacritics for lookup
        word_consonants = re.sub(u'[^\u0647\u0630\u0627\u0647\u0646\u0621\u0623\u0648\u0644\u0626\u0643\u0645\u064a\u0637\u062a\u0641\u062f\u0642\u0633\u0631\u0634\u0635\u0636\u0638\u0639\u063a\u0628\u062c\u062d\u062e\u062a\u062b]', u'', word)

        if word_consonants in self.fixedWords:
            pronunciations = self.fixedWords[word_consonants]
            if isinstance(pronunciations, list):
                return pronunciations
            else:
                return [pronunciations]
        return None

    def phonetise_word(self, word: str) -> List[str]:
        """
        Phonetically transcribe a single Arabic word.
        """
        if not word or word.strip() == u'-':
            return []

        original_word = word
        word = self.preprocess_text(word)
        orthography = self.arabic_to_buckwalter(word)

        # Check fixed words
        fixed = self.check_fixed_word(original_word, orthography)
        if fixed:
            return fixed

        # Sun letters for definite article assimilation
        sun_letters = [u'\u062a', u'\u062b', u'\u062f', u'\u0630',
                      u'\u0631', u'\u0632', u'\u0633', u'\u0634',
                      u'\u0635', u'\u0636', u'\u0637', u'\u0638',
                      u'\u0644', u'\u0646']

        # Pad word for lookahead/lookbehind
        # Use special padding that won't be confused with actual consonants
        word = u'xx' + word + u'zz'
        phones = []
        emphatic_context = False
        in_definite_article = False
        next_is_doubled = False  # For sun letter assimilation
        skip_next = False  # Skip shadda if already processed
        skip_next2 = False  # Skip second char (vowel before shadda)

        for index in range(2, len(word) - 2):
            # Skip this character if it was already processed as part of lookahead
            if skip_next:
                skip_next = False
                continue
            # Also skip if this is the second character to skip (vowel + shadda case)
            if skip_next2:
                skip_next2 = False
                continue

            letter = word[index]
            letter1 = word[index + 1]  # Next char
            letter2 = word[index + 2]  # Next next char
            letter_1 = word[index - 1]  # Prev char
            letter_2 = word[index - 2]  # Prev prev char

            # Check for definite article start (ال)
            if letter == u'\u0627' and letter1 == u'\u0644' and letter_2 == 'x':
                in_definite_article = True
                # Check if next letter (after lam) is a sun letter
                if index + 2 < len(word) - 2 and word[index + 2] in sun_letters:
                    next_is_doubled = True
                # In Levantine, definite article is "il" or "el"
                phones.append('i')
                continue  # Skip the alif, process lam next

            # Still in definite article - process lam
            if in_definite_article and letter == u'\u0644':
                if next_is_doubled:
                    # Sun letter: lam is silent, next letter will be doubled
                    phones.append('')
                else:
                    # Moon letter: lam is pronounced
                    phones.append('l')
                in_definite_article = False
                continue

            # Check for initial alif with short vowel (اَ اُ اِ إَ إُ إِ أَ أُ أِ)
            # These should be treated as hamza + vowel, skip the next diacritic
            if (letter in [u'\u0627', u'\u0623', u'\u0625'] and letter_2 == 'x' and
                letter1 in [u'\u064e', u'\u064f', u'\u0650']):
                phones.append("'")
                phones.append(self.vowelMap[letter1][0])  # Always use non-emphatic for initial
                skip_next = True
                continue

            # 1. Emphatic Spread Logic
            if letter in self.emphatics:
                emphatic_context = True
            elif letter in self.consonants and letter not in [u'\u0631', u'\u0644', u'\u0648', u'\u064a']:
                emphatic_context = False

            vowel_choice = 1 if emphatic_context else 0

            # 2. Handle Consonants (check for shadda AFTER the consonant)
            if letter in self.consonantMap:
                consonant = self.consonantMap[letter]
                # Check if there's a shadda after this consonant (may be after a vowel)
                # Shadda can be immediately after, or after a vowel diacritic
                has_shadda = (letter1 == u'\u0651') or (letter1 in self.diacriticsWithoutShadda and letter2 == u'\u0651')
                # Also need to skip the appropriate number of characters
                if has_shadda:
                    phones.append(consonant + consonant)
                    # Skip the shadda (and possibly the vowel before it)
                    if letter1 == u'\u0651':
                        skip_next = True
                    else:
                        skip_next = True
                        skip_next2 = True  # Will skip two characters
                elif next_is_doubled:
                    # Double the sun letter (from definite article)
                    phones.append(consonant + consonant)
                    next_is_doubled = False
                else:
                    phones.append(consonant)

            # Also handle ambiguous consonants (ل، و، ي) with shadda
            elif letter in self.ambiguousConsonantMap:
                consonant = self.ambiguousConsonantMap[letter]
                # Handle list values for ta marbuta
                if isinstance(consonant, list):
                    consonant = consonant[0]  # Use first value

                # Check if there's a shadda after this consonant
                has_shadda = (letter1 == u'\u0651') or (letter1 in self.diacriticsWithoutShadda and letter2 == u'\u0651')
                if has_shadda:
                    phones.append(consonant + consonant)
                    # Skip the shadda (and possibly the vowel before it)
                    if letter1 == u'\u0651':
                        skip_next = True
                    else:
                        skip_next = True
                        skip_next2 = True  # Will skip two characters
                else:
                    phones.append(consonant)

            # 3. Handle Shadda (Gemination) - skip if already processed
            elif letter == u'\u0651':
                # Shadda is handled when we process the consonant (lookahead)
                # If we encounter it here, it means the previous consonant didn't handle it
                # Check if previous phone exists and is a single consonant
                if phones and len(phones[-1]) == 1 and phones[-1] not in ['a', 'i', 'u', 'e', 'o', 'aa', 'ii', 'uu']:
                    # Double it
                    phones[-1] = phones[-1] + phones[-1]

            # 4. Handle Ta Marbuta
            elif letter == u'\u0629':
                if letter1 in self.diacritics or letter1 in self.vowelMap:
                    phones.append('t')
                else:
                    phones.append('a' if not self.simplify_feminine_endings else 'e')

            # 5. Handle Alif (Long Vowel)
            elif letter in [u'\u0627', u'\u0649']:
                # Skip initial alif with short vowel - already handled earlier
                if letter_2 == 'x' and letter1 in [u'\u064e', u'\u064f', u'\u0650']:
                    continue
                # If preceded by a vowel diacritic, it's part of diphthong or just alif
                elif letter_1 in self.vowelMap or letter_1 in [u'\u064e', u'\u064f', u'\u0650']:
                    phones.append(self.vowelMap[u'\u0627'][vowel_choice][0])
                else:
                    phones.append(self.vowelMap[u'\u0627'][vowel_choice][0])

            # 6. Handle Waw (و) and Ya (ي)
            elif letter in [u'\u0648', u'\u064a']:
                is_consonant = False
                handled = False  # Track if we've already added something

                # If start of word, it's a consonant (e.g., Wein, Yalla)
                if letter_2 == 'x':
                    is_consonant = True

                # If at end of word (before 'z' padding), it's NOT a long vowel - consonant only
                if letter1 == 'z':
                    phones.append(self.ambiguousConsonantMap[letter])
                    handled = True

                # If followed by shadda, it's doubled (e.g., huwwa)
                elif letter1 == u'\u0651':
                    consonant = self.ambiguousConsonantMap[letter]
                    phones.append(consonant + consonant)
                    skip_next = True
                    handled = True

                # If followed by alif, it's consonant + alif (consonant part only here)
                elif letter1 == u'\u0627':
                    phones.append(self.ambiguousConsonantMap[letter])
                    handled = True

                # If followed by a short vowel diacritic, it's consonant + that vowel
                elif letter1 in [u'\u064e', u'\u064f', u'\u0650']:
                    phones.append(self.ambiguousConsonantMap[letter])
                    handled = True  # The vowel will be processed next

                if is_consonant and not handled:
                    phones.append(self.ambiguousConsonantMap[letter])
                    handled = True

                # If acting as long vowel (uu or ii)
                if not handled and letter1 not in [u'\u0627', u'\u0651', u'\u064e', u'\u064f', u'\u0650', 'z']:
                    phones.append(self.vowelMap[letter][vowel_choice][0])

            # 7. Handle Short Vowels
            elif letter in [u'\u064e', u'\u064f', u'\u0650']:
                phones.append(self.vowelMap[letter][vowel_choice])

            # 8. Handle Hamza variants (أ إ ء ئ ؤ)
            elif letter in [u'\u0623', u'\u0625', u'\u0621', u'\u0626', u'\u0624']:
                # If followed by short vowel, add hamza + vowel
                if letter1 in [u'\u064e', u'\u064f', u'\u0650']:
                    phones.append("'")
                    phones.append(self.vowelMap[letter1][vowel_choice])
                else:
                    phones.append("'")

        return self._generate_pronunciations(phones)

    def _generate_pronunciations(self, phones: List) -> List[str]:
        """Generate all possible pronunciations from phones (which may contain alternatives)."""
        if not phones:
            return []

        # Count possibilities
        possibilities = 1
        for phone in phones:
            if isinstance(phone, list):
                possibilities *= len(phone)

        # Generate all combinations
        pronunciations = [[] for _ in range(possibilities)]
        iterations = 1

        for phone in phones:
            if isinstance(phone, list):
                for i in range(possibilities):
                    choice_idx = (i // iterations) % len(phone)
                    if phone[choice_idx] != '':
                        pronunciations[i].append(phone[choice_idx])
                iterations *= len(phone)
            else:
                if phone != '':
                    for pronunciation in pronunciations:
                        pronunciation.append(phone)

        # Post-process: remove duplicates and clean up
        cleaned_pronunciations = []
        for pronunciation in pronunciations:
            cleaned = self._clean_pronunciation(pronunciation)
            if cleaned and cleaned not in cleaned_pronunciations:
                cleaned_pronunciations.append(cleaned)

        return cleaned_pronunciations

    def _clean_pronunciation(self, pronunciation: List[str]) -> str:
        """Clean up a pronunciation by removing redundant elements."""
        if not pronunciation:
            return ''

        result = []
        for phone in pronunciation:
            if phone == '':
                continue
            # Handle doubled consonants (from shadda or sun letters)
            if len(phone) == 2 and phone[0] == phone[1]:
                result.append(phone)
            # Handle long vowels
            elif phone in ['aa', 'uu', 'ii', 'AA', 'UU', 'II']:
                result.append(phone)
            # Handle short vowels
            elif phone in ['u', 'i', 'a', 'U', 'I', 'A', 'e', 'o']:
                result.append(phone)
            # Handle single consonants
            else:
                result.append(phone)

        # Join and return
        return ' '.join(result)

    def phonetise(self, text: str) -> Tuple[str, List[str]]:
        """
        Phonetically transcribe Arabic text.

        Args:
            text: Arabic text to phonetise (should be diacritized for best results)

        Returns:
            Tuple of (original_text, list_of_phoneme_sequences)
        """
        if not text:
            return (text, [])

        # Split into words
        words = text.split()
        all_pronunciations = []

        for word in words:
            pronunciations = self.phonetise_word(word)
            if pronunciations:
                all_pronunciations.append(pronunciations)
            else:
                all_pronunciations.append([''])  # Empty for unrecognized

        # Combine pronunciations (take first option for each word)
        primary_pronunciation = []
        for word_pronunciations in all_pronunciations:
            if word_pronunciations:
                primary_pronunciation.append(word_pronunciations[0])

        return (text, all_pronunciations)


# Global instance and convenience function
_default_phonetiser = LevantinePhonetiser(urban=True)


def phonetise(text: str, urban: bool = True) -> Tuple[str, List[str]]:
    """
    Convenience function to phonetise Arabic text.

    Args:
        text: Arabic text to phonetise
        urban: If True, use urban dialect (qaf → hamza)

    Returns:
        Tuple of (original_text, list_of_proneme_sequences)

    Example:
        >>> phonetise("كيف حالك")
        ('كيف حالك', [['kiif', 'Haal', 'lak']])
    """
    phonetiser = LevantinePhonetiser(urban=urban)
    return phonetiser.phonetise(text)


def get_phonemes(text: str, urban: bool = True) -> str:
    """
    Get the primary phoneme sequence for Arabic text.

    Args:
        text: Arabic text to phonetise
        urban: If True, use urban dialect

    Returns:
        Space-separated phoneme string

    Example:
        >>> get_phonemes("البيت")
        "'al bayt"
    """
    _, pronunciations = phonetise(text, urban=urban)
    primary = []
    for word_prons in pronunciations:
        if word_prons:
            primary.append(word_prons[0])
    return ' '.join(primary)


if __name__ == '__main__':
    # Test examples
    test_words = [
        u'\u0643\u064a\u0641',      # kiif - how
        u'\u0627\u0644\u0628\u064a\u062a',  # al-bayt - the house
        u'\u0647\u0627\u062f\u0627',  # hada - this
        u'\u0628\u062f\u064a',       # biddi - I want
    ]

    print("Levantine Arabic Phonetiser - Test")
    print("=" * 50)
    for word in test_words:
        _, prons = phonetise(word)
        print(f"{word}: {prons[0] if prons else '(empty)'}")
