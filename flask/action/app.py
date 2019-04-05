from flask import Flask, jsonify, abort, make_response, request
from flask_cors import CORS

api = Flask(__name__)
CORS(api)

import os
import sys
from pathlib import Path

ROOT_NUM = 1
BASEDIR = str(Path(__file__).resolve().parents[ROOT_NUM].absolute())
modules_path = str(BASEDIR / Path("modules"))
sys.path.append(modules_path)

import jumanpp_manager as jpm

jpp = jpm.Jumanpp()

@api.route('/parse', methods=['GET'])
def parse():
    try:
        text = request.args.get('text')
        text = jpp.parse_text(text)

        hash = {
            'text': text
        }

    except Exception as e:
        print(e)
        hash = {
            'error': str(e)
        }

    return make_response(jsonify(hash))

@api.route('/count', methods=['GET'])
def count():
    try:
        text = request.args.get('text')
        sentence_type = request.args.get('sentence_type')
        eliminate_subtype = request.args.get('eliminate_subtype')
        text,e = jpp.count_text(text=text,sentence_type=sentence_type,eliminate_subtype=eliminate_subtype)
        # text = jpp.count_text(text=text, sentence_type=sentence_type)

        text = [{'text': t[0], 'value': t[1] * 1000} for t in text]

        hash = {
            'text': text,
            'e':e
        }

    except Exception as e:
        print(e)
        hash = {
            'error': str(e),
            'e':e
        }

    return make_response(jsonify(hash))



if __name__ == '__main__':
    api.run(host='0.0.0.0', port=5000, debug=True)