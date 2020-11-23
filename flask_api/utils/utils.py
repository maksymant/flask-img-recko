import bcrypt


def user_exists(username, users):
    if users.find({'Username': username}).count() == 1:
        return True
    else:
        return False


def verify_pw(username, password, users):
    hashed_pw = users.find_one({
        'Username': username
    })['Password']

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False


def user_cash(username, users):
    cash = users.find_one({
        'Username': username
    })['Own']

    return cash


def user_debt(username, users):
    debt = users.find_one({
        'Username': username
    })['Debt']

    return debt


def generate_ret_json(status, message):
    ret_json = {
        'status': status,
        'message': message
    }
    return ret_json


def verify_creds(username, password, users):
    if not user_exists(username, users):
        return generate_ret_json(301, 'Invalid Username'), True

    is_correct_pw = verify_pw(username, password, users)

    if not is_correct_pw:
        return generate_ret_json(302, 'Incorrect Password'), True

    return None, False


def update_account(username, balance, users):
    users.update_one({
        'Username': username
    }, {
        '$set': {
            'Own': balance
        }
    })


def update_debt(username, debt, users):
    users.update_one({
        'Username': username
    }, {
        '$set': {
            'Debt': debt
        }
    })
