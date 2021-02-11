from flask import (Flask, render_template, url_for, request)
# from flask import Markup

app = Flask(__name__) #Needs to be used in every flask application

@app.route('/')
def index():
    return render_template('main/index.html', title='Index')

@app.route("/log")
def log_window():
    labels = ["January","February","March","April","May","June","July","August"]
    values = [10,9,8,7,6,4,7,8]
    # make a 'JSON' dictonary
    data = { 'labels' : labels, 'values': values }
    return render_template('main/log.html', data=data, title='Log File')

@app.route('/cooler', methods=('GET','POST'))
def cooler_window():

    if request.method == 'POST': 
        autoOn = request.form.get('auto')
        manualOn = request.form.get('manual')
        highFanOn = request.form.get('highFan')
        lowFanOn = request.form.get('lowFan')
        pumpOn = request.form.get('pump')

        print("Is auto checked?  " + str("" if autoOn is None else autoOn))
        print("Is manual checked?  " + str("" if manualOn is None else manualOn))
        print("Is highFan checked?  " + str("" if highFanOn is None else highFanOn))
        print("Is lowFan checked?  " + str("" if lowFanOn is None else lowFanOn))
        print("Is pump checked?  " + str("" if pumpOn is None else pumpOn))
        #print("Is cooler running yet?  " + str("" if coolerRunning is None else coolerRunning))
        print("Switching\n")

        # if coolerRunning == False:
        #     coolerRunning = True
        # else:
        #     coolerRunning = False
    else:
        # coolerRunning = False
        autoOn = True
        manualOn = False
        highFanOn = False
        lowFanOn = True
        pumpOn = True

    return render_template('main/cooler.html', coolerRunning=False, autoOn=autoOn, manualOn=manualOn, hihgFanOn=highFanOn, lowFanOn=lowFanOn, pumpOn=pumpOn)

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

