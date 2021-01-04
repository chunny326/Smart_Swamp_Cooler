
from flask import (Flask, render_template)
# from flask import Markup

app = Flask(__name__) #Needs to be used in every flask application

@app.route('/')
def index():
    return render_template('main/index.html', title='Index')

@app.route("/log")
def chart():
    labels = ["January","February","March","April","May","June","July","August"]
    values = [10,9,8,7,6,4,7,8]
    # make a 'JSON' dictonary
    data = { 'labels' : labels, 'values': values }
    return render_template('main/chart.html', data=data, title='Log File')

