import flask
from app import app
import database_methods


@app.route('/')
def index():
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
def login():

    result = database_methods.get_debit_transactions(flask.session['id'])
    if result:
        return flask.render_template("home.html")
    else:
        return "Error"
