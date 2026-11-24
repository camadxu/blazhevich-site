"""Content regressions for the school biographies (stdlib only)."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Nodes(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'text': ''}
        self.nodes.append(node)
        if tag not in {'br', 'hr', 'img', 'meta', 'link', 'input', 'source', 'wbr'}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]['tag'] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node['text'] += data


def read(relative):
    return (ROOT / relative).read_text(encoding='utf-8')


def parse(relative):
    parser = Nodes()
    parser.feed(read(relative))
    return parser.nodes


class SchoolProfiles(unittest.TestCase):
    def test_malyukh_is_one_attributed_note_not_a_personal_chapter(self):
        source = read('src/ru/schools.html')
        matches = [node for node in parse('src/ru/schools.html')
                   if node['attrs'].get('id') == 'malyukh']
        self.assertEqual(len(matches), 1)
        note = matches[0]
        self.assertEqual(note['tag'], 'p')
        self.assertIn('note', note['attrs'].get('class', '').split())
        self.assertIn('Коршунов', note['text'])
        self.assertIn('По сведениям владельца сайта', note['text'])
        self.assertLess(len(note['text']), 350)
        self.assertNotIn('Вне двух столиц', source)
        self.assertNotIn('Брассиссимо', source)

    def test_batashev_honoured_title_is_linked_in_both_school_summaries(self):
        for relative, name, title in (
            ('src/ru/schools.html', 'Виктор Борисович Баташёв', 'заслуженный артист'),
            ('src/en/page.html', 'Viktor Borisovich Batashev', 'Honoured Artist'),
        ):
            with self.subTest(page=relative):
                notes = [node for node in parse(relative)
                         if node['tag'] == 'p' and name in node['text']
                         and title in node['text']]
                self.assertTrue(notes, 'the short school summary must distinguish the title')
                self.assertIn('https://www.mosconsv.ru/ru/eventdet/120631', read(relative))

    def test_verified_school_facts_are_sourced_in_both_languages(self):
        decrees = ('/acts/bank/24274', '/acts/bank/11005', '/acts/bank/21144')
        for language, schools, moscow, piguzov, title in (
            ('ru', 'src/ru/schools.html', 'src/ru/moscow.html', 'Пигузов',
             'Заслуженный работник культуры РСФСР'),
            ('en', 'src/en/page.html', 'src/en/moscow.html', 'Piguzov',
             'Honoured Cultural Worker of the RSFSR'),
        ):
            with self.subTest(language=language):
                school_source = read(schools)
                for decree in decrees:
                    self.assertIn(decree, school_source)
                piguzov_nodes = [node for node in parse(moscow)
                                 if node['tag'] in {'li', 'article'}
                                 and piguzov in node['text'] and '1964' in node['text']]
                self.assertTrue(piguzov_nodes, 'documented graduation must replace the old gap')
                for source in (school_source, read(moscow)):
                    self.assertIn('/acts/bank/505/print', source)
                    self.assertIn(title, source)
                    self.assertIn('gudi1991.ucoz.ru/', source)
        self.assertNotIn('Окончание консерватории, класс в училище', read('src/ru/moscow.html'))
        self.assertNotIn('списки народных артистов РФ (Турусин', read('src/ru/moscow.html'))


if __name__ == '__main__':
    unittest.main()
