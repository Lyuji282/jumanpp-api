import requests as req
import ast
from collections import defaultdict
from pprint import pprint


class Jumanpp:
    def __init__(self):
        pass

    def pretty_text(self, text):
        eliminate_list = [
            " ",
            "　",
            "\n",
            "（",
            "）",
            "ゝ"
        ]
        for el in eliminate_list:
            text = text.replace(el, "")
        return text

    def parse_text(self, text="私は猫", endpoint="parse"):
        try:
            text = self.pretty_text(text)
            res = req.post(f"http://app:4567/{endpoint}", params={"string": text})
            res = res.content.decode()
            res = ast.literal_eval(res)
            return res
        except Exception as e:
            return str(e)

    def count_text(self, text="森、それ、金、海,金",
                   sentence_type=['名詞'],
                   eliminate_subtype=['数詞'],
                   is_sort=True,
                   is_descending=True,
                   least_count=0):
        try:
            e = self.parse_text(text=text, endpoint="parse")
            res = e

            if sentence_type is None:
                sentence_type = ['名詞']

            if sentence_type == "all":
                target_clauses = [r[0] for r in res['results'] if r[3] not in eliminate_subtype]
            else:
                target_clauses = [r[0] for r in res['results'] if
                                  r[3] in sentence_type and r[3] not in eliminate_subtype]

            res = self.parse_text(text=text, endpoint="split")['results']
            res = [r for r in res if r in target_clauses and len(r) > least_count]

            d = defaultdict(int)
            for r in res:
                d[r] += 1
            d = dict(d)
            if is_sort:
                d = sorted(d.items(), key=lambda x: x[1], reverse=is_descending)
            return d,e
        except Exception as e:
            return str(e)
