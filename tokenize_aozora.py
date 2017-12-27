from janome.tokenizer import Tokenizer
import urllib.request
import zipfile
import tempfile
import os
from abc import ABCMeta, abstractmethod
import re

class Task:
    processes = []
    def process(self, process):
        self.processes.append(process)
        return self
    
    def run(self, init):
        for p in self.processes:
            init = p.apply(init)
        return init


class Process(metaclass=ABCMeta):
    @abstractmethod
    def apply(self, init):
        pass

class DownloadAozora(Process):
    
    def __init__(self, aozora_text):
        self.aozora_text = aozora_text
    
    def apply(self, init):
        localfile = self.aozora_text.filename()
        if not os.path.exists(localfile):
            #download
            print('downloading')
            urllib.request.urlretrieve(self.aozora_text.url(), localfile)
        #unzip
        with zipfile.ZipFile(localfile, 'r') as zip_fp:
            for entry in zip_fp.infolist():
                if entry.filename.find('.txt') > 0:
                    with zip_fp.open(entry.filename, 'r') as fp:
                        text = fp.read().decode('shift_jis')
                        text = re.split(r'\-{5,}',text)[2]
                        text = re.split(r'底本：',text)[0]
                        return text.strip().split('\r\n')
        raise Exception('No text file found in {0}'.format(self.url))


class TokenCounter(Process):
    
    def __init__(self, tokenizer, filter):
        self.tokenizer = tokenizer
        self.filter = filter
    
    def apply(self, lines):
        counts = {}
        for line in lines:
            for token in self.tokenizer.tokenize(line):
                if self.filter(token):
                    counts[token.surface] = counts.get(token.surface, 0) + 1
        return counts

def noun_filter(token):

    def is_h(title):
        a =   [ch for ch in title if "あ" <= ch <= "ん"]
        if len(title) == len(a):
            return True
        return False
    return token.part_of_speech.find('名詞') >= 0 and not is_h(token.surface)

class SortByFreq(Process):
    
    def __init__(self, limit, desc=True):
        self.limit = limit
        self.desc = desc
    
    def apply(self, worddic):
        keys = sorted(worddic.items(),key = lambda x:x[1], reverse=self.desc)
        return [(word, cnt) for word,cnt in keys[:self.limit]]

DATASET = {
        'At the Mountains of Madness': 'http://www.aozora.gr.jp/cards/001699/files/57858_ruby_59671.zip'
}
    
class DataSet:
    
    def __init__(self, url):
        self.url = url

    @staticmethod
    def get(key):
        return DataSet(DATASET[key])
    
    def filename(self):
        return self.url.split('/')[-1]
    
    def url(self):
        return self.url