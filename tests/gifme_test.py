from plugins import gifme

# i really just wanted to test the regex
# >_>


def test_regex_matches_good():
    test_phrases = {
        'glados gif me mana': 'mana',
        'glados, gif me multiple words': 'multiple words',
        'glados, giff me something': 'something',
        'glados giff me something else': 'something else',
        'glados giff no me': 'no me',
        'glados  gif   me   people who suck at spacing': 'people who suck at spacing',
        'glados gif me': 'me'
    }

    for phrase, output in test_phrases.items():
        match = gifme.query_re.match(phrase)
        assert match
        assert match.group(1) == output


def test_regex_does_not_match_bad():
    bad_phrases = [
        'giff mana',
        'glados giff',
        'glados gif',
        'glados',
        'glados potato'
    ]

    for phrase in bad_phrases:
        assert not gifme.query_re.match(phrase)
