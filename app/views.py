import flask
from app import app
import database_methods


@app.route('/')
def index():
    flask.session['login_attempts'] = 0
    return flask.render_template("login.html")


@app.route('/', methods=['POST'])
def login_post():
    flask.session['message'] = None

    if flask.request.form['action'] == 'login_attempt':
        email = flask.request.form['email']
        post_password = flask.request.form['password']
        result = database_methods.login(email, post_password)

        if result:
            flask.session['message'] = None
            return flask.redirect('/home')
        else:
            if flask.session['login_attempts'] == 2:
                return flask.render_template('lockout.html')
            flask.session['login_attempts'] += 1
            flask.session['message'] = "Incorrect Information"
            return flask.render_template('login.html')
    else:
        return flask.redirect('/register')


@app.route('/register')
def register():
    return flask.render_template('register.html')


@app.route('/logout')
def log_out():
    flask.session.clear()
    return flask.redirect('/')


@app.route('/home')
def home():
    flask.session['message'] = None
    database_methods.get_debit_transactions()
    database_methods.get_debit_transfers()

    flask.session['page'] = '.home'
    return flask.render_template("home.html")


@app.route('/savings')
def savings():
    database_methods.get_savings_transfers()
    flask.session['page'] = '.savings'
    return flask.render_template("savings.html")


@app.route('/savings', methods=['POST'])
def add_savings():
    database_methods.open_savings_account()

    return flask.redirect("/savings")


@app.route('/credit')
def credit():
    database_methods.get_credit_history()
    database_methods.get_credit_check()
    flask.session['page'] = '.credit'
    return flask.render_template("credit.html")


@app.route('/credit', methods=['POST'])
def new_line_of_credit():
    flask.session['message'] = None
    if flask.request.form['action'] == 'create_credit':
        database_methods.open_credit_account()
    else:
        database_methods.delete_credit(int(
            flask.request.form['account_number']))

    return flask.render_template('credit.html')


@app.route('/transfer')
def transfer():
    flask.session['page'] = '.transfer'
    return flask.render_template("transfer.html")


@app.route('/transfer', methods=['POST'])
def transfer_action():
    flask.session['message'] = None
    if flask.request.form['action'] == 'personal':
        transfer_type = flask.request.form['personal_transfer']
        amount = float(flask.request.form['personal_transfer_amount'])
        database_methods.personal_transfer(transfer_type, amount)

    elif flask.request.form['action'] == 'payment':
        account = flask.request.form['credit_account']
        amount = float(flask.request.form['credit_payment'])
        database_methods.credit_payment(account, amount)

    else:
        recipient = flask.request.form['send_to']
        amount = float(flask.request.form['transfer_amount'])
        database_methods.send_money(recipient, amount)

    return flask.render_template('transfer.html')


@app.route('/personal')
def personal():
    flask.session['page'] = '.personal'
    database_methods.get_personal_info()
    return flask.render_template("personal.html")


@app.route('/personal', methods=['POST'])
def update_personal():
    field = flask.request.form['updated_value']
    value = flask.request.form['update_personal']

    database_methods.update_info(field, value)

    flask.session['personal_info'] = None
    return flask.redirect("/personal")


@app.route('/contact')
def contact():
    flask.session['page'] = '.contact'
    return flask.render_template("contact.html")
