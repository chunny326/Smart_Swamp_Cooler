
from flask import (Flask, render_template)

app = Flask(__name__) #Needs to be used in every flask application

@app.route('/')
def index():
    return render_template('main/index.html')
