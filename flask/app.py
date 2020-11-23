from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://db:27017')
db = client.SimilarityDB
users = db['Users']


def user_exists(username):
    if users.find({'Username': username}).count() == 1:
        return True
    else:
        return False


def verify_pw(username, password):
    if not user_exists(username):
        return False

    hashed_pw = users.find({
        'Username': username
    })[0]['Password']

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False


def count_tokens(username):
    tokens = users.find({
        'Username': username
    })[0]['Tokens']

    return tokens


class Register(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']

        if user_exists(username):
            ret_json = {
                'status': 301,
                'message': 'Invalid user'
            }
            return jsonify(ret_json)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            'Username': username,
            'Password': hashed_pw,
            'Tokens': 6
        })

        ret_json = {
            'status': 200,
            'message': 'Successfully signed up for the API'
        }
        return jsonify(ret_json)


class Detect(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        text1 = posted_data['text1']
        text2 = posted_data['text2']

        if not user_exists(username):
            ret_json = {
                'status': 301,
                'message': 'Invalid user'
            }
            return jsonify(ret_json)

        if not verify_pw(username, password):
            ret_json = {
                'status': 302,
                'message': 'Invalid password'
            }
            return jsonify(ret_json)

        current_tokens = count_tokens(username)

        if current_tokens <= 0:
            ret_json = {
                'status': 303,
                'message': 'Not enough tokens!'
            }
            return jsonify(ret_json)

        nlp = spacy.load('en_core_web_sm')
        text1 = nlp(text1)
        text2 = nlp(text2)
        ratio = text1.similarity(text2)

        ret_json = {
            'status': 200,
            'ratio': ratio,
            'message': 'Similarity calculated'
        }

        users.update({
            'Username': username
        },{
            '$set': {'Tokens': current_tokens - 1}
        })

        return jsonify(ret_json)


class Refill(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['admin_pw']
        refill_amount = posted_data['refill_amount']

        if not user_exists(username):
            ret_json = {
                'status': 301,
                'message': 'Invalid user'
            }
            return jsonify(ret_json)

        correct_pw = 'abc123'
        if not password == correct_pw:
            ret_json = {
                'status': 304,
                'message': 'Invalid admin password'
            }
            return jsonify(ret_json)

        # current_tokens = count_tokens(username)
        users.update({
            'Username': username
        }, {
            '$set': {
                'Tokens': refill_amount
            }
        })

        ret_json = {
            'status': 200,
            'message': 'Refilled successfully'
        }

        return jsonify(ret_json)


api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
