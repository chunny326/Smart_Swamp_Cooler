"""
Authors: Jayden Smith & Maxwell Cox

Last Modified: March 26, 2021

ECE 4020 - Senior Project II

Main script for Flask website
filename: main.py
"""

from flask import (Flask, render_template, request, url_for, make_response, send_file)
from flask_mysql_connector import MySQL
import json
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import requests
from pathlib import Path
import logging
import geocoder
import reverse_geocoder
import datetime
from datetime import datetime
import os
import qrcode
import image

global numDays
numDays = 14

# Unique IDs for Zigbee sensor nodes
ROOF_SENSOR_ID = "0013a200Ac21216"
HOME_SENSOR_ID = "0013a200Ac1f102"

app = Flask(__name__) # Needs to be used in every flask application

# Connect to the mySQL database and provide login credentials
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'pi'
app.config['MYSQL_DATABASE'] = 'smartswampcooler'
app.config['MYSQL_PASSWORD'] = 'jeniffer'
mysql = MySQL(app)

# SQL queries to be used
# Select all data from given sensor and interval (# of days previous)
SQL_SELECT_SENSOR_DATA = """
  SELECT *
  FROM sensor_data
  WHERE sensor_id=%s
  AND timestamp >= NOW() - INTERVAL %s DAY
  ORDER BY timestamp
"""

# Select most recent entry for given sensor ID
SQL_SELECT_RECENT_DATA = """
  SELECT *
  FROM sensor_data
  WHERE sensor_id=%s
  ORDER BY timestamp
  DESC LIMIT 1
"""

# Insert new row of Cooler Settings
SQL_INSERT_SETTINGS = """
 INSERT INTO cooler_settings (timestamp, setting, desiredTemperature)
 VALUES (NOW(), %s, %s)
"""

# Select most recent entry for cooler setting
SQL_SELECT_COOLER_SETTING = """
  SELECT *
  FROM cooler_settings
  ORDER BY timestamp
  DESC LIMIT 1
"""

# Retrieve all cooler settings to display on webpage
SQL_SELECT_ALL_COOLER_SETTINGS = """
  SELECT *
  FROM cooler_settings
  ORDER BY timestamp
  DESC LIMIT 2000
"""

#  Define a class for holding database entry information
class SensorData:
  def __init__(self, id="-1", sensor_id="-1", temperature=32.5, humidity=25.7):
    self.id = id
    self.sensor_id = sensor_id
    self.temperature = temperature
    self.humidity = humidity
        
# Maps database data to sensor_data object
def map_to_object(data):
  sensor_data = SensorData()
  try:
    # assign database fields to object
    sensor_data.id                      = (data["id"])
    sensor_data.sensor_id               = (data["sensor_id"])
    sensor_data.timestamp               = str(data["timestamp"])
    sensor_data.temperature             = (data["temperature"])
    sensor_data.humidity                = (data["humidity"])
  
  except Exception as ex:
    print("ERROR: Error mapping database data to sensor_data object")
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print(message)
    return sensor_data 
  
  return sensor_data

# retrieve most recent temp/hum/timestamp data from database
def getRecentData(sensor_name=""):
  # creating a connection cursor
  mycursor = mysql.new_cursor()
  
  if sensor_name == "roof":
    params = (ROOF_SENSOR_ID,)
  elif sensor_name == "home":
    params = (HOME_SENSOR_ID,)
  else:
    print("ERROR: Invalid sensor name: {}".format(sensor_name))
    print("Specify valid sensor name: 'roof' or 'home'\n")
    return -1
  
  # retrieve most recent data
  mycursor.execute(SQL_SELECT_RECENT_DATA, params)
  
  # this will extract row headers
  row_headers = [x[0] for x in mycursor.description] 
  myresult = mycursor.fetchall()

  # convert SQL entry to Python dict object
  json_data = []
  for result in myresult:
    json_data.append(dict(zip(row_headers,result)))

  data = json.dumps(json_data, indent=4, sort_keys=True, default=str)
  data = json.loads(data)
  
  # print out all json data entries
  for i in range(len(data)):
      #print(data[i])
      sensor_data = map_to_object(data[i])
  
  return sensor_data

# Read entries from database given sensor name and number of days
def read_sensor_db(sensor_name="", days=2):
  # create new connection cursor
  mycursor = mysql.new_cursor()

  if sensor_name == "roof":
    params = (ROOF_SENSOR_ID, days,)
  elif sensor_name == "home":
    params = (HOME_SENSOR_ID, days,)
  else:
    print("ERROR: Invalid sensor name: {}".format(sensor_name))
    print("Specify valid sensor name: 'roof' or 'home'\n")
    return -1
  
  if days < 1:
    print("ERROR: Specify number of days for sensor data >1\n")
    return -1
    
  # retrieve data from given sensor for given number of days
  mycursor.execute(SQL_SELECT_SENSOR_DATA, params)
  
  # feed database entries into individual temps/hums/times for plotting
  # and return these Python lists
  data = mycursor.fetchall()
  dates = []
  temps = []
  hums = []
  for row in data:
      dates.append(row[2])
      temps.append(row[3])
      hums.append(row[4])
  
  return dates, temps, hums

def get_cooler_setting():
    # creating a connection cursor
    mycursor = mysql.new_cursor()
    
    # retrieve data from given sensor for given number of days
    mycursor.execute(SQL_SELECT_COOLER_SETTING)
  
    # this will extract row headers
    row_headers = [x[0] for x in mycursor.description] 
    myresult = mycursor.fetchall()

    json_data = []
    for result in myresult:
        json_data.append(dict(zip(row_headers,result)))
    
    data = json.dumps(json_data, sort_keys=True, default=str)
    data = json.loads(data)
    
    return data[0]["setting"], data[0]["desiredTemperature"] 
    
def plot_sensor(data, time, loc='inside', sensor='temperature'):
    ys = data
    #print("These are my {} {} values:\n{}".format(loc, sensor, ys))
    
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    
    if sensor == 'temperature':
        axis.set_title("Temperature [°F]")
    else:
        axis.set_title("Humidity [%]")
    
    axis.set_xlabel("Time")
    axis.grid(True)
    xs = time
    axis.plot(xs, ys)
    axis.tick_params('x', labelrotation=75)
    fig.set_tight_layout(True)
    
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    
    return response

# Insert newest cooler setting to the database
def write_db(coolerSet, desiredTemperature):
    print("Inserting new cooler setting data...")
    
    mycursor = mysql.new_cursor()

    params = (coolerSet, desiredTemperature,)
    mycursor.execute(SQL_INSERT_SETTINGS, params)
    mysql.connection.commit()
  
    print("{} record(s) affected".format(mycursor.rowcount))
  
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

    #logging.basicConfig(level=logging.DEBUG)
    session = requests.Session()
    session.headers.update({'User-Agent': '(Smart Swamp Coooler Project, ronaldjensen@mail.weber.edu)'})

    lat, lon = coordinates

    request_string = 'https://api.weather.gov/points/{lat:0.3f},{lon:0.3f}'.format(lat=lat, lon=lon)
    print('get '+request_string)

    for i in range(0,5):
        response = session.get(request_string, timeout=(5, 60)) # wait 5 seconds
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
def retrieve_forecast_data():
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

    g = geocoder.ip('me')

    cityAndState = getCityAndState(g.latlng)
    forecast_data = retrieve_raw_forecast_data(g.latlng)
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

def ip_or_qr(get=None):
    # find current IP address where website is available on network
    stream = os.popen("ifconfig wlan0 | egrep -o 'inet ([0-9]{1,3}\.){3}[0-9]{1,3}' | egrep -o '([0-9]{1,3}\.){3}[0-9]{1,3}'")
    ip_addr = "http://" + stream.read()
    
    # print("Current IP address: ", ip_addr)
    if get == 'ip':
        return ip_addr
    
    # make and return QR code image
    if get == 'qr':
        # convert IP address to QR code to display on website, where any phone can scan and connect to it
        #return qrcode.make(ip_addr)
        return qrcode.make(ip_addr)

@app.route("/")
def index():
    # recent sensor readings
    recent_roof_data = SensorData()
    recent_home_data = SensorData()
    recent_roof_data = getRecentData(sensor_name="roof")
    recent_home_data = getRecentData(sensor_name="home")
    coolerSetting, desiredTemperature = get_cooler_setting()
    
    # displaying forecast
    temperatures, times, upcomingWeekWeatherData, upcomingWeekLength,\
        currentCommonTime, currentTemperature, currentIcon,\
        currentForecast, currentDate, cityAndState = retrieve_forecast_data()
    
    # retrieve current IP address on network
    ip_addr = ip_or_qr(get='ip')
    
    templateData = {
        'time_roof': recent_roof_data.timestamp,
        'temp_roof': recent_roof_data.temperature,
        'hum_roof': recent_roof_data.humidity,
        'time_home': recent_home_data.timestamp,
        'temp_home': recent_home_data.temperature,
        'hum_home': recent_home_data.humidity,
        'num_days': numDays,
        'cooler_setting': coolerSetting,
        'desired_temp': desiredTemperature,
        'temperatures': temperatures,
        'times': times, 
        'upcomingWeekWeatherData': upcomingWeekWeatherData, 
        'upcomingWeekLength': upcomingWeekLength,
        'currentCommonTime': currentCommonTime, 
        'currentTemperature': currentTemperature,
        'currentIcon': currentIcon,
        'currentForecast': currentForecast,
        'currentDate': currentDate,
        'cityAndState': cityAndState,
        'ip_addr': ip_addr
    }
    
    return render_template('main/index.html', **templateData)

@app.route('/', methods=['POST'])
def my_form_post():
    req_form = dict(request.form)
    coolerSetting = None
    desiredTemperature = None
    
    if 'numDays' in req_form:
        #print("Setting numDays\n")
        global numDays
        numDays = int (request.form.get('numDays'))
        coolerSetting, desiredTemperature = get_cooler_setting()
    elif 'coolerSetting' in req_form:
        #print("Setting coolerSetting\n")
        #global coolerSetting
        coolerSetting = request.form.get('coolerSetting')
        desiredTemperature = request.form.get('desiredTemperature')
        write_db(coolerSetting, desiredTemperature)
        
    recent_roof_data = SensorData()
    recent_home_data = SensorData()
    recent_roof_data = getRecentData(sensor_name="roof")
    recent_home_data = getRecentData(sensor_name="home")
    
    # displaying forecast
    temperatures, times, upcomingWeekWeatherData, upcomingWeekLength,\
        currentCommonTime, currentTemperature, currentIcon,\
        currentForecast, currentDate, cityAndState = retrieve_forecast_data()
    
    # retrieve current IP address on network
    ip_addr = ip_or_qr(get='ip')
    
    templateData = {
        'time_roof': recent_roof_data.timestamp,
        'temp_roof': recent_roof_data.temperature,
        'hum_roof': recent_roof_data.humidity,
        'time_home': recent_home_data.timestamp,
        'temp_home': recent_home_data.temperature,
        'hum_home': recent_home_data.humidity,
        'num_days': numDays,
        'cooler_setting': coolerSetting,
        'desired_temp': desiredTemperature,
        'temperatures': temperatures,
        'times': times, 
        'upcomingWeekWeatherData': upcomingWeekWeatherData, 
        'upcomingWeekLength': upcomingWeekLength,
        'currentCommonTime': currentCommonTime, 
        'currentTemperature': currentTemperature,
        'currentIcon': currentIcon,
        'currentForecast': currentForecast,
        'currentDate': currentDate,
        'cityAndState': cityAndState,
        'ip_addr': ip_addr
    }
    
    return render_template('main/index.html', **templateData)

@app.route('/qr_code')
def get_qr_code():
    qr_code = ip_or_qr(get='qr')
    output = io.BytesIO()
    qr_code.convert('RGBA').save(output, format='PNG')
    output.seek(0, 0)

    return send_file(output, mimetype='image/png', as_attachment=False)

@app.route('/plot/temp_roof')
def plot_temp_roof():
    global numDays
    times, temps, hums = read_sensor_db(sensor_name="roof", days=numDays)
    return plot_sensor(temps, loc='outside', sensor='temperature', time=times)

@app.route('/plot/hum_roof')
def plot_hum_roof():
    global numDays
    times, temps, hums = read_sensor_db(sensor_name="roof", days=numDays)
    return plot_sensor(hums, loc='outside', sensor='humidity', time=times)

@app.route('/plot/temp_home')
def plot_temp_home():
    global numDays
    times, temps, hums = read_sensor_db(sensor_name="home", days=numDays)
    return plot_sensor(temps, loc='inside', sensor='temperature', time=times)

@app.route('/plot/hum_home')
def plot_hum_home():
    global numDays
    times, temps, hums = read_sensor_db(sensor_name="home", days=numDays)
    return plot_sensor(hums, loc='inside', sensor='humidity', time=times)

@app.route('/cooler_settings_log')
def cooler_settings_log():
    # creating a connection cursor
    mycursor = mysql.new_cursor()
    # get all cooler settings to display
    mycursor.execute(SQL_SELECT_ALL_COOLER_SETTINGS) 
    data = mycursor.fetchall() 
    return render_template('main/cooler_settings_log.html', value=data)