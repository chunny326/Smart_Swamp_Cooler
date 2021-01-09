from flask import (Flask, render_template, url_for)
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
    return render_template('main/log.html', data=data, title='Log File')

@app.route('/cooler')
def cooler_window():
    autoOn = True
    fanOn = False
    pumpOn = False
    return render_template('main/cooler.html', autoOn=autoOn, fanOn=fanOn, pumpOn=pumpOn)

@app.route('/interval')
def interval_window():
    return render_template('main/interval.html')

@app.route('/Add_Interval')
def new_interval_window():
    return render_template('main/newInterval.html')

@app.route('/Update_Interval')
def update_interval_window():
    return render_template('main/updateInterval.html')

@app.route('/timer')
def timer_window():
    return render_template('main/timer.html')

@app.route('/custom_log')
def custom_log_window():
    return render_template('main/customLog.html')

