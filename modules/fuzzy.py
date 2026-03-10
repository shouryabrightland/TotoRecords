from difflib import SequenceMatcher
import re
from rapidfuzz import process, fuzz
from pathlib import Path
from metaphone import doublemetaphone


class fuzzy:

    STOP_WORDS = {
        "please","can","you","could","would","will",
        "the","a","an",
        "for","to","of","in","on","at",
        "me","my","mine",
        "is","are","was","were",
        "do","did","does",
        "kindly","may","might","shall","should",
        "and","but","or","if","then",
        "that","this","these","those",
        "he","she","it","they",
        "his","her","its","their",
        "as","by","with","about","into","through",
        "up","down","out","over","under",
        "also","just","only","even","really",
        "very","quite","so","such",
        "name",
    }


    def _clean_input(self, text):
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)

        words = text.split()
        words = [w for w in words if w not in self.STOP_WORDS]

        return " ".join(words)


    def _extract_target(self, text):
        words = text.split()
        if not words:
            return text
        return words[-1]


    def _phonetic(self, word):
        code1, code2 = doublemetaphone(word)
        return code1 or code2


    def fuzzy_match(self, raw_item, items, limit=10):

        cleaned = self._clean_input(raw_item)
        target = self._extract_target(cleaned)

        if not target:
            target = raw_item

        target = target.lower()
        target_code = self._phonetic(target)

        phonetic_scores = []

        # compute phonetic similarity
        for item in items:
            word = item.split()[0].lower()
            code = self._phonetic(word)

            score = fuzz.ratio(target_code, code)
            phonetic_scores.append((item, score))

        # sort by phonetic similarity
        phonetic_scores.sort(key=lambda x: x[1], reverse=True)

        # keep top 50%
        cutoff = max(1, len(phonetic_scores) // 2)
        candidates = [item for item, _ in phonetic_scores[:cutoff]]

        # final fuzzy ranking
        results = process.extract(
            target,
            candidates,
            scorer=fuzz.WRatio,
            limit=limit
        )

        return [(m, s/100) for m, s, _ in results if s >= 50]
    

    
    def fuzzy_file_match(self, target_filename, directory=".", limit=10):
        """
        Returns file list with match score
        """

        directory = Path(directory)

        files = [
            f.name
            for f in directory.iterdir()
            if f.is_file()
        ]

        return self.fuzzy_match(target_filename, files, limit)

    def fuzzy_match_basic(self,rawItem,list):
        ''' takes string and give match score from all elements from the array'''
        results = []
        for item in list:
            score = self.similarity_ratio(rawItem, item)
            results.append((item, score))
            # sort by highest similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def similarity_ratio(self,a, b):
        '''returns score of match'''
        return SequenceMatcher(None, a, b).ratio()

