import requests
from pathlib import Path
import logging
import json
import io
import geocoder
import reverse_geocoder
import datetime
from datetime import datetime
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from flask import (Flask, render_template, url_for, make_response, request)
# from flask import Markup

app = Flask(__name__) #Needs to be used in every flask application

def plot_forecast(temperatures, time):
    ys = temperatures
    
    fig = Figure(figsize=(9, 4))
    axis = fig.add_subplot(1, 1, 1)
    
    # axis.set_title("Temperature [°F]")
    
    #axis.set_xlabel("Time")
    axis.grid(True)
    xs = time
    axis.plot(xs, ys)
    axis.tick_params('x', labelrotation=75)
    axis.xaxis.set_ticks_position('top')
    #fig.set_tight_layout(True)
    
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    
    return response

# Author: Maxwell Cox
# Last date modified: 3/24/2021
# Description: This method performs the requests to retrieve the forecast data from weather.gov. 
#              The requests will be attempted up to five times to ensure a valid response is given.
def retrieve_raw_forecast_data(coordinates):

    logging.basicConfig(level=logging.DEBUG)
    session = requests.Session()
    session.headers.update({'User-Agent': '(Smart Swamp Coooler Project, ronaldjensen@mail.weber.edu)'})

    lat, lon = coordinates

    request_string = 'https://api.weather.gov/points/{lat:0.3f},{lon:0.3f}'.format(lat=lat, lon=lon)
    print('get '+request_string)

    for i in range(0,5):
        response=session.get(request_string, timeout=(5, 60)) # wait 5 seconds
        if not response.ok:
            continue
        else:
            points_data = json.loads(response.content)
            forecast_request = points_data['properties']['forecastHourly']
            break

    for i in range(0,5):
        response=session.get(forecast_request, timeout=(5, 60)) # wait 5 seconds
        if not response.ok:
            continue
        else:
            return json.loads(response.content)

# Author: Maxwell Cox
# Last date modified: 3/24/2021
# Description: This method returns the city and state where the pi is being used
def getCityAndState(coordinates):
    location = reverse_geocoder.search(coordinates)
    print(location[0]['name'])
    return location[0]['name'] + ', ' + location[0]['admin1']

# Author: Maxwell Cox
# Last date modified: 3/24/2021
# Description: This method returns the present temperature from the forecast data
def getCurrentTemperature(forecast_data):
    periods = forecast_data['properties']['periods']
    firstPeriod = periods[0]
    return firstPeriod['temperature']

# Author: Maxwell Cox
# Last date modified: 3/24/2021
# Description: This method returns the current forecast icon from the forecast data
def getCurrentIcon(forecast_data):
    periods = forecast_data['properties']['periods']
    firstPeriod = periods[0]
    return firstPeriod['icon']

# Author: Maxwell Cox
# Last date modified: 3/24/2021
# Description: This method returns the current forecast from the forecast data
def getCurrentForecast(forecast_data):
    periods = forecast_data['properties']['periods']
    firstPeriod = periods[0]
    return firstPeriod['shortForecast']

# Author: Maxwell Cox
# Last date modified: 3/24/2021
# Description: This method returns the current date and time from the forecast data
def getCurrentDateAndTime():
    commonTimeValues = [['12am', '00:00:00'],
                        ['1am', '01:00:00'],
                        ['2am', '02:00:00'],
                        ['3am', '03:00:00'],
                        ['4am', '04:00:00'],
                        ['5am', '05:00:00'],
                        ['6am', '06:00:00'],
                        ['7am', '07:00:00'],
                        ['8am', '08:00:00'],
                        ['9am', '09:00:00'],
                        ['10am', '10:00:00'],
                        ['11am', '11:00:00'],
                        ['12pm', '12:00:00'],
                        ['1pm', '13:00:00'],
                        ['2pm', '14:00:00'],
                        ['3pm', '15:00:00'],
                        ['4pm', '16:00:00'],
                        ['5pm', '17:00:00'],
                        ['6pm', '18:00:00'],
                        ['7pm', '19:00:00'],
                        ['8pm', '20:00:00'],
                        ['9pm', '21:00:00'],
                        ['10pm', '22:00:00'],
                        ['11pm', '23:00:00']]

    currentDate = datetime.now()
    stringCurrentDate = currentDate.strftime('%m/%d')
    stringCurrentTime = currentDate.strftime('%H:00:00')
    for commonTimeValue in commonTimeValues:
        if commonTimeValue[1] == stringCurrentTime:
            currentCommonTime = commonTimeValue[0]
            break

    return currentCommonTime, stringCurrentDate

# Author: Maxwell Cox
# Last date modified: 3/24/2021
# Description: This method retrieves and formats data from weather.gov. It performs requests to retrieve the data first and then 
#              performs formatting to display the current, the daily and the upcoming week's forecast.
def retrieve_forecat_data():
    startDate = None
    currentTemperature = None
    currentForecast = None
    currentIcon = None
    currentTime = None
    currentCommonTime = None
    dailyHigh = None
    dailyLow = None
    next24HoursCollected = False
    nextTwentyFourHourWeatherData = []
    upcomingWeekWeatherData = []
    averageForecast = []
    temperatures = []
    times = []
    commonTimeValues = [['12am', '00:00:00'],
                        ['1am', '01:00:00'],
                        ['2am', '02:00:00'],
                        ['3am', '03:00:00'],
                        ['4am', '04:00:00'],
                        ['5am', '05:00:00'],
                        ['6am', '06:00:00'],
                        ['7am', '07:00:00'],
                        ['8am', '08:00:00'],
                        ['9am', '09:00:00'],
                        ['10am', '10:00:00'],
                        ['11am', '11:00:00'],
                        ['12pm', '12:00:00'],
                        ['1pm', '13:00:00'],
                        ['2pm', '14:00:00'],
                        ['3pm', '15:00:00'],
                        ['4pm', '16:00:00'],
                        ['5pm', '17:00:00'],
                        ['6pm', '18:00:00'],
                        ['7pm', '19:00:00'],
                        ['8pm', '20:00:00'],
                        ['9pm', '21:00:00'],
                        ['10pm', '22:00:00'],
                        ['11pm', '23:00:00']]


    g=geocoder.ip('me')

    cityAndState = getCityAndState(g.latlng)
    forecast_data = retrieve_raw_forecast_data(g.latlon)
    currentTemperature = getCurrentTemperature(forecast_data)
    currentIcon = getCurrentIcon(forecast_data)
    currentForecast = getCurrentForecast(forecast_data)
    currentCommonTime, stringCurrentDate = getCurrentDateAndTime()

    periods = forecast_data['properties']['periods']

    for sample in periods:
        if startDate == None:
            time = sample['startTime'].split('T')
            startDate = time[0]
            sampleDate = time[0]

        similarPrediction = False
        for forecast in averageForecast:
            if forecast[0] == sample['shortForecast']:
                forecast[1] += 1
                similarPrediction = True
                break
        
        if not similarPrediction:
            averageForecast.append([sample['shortForecast'], 1, sample['icon']])

        if currentTime != sample['endTime'].split('T')[1] and not next24HoursCollected:
            for commonTimeValue in commonTimeValues:
                if sample['startTime'].split('T')[1].split('-')[0] == commonTimeValue[1]:
                    nextTwentyFourHourWeatherData.append([sample['startTime'].split('T')[0].split('-')[0], commonTimeValue[0], sample['temperature']])
        elif not next24HoursCollected:
            for commonTimeValue in commonTimeValues:
                if sample['startTime'].split('T')[1].split('-')[0] == commonTimeValue[1]:
                    nextTwentyFourHourWeatherData.append([sample['startTime'].split('T')[0].split('-')[0], commonTimeValue[0], sample['temperature']])
                    next24HoursCollected = True

        if sampleDate == sample['startTime'].split('T')[0]:
            if dailyHigh == None:
                dailyHigh = sample['temperature']
            elif sample['temperature'] > dailyHigh:
                dailyHigh = sample['temperature']
            if dailyLow == None:    
                dailyLow = sample['temperature']
            elif sample['temperature'] < dailyLow:
                dailyLow = sample['temperature']

        else:
            forecastMostLikely = []
            for forecast in averageForecast:
                if len(forecastMostLikely) == 0 or forecastMostLikely[1] < forecast[1]:
                    forecastMostLikely = forecast

            formattedDate = datetime.strptime(sampleDate, '%Y-%m-%d').strftime('%m/%d')
            upcomingWeekWeatherData.append([formattedDate, dailyHigh, dailyLow, forecastMostLikely[2]])

            averageForecast = []
            sampleDate = sample['startTime'].split('T')[0]
            dailyHigh = sample['temperature']
            dailyLow = sample['temperature']
                
    
    for hour in nextTwentyFourHourWeatherData:
        temperatures.append(hour[2])
        times.append(hour[1])

    upcomingWeekLength = len(upcomingWeekWeatherData)

    return temperatures, times, upcomingWeekWeatherData, upcomingWeekLength, currentCommonTime, currentTemperature, currentIcon, currentForecast, stringCurrentDate, cityAndState


@app.route('/')
def index():

    temperatures, times, upcomingWeekWeatherData, upcomingWeekLength, currentCommonTime, currentTemperature, currentIcon, currentForecast, currentDate, cityAndState = retrieve_forecat_data()

    return render_template('main/index.html', title='Index', temperatures=temperatures, times=times, upcomingWeekWeatherData=upcomingWeekWeatherData, upcomingWeekLength=upcomingWeekLength, currentCommonTime=currentCommonTime, currentTemperature=currentTemperature, currentIcon=currentIcon, currentForecast=currentForecast, currentDate=currentDate, cityAndState=cityAndState)

@app.route("/log")
def log_window():

    return render_template('main/log.html')

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


# @app.route('/plot/forecast')
# def plot_temp_roof():
#     temperatures, hours, upcomingWeekWeatherData, currentTime, currentTemperature, currentConditions = retrieve_forecat_data()

#     return plot_forecast(temperatures, time=hours) 
