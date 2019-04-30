from flask import Flask
import session_key
import os

# Initialize the app
app = Flask(__name__, instance_relative_config=True)
app.secret_key = session_key.secret_key
# app.secret_key = os.environ['secret_key']

from app import views
# Load the views
app.config.from_object('config')
