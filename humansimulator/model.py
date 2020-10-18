import random
import re
import sys

import yaml

import humansimulator.parser as parser

BEGINNING_OF_SENTENCE = object()
END_OF_SENTENCE       = object()

PHRASE_ENDER_RE = re.compile(r'\s+([,!?.;])')


class MarkovModel(object):
    def __init__(self, name):
        self.name = name
        self.token_map = {}
        self.token_totals = {}

    def add_line(self, line):
        prev_token = BEGINNING_OF_SENTENCE
        for token in line:
            self.add_pair(prev_token, token)
            prev_token = token
        self.add_pair(prev_token, END_OF_SENTENCE)

    def add_pair(self, first, second):
        if first not in self.token_map:
            self.token_map[first] = {}
            self.token_totals[first] = 0
        if second not in self.token_map[first]:
            self.token_map[first][second] = 0
        self.token_map[first][second] += 1
        self.token_totals[first] += 1

    def get_next_token(self, token):
        value = random.randint(0, self.token_totals[token])
        tokens = list(self.token_map[token].items())
        random.shuffle(tokens)
        for second, frequency in tokens:
            value -= frequency
            if value <= 0:
                return second

    def get_sentence(self):
        tokens = []
        token = self.get_next_token(BEGINNING_OF_SENTENCE)
        while token is not END_OF_SENTENCE:
            tokens.append(token)
            token = self.get_next_token(token)
        sentence = ' '.join(tokens)
        sentence = PHRASE_ENDER_RE.sub(r'\1', sentence)
        return sentence

    def merge(self, other):
        for first, value_map in other.token_map.items():
            if first not in self.token_map:
                self.token_map[first] = {}
                self.token_totals[first] = 0
            for second, value in value_map.items():
                if second not in self.token_map[first]:
                    self.token_map[first][second] = 0
                self.token_map[first][second] += value
            self.token_totals[first] += other.token_totals[first]


class ModelSet(object):
    def __init__(self):
        self.models = {}

    def add_model(self, model):
        self.models[model.name] = model

    def delete_model(self, name):
        try:
            del self.models[name]
        except KeyError:
            pass

    def merge(self, first_name, second_name):
        first_model = self.models.get(first_name)
        if not first_model:
            return
        first_model.merge(self.models[second_name])
        del self.models[second_name]

    def get_sentence(self, username):
        if username in self.models:
            return self.models[username].get_sentence()
        return None

    @classmethod
    def from_config(cls, filename):
        with open(filename) as ifile:
            config = yaml.load(ifile.read())

        model_set = cls()

        initial_data = parser.parse_corpus(config)
        for username, lines in initial_data.items():
            model = MarkovModel(username)
            for line in lines:
                model.add_line(line)
            model_set.add_model(model)

        for name, aliases in config['merges'].items():
            for alias in aliases:
                model_set.merge(name, alias)
        for name in config['deletes']:
            model_set.delete_model(name)

        return model_set


def main():
    models = ModelSet.from_config('config.yaml')

    for model in models.models.values():
        print('{}: {}'.format(model.name, model.get_sentence()))

if __name__ == '__main__':
    sys.exit(main())
