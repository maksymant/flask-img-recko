from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
from utils.utils import user_exists, user_cash, user_debt, generate_ret_json, verify_creds, update_account,\
    update_debt
import bcrypt


app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://db:27017')
db = client.BankAPI
users = db.Users


class Register(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']

        if user_exists(username, users):
            ret_json = {
                'status': 301,
                'message': 'Invalid Username'
            }

            return jsonify(ret_json)

        hashed_pw = bcrypt.hashpw(password.encode('utf'), bcrypt.gensalt())

        users.insert_one({
            'Username': username,
            'Password': hashed_pw,
            'Own': 0,
            'Debt': 0
        })

        ret_json = {
            'status': 200,
            'message': 'Successfully signed up'
        }
        return jsonify(ret_json)


class Add(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        money = posted_data['amount']

        ret_json, error = verify_creds(username, password, users)

        if error:
            return jsonify(ret_json)

        if money <= 0:
            return jsonify(generate_ret_json(304, 'Money amount must be > 0'))

        cash = user_cash(username, users)
        bank_cash = user_cash('Bank', users)
        update_account('Bank', bank_cash + 1, users)  # +/- 1 fee for using Add
        update_account(username, cash + money - 1, users)

        return jsonify(generate_ret_json(200, 'Money has been added'))


class Transfer(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        money = posted_data['amount']
        to = posted_data['to']

        ret_json, error = verify_creds(username, password, users)
        if error:
            return jsonify(ret_json)

        cash = user_cash(username, users)
        if cash <= 0:
            return jsonify(generate_ret_json(304, 'Out of money. Add or take a loan'))

        if not user_exists(to, users):
            return jsonify(generate_ret_json(301, 'Recipient username does not exist'))

        cash_to = user_cash(to, users)
        cash_bank = user_cash('Bank', users)

        update_account('Bank', cash_bank + 1, users)
        update_account(to, cash_to + money - 1, users)
        update_account(username, cash - money, users)

        return jsonify(generate_ret_json(200, 'Amount transferred successfully'))


class Balance(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']

        ret_json, error = verify_creds(username, password, users)
        if error:
            return jsonify(ret_json)

        ret_json = users.find_one({
            'Username': username
        }, {
            'Password': 0,
            '_id': 0
        })

        return jsonify(ret_json)


class TakeLoan(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        money = posted_data['amount']

        ret_json, error = verify_creds(username, password, users)
        if error:
            return jsonify(ret_json)

        cash = user_cash(username, users)
        debt = user_debt(username, users)

        update_account(username, cash + money, users)
        update_debt(username, debt + money, users)

        return jsonify(generate_ret_json(200, 'Loan added to your account'))


class PayLoan(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        money = posted_data['amount']

        ret_json, error = verify_creds(username, password, users)
        if error:
            return jsonify(ret_json)

        cash = user_cash(username, users)
        debt = user_debt(username, users)

        if cash < money:
            return jsonify(generate_ret_json(303, 'Not enough cash in you account'))

        update_account(username, cash - money, users)
        update_debt(username, debt - money, users)

        return jsonify(generate_ret_json(200, 'Debt reduced'))


api.add_resource(Register, '/register')
api.add_resource(Add, '/add')
api.add_resource(Transfer, '/transfer')
api.add_resource(Balance, '/balance')
api.add_resource(TakeLoan, '/takeloan')
api.add_resource(PayLoan, '/payloan')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
