from flask import Flask, request, render_template, jsonify, redirect, url_for
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

import os
from os.path import join, dirname
from dotenv import load_dotenv


app = Flask(__name__)

db_connect = 'mongodb+srv://alfasorahakbauw53:sparta@cluster0.vohunfz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(db_connect)

db = client.dbWish_list

@app.route ('/')
def home():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
        msg = request.args.get('msg')
    return render_template(
        'index.html',
        words=words,
        msg=msg
    )


@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = 'e3a916bf-fd4e-4023-b457-807e02006447'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        return redirect(url_for('error', msg=f'Kata "{keyword}" tidak ditemukan'))

    if type(definitions[0]) is str:
        saran = ', '.join(definitions)
        return redirect(url_for('error', msg=f'Kata "{keyword}" tidak ditemukan. Mungkin maksud Anda salah satu dari kata-kata ini: {saran}', suggested_words=saran))

    status = request.args.get('status_give', 'new')
    return render_template('detail.html', word=keyword, definitions=definitions, status=status)

@app.route('/error')
def error():
    error_message = request.args.get('msg')
    suggested_words = request.args.get('suggested_words', '').split(',')
    return render_template('error.html', error_message=error_message, suggested_words=suggested_words)

@app.route('/api/save_word', methods = ['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    tanggal = datetime.now().strftime('%Y-%m-%d')

    doc = {
        'word' : word,
        'definitions' : definitions,
        'date' : tanggal
    }

    db.words.insert_one(doc)

    return jsonify({
        'result' : 'success',
        'msg' : f'kata "{word}", berhasil tersimpan!',
    })

@app.route('/api/delete_word', methods = ['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word' : word})
    db.examples.delete_many({'word' : word})
    return jsonify({
        'result' : 'success',
        'msg' : f'kata {word} berhasil terhapus',
    })

@app.route('/api/get_ex', methods=['GET'])
def get_ex():
    word = request.args.get('word')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'id': str(example.get('_id')),
            'example': example.get('example'),
        })
    return jsonify({
        'result': 'success',
        'examples': examples
    })


@app.route('/api/save_ex', methods=['POST'])
def save_ex():
     word = request.form.get('word')
     example = request.form.get('example')
     doc = {
        'word' : word,
        'example' : example,
     }
     db.examples.insert_one(doc)
     return jsonify({
            'result' : 'success',
            'msg' : f'Contoh kalimat, {example}, untuk kata {word} telah tersimpan!'
        })

@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
     id = request.form.get('id')
     word = request.form.get('word')
     db.examples.delete_one({'_id' : ObjectId(id)})
     return jsonify({
        'result' : 'success',
        'msg' : f'contoh kalimat, {word}, telah terhapus! '
     })

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)