import flask
from app import app
import database_methods


@app.route('/')
def index():
    flask.session.clear()
    database_methods.close_connect()
    return flask.render_template("login.html")


@app.route('/', methods=['POST'])
def login_post():
    email = flask.request.form['email']
    post_password = flask.request.form['password']
    result = database_methods.login(email, post_password)

    if result:
        return flask.redirect('/home')
    else:
        return flask.redirect('/')


@app.route('/home')
def home():
    if flask.session.get('debit_transactions') is None:
        database_methods.get_debit_transactions(flask.session['id'])

    flask.session['page'] = '.home'
    return flask.render_template("home.html")


@app.route('/savings')
def savings():
    flask.session['page'] = '.savings'
    return flask.render_template("savings.html")


@app.route('/credit')
def credit():
    flask.session['page'] = '.credit'
    return flask.render_template("credit.html")


@app.route('/transfer')
def transfer():
    flask.session['page'] = '.transfer'
    return flask.render_template("transfer.html")


@app.route('/personal')
def personal():
    flask.session['page'] = '.personal'
    return flask.render_template("personal.html")


@app.route('/contact')
def contact():
    flask.session['page'] = '.contact'
    return flask.render_template("contact.html")
