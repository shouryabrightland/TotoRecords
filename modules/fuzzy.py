from difflib import SequenceMatcher
from pathlib import Path

class fuzzy:


    def fuzzy_match(self,rawItem,list):
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


    def fuzzy_file_match(self,target_filename, directory="."):
        '''returns file list with match score'''
        directory = Path(directory)
        files = [f.name for f in directory.iterdir() if f.is_file()]

        return self.fuzzy_match(target_filename,files)
    