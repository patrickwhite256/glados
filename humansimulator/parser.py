import html
import os.path
import re
import sys
from collections import defaultdict

LINE_RE   = re.compile(r'\[\d+:\d+:\d+\] (\w+): (.*)', re.I)
UPLOAD_RE = re.compile(r'<@\w+\|\w+> uploaded a file', re.I)
JOINED_RE = re.compile(r'<@\w+\|\w+> has joined the channel', re.I)
PINNED_RE = re.compile(r'<@\w+\|\w+> pinned', re.I)
LEFT_RE   = re.compile(r'<@\w+\|\w+> has left the channel', re.I)
TOPIC_RE  = re.compile(r'<@\w+\|\w+> set the channel', re.I)
LINK_RE   = re.compile(r'<http.*>', re.I)
NAME_RE   = re.compile(r'<@\w+>', re.I)
CHARS_RE  = re.compile(r'([!?.]+|[<>;/&+-,])', re.I)
GROUP_RE  = re.compile(r'<!.*>')
QUOTES_RE = re.compile(r'(^["\'])|(["\']$)')


def corpus_directories(corpus_dir, whitelist):
    '''
    returns a generator that yields full pathnames
    '''
    if os.path.isabs(corpus_dir):
        corpus_path = corpus_dir
    else:
        corpus_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   corpus_dir)
    for path in os.listdir(corpus_path):
        dir_path = os.path.join(corpus_path, path)
        if not os.path.isdir(dir_path):
            continue
        if not whitelist or path in whitelist:
            yield dir_path


def corpus_filenames(corpus_dir, whitelist=None):
    '''
    returns a generator that yields filenames of non-empty files in the corpus
    '''
    for path in corpus_directories(corpus_dir, whitelist):
        for filename in os.listdir(path):
            full_path = os.path.join(path, filename)
            if os.stat(full_path).st_size > 0:
                yield full_path


def ignored(message):
    for ignore_re in [UPLOAD_RE, JOINED_RE, LEFT_RE, TOPIC_RE]:
        if ignore_re.match(message):
            return True
    return False


def parse_file(path):
    lines = defaultdict(list)
    with open(path) as corpus_file:
        for line in corpus_file:
            res = LINE_RE.match(line)
            if not res:
                # TODO: this is a continuation of the previous line
                # don't just ignore it
                continue
            username = res.group(1)
            if username == 'glados':
                continue
            message = res.group(2)
            if ignored(message):
                continue
            tokens = tokenize_line(message)
            if len(tokens) > 1:
                lines[username].append(tokens)
    return lines


def parse_corpus(config):
    lines = defaultdict(list)
    for path in corpus_filenames(config['corpus_dir'], config['whitelist']):
        line_map = parse_file(path)
        for username, token_lists in line_map.items():
            lines[username] += token_lists
    return lines


def tokenize_line(line):
    tokens = []
    line = html.unescape(line).lower()
    line = LINK_RE.sub('', line)
    line = NAME_RE.sub('', line)
    line = GROUP_RE.sub('', line)
    line = CHARS_RE.sub(r' \1 ', line)
    for token in re.split(r'\s', line):
        token = QUOTES_RE.sub('', token)
        if token:
            tokens.append(token)
    return tokens
