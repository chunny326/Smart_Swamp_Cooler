"""
Author: Jayden Smith

Last Modified: April 5, 2021

ECE 4020 - Senior Project II

filename: main.py

Main script for Flask website:
This script manages the main website, including accessing MySQL databse, 
controlling which cooler setting and desired temperature is chosen, 
displaying inside and outside sensor data, showing historical cooler
settings and sensor readings, and providing live forecast conditions. 
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

# default number of days shown for historical sensor plots
global numDays
numDays = 14

# Unique IDs for Zigbee sensor nodes
HOME_SENSOR_ID = "0013a200Ac21216"
ROOF_SENSOR_ID = "0013a200Ac1f102"

# Needs to be used in every flask application
app = Flask(__name__) 

# Connect to the mySQL database and provide login credentials
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'pi'
app.config['MYSQL_DATABASE'] = 'smartswampcooler'
app.config['MYSQL_PASSWORD'] = 'jeniffer'
mysql = MySQL(app)

# --------------- SQL queries to be used ---------------------- #
# Select all data from given sensor and interval (# of days shown)
SQL_SELECT_SENSOR_DATA = """
  SELECT *
  FROM sensor_data
  WHERE sensor_id=%s
  AND timestamp >= NOW() - INTERVAL %s DAY
  ORDER BY timestamp
"""

# Select most recent entry for given sensor
SQL_SELECT_RECENT_DATA = """
  SELECT *
  FROM sensor_data
  WHERE sensor_id=%s
  ORDER BY timestamp
  DESC LIMIT 1
"""

# Insert new row of settings for cooler (setting and desired temp)
SQL_INSERT_SETTINGS = """
 INSERT INTO cooler_settings (timestamp, setting, desiredTemperature)
 VALUES (NOW(), %s, %s)
"""

# Select most recent entry for cooler setting to display on website
SQL_SELECT_COOLER_SETTING = """
  SELECT *
  FROM cooler_settings
  ORDER BY timestamp
  DESC LIMIT 1
"""

# Retrieve all cooler settings to display on webpage for page of 
#   historical settings and desired temperatures with timestamps
SQL_SELECT_ALL_COOLER_SETTINGS = """
  SELECT *
  FROM cooler_settings
  ORDER BY timestamp
  DESC LIMIT 2000
"""

# Delete old forecasted data to not fill up database needlessly
#   old forecasted data is deleted and new data replaces it
SQL_DELETE_OLD_FORECAST = """
  DELETE FROM forecast
"""

# Insert forecasted temperatures into database for smart algorithm
SQL_INSERT_FORECAST_TEMPERATURE = """
  INSERT INTO forecast (timestamp, temperature)
  VALUES (%s, %s)
"""

# Define a class for holding sensor data information for database entry
#   entries have a sensor id, temperature, humidity, and timestamp
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
    # assign database fields to SensorData object
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
  # create a connection cursor to the database
  mycursor = mysql.new_cursor()
  
  # get chosen sensor data based on id from database
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
  
  # print out all json data entries and map to SensorData class object
  for i in range(len(data)):
      #print(data[i])
      sensor_data = map_to_object(data[i])
  
  return sensor_data

# Read entries from database given sensor name and number of days
def read_sensor_db(sensor_name="", days=2):
  # create new connection cursor
  mycursor = mysql.new_cursor()

  # get chosen sensor data based on id from database
  if sensor_name == "roof":
    params = (ROOF_SENSOR_ID, days,)
  elif sensor_name == "home":
    params = (HOME_SENSOR_ID, days,)
  else:
    print("ERROR: Invalid sensor name: {}".format(sensor_name))
    print("Specify valid sensor name: 'roof' or 'home'\n")
    return -1
  
  # validate accurate database retrieval
  if days < 1:
    print("ERROR: Specify number of days for sensor data >1\n")
    return -1
    
  # retrieve data from given sensor for given number of days
  mycursor.execute(SQL_SELECT_SENSOR_DATA, params)
  
  # feed database entries into individual temps/hums/times lists
  # for plotting and return these Python lists
  data = mycursor.fetchall()
  dates = []
  temps = []
  hums = []
  for row in data:
      dates.append(row[2])
      temps.append(row[3])
      hums.append(row[4])
  
  return dates, temps, hums

# retrieve current cooler setting and desired temp from database 
def get_cooler_setting():
    # creating a connection cursor
    mycursor = mysql.new_cursor()
    
    # retrieve data from given sensor for given number of days
    mycursor.execute(SQL_SELECT_COOLER_SETTING)
  
    # this will extract row headers
    row_headers = [x[0] for x in mycursor.description] 
    myresult = mycursor.fetchall()

    # convert SQL entry to Python dict object
    json_data = []
    for result in myresult:
        json_data.append(dict(zip(row_headers,result)))
    
    data = json.dumps(json_data, sort_keys=True, default=str)
    data = json.loads(data)
    
    return data[0]["setting"], data[0]["desiredTemperature"] 

# plot temperature and humidity plots on website, return png
# image to display    
def plot_sensor(data, time, loc='inside', sensor='temperature'):
    # assign y axis for temperature or humidity
    ys = data
    #print("These are my {} {} values:\n{}".format(loc, sensor, ys))
    
    # create new subplot
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    
    # assign y axis label depending on temp or hum
    if sensor == 'temperature':
        axis.set_title("Temperature [°F]")
    else:
        axis.set_title("Humidity [%]")
    
    # add label, grid, x-axis spacing, other formatting
    axis.set_xlabel("Time")
    axis.grid(True)
    xs = time
    axis.plot(xs, ys)
    axis.tick_params('x', labelrotation=75)
    fig.set_tight_layout(True)
    
    # convert to image that can be displayed in HTML
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    
    # return png image to be displayed
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    
    return response

# insert newest cooler setting to the database
def write_db(coolerSet, desiredTemperature):
    print("Inserting new cooler setting data...")
    
    # create new database connection cursor
    mycursor = mysql.new_cursor()

    # provide cooler setting and desired temperature parameters
    # to SQL query to write to database
    params = (coolerSet, desiredTemperature,)
    
    # write settings to database and commit changes
    mycursor.execute(SQL_INSERT_SETTINGS, params)
    mysql.connection.commit()
  
    print("{} record(s) affected".format(mycursor.rowcount))
  
# delete previous forecasted temperatures from database, then
# rewrite over entries with newly retrieved forecasted data
def forecast_temps_db(temperatures, times):
    # create a connection to database, call SQL query to 
    # delete old data, commit changes
    mycursor = mysql.new_cursor()
    mycursor.execute(SQL_DELETE_OLD_FORECAST)
    mysql.connection.commit()
    
    # connect to database, insert all data retrieved from 
    # weather.gov into forecast database table, commit changes
    i = 0
    for temperature in temperatures:
       mycursor = mysql.new_cursor()
       params = (times[i], temperature,)
       i += 1
       mycursor.execute(SQL_INSERT_FORECAST_TEMPERATURE, params)
       mysql.connection.commit()

# plot forecasted data, make displayable in HTML
def plot_forecast(temperatures, time):
    # get y axis temperature values
    ys = temperatures
    
    # create new Python subplot
    fig = Figure(figsize=(9, 4))
    axis = fig.add_subplot(1, 1, 1)
    
    # set title and axis parameters
    # axis.set_title("Temperature [°F]")
    #axis.set_xlabel("Time")
    axis.grid(True)
    xs = time
    axis.plot(xs, ys)
    axis.tick_params('x', labelrotation=75)
    axis.xaxis.set_ticks_position('top')
    #fig.set_tight_layout(True)
    
    # convert to displayable image for website
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    
    # return viewable png image for website
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
    
    # write list of forecasted temperatures to database for smart algorithm
    forecast_temps_db(temperatures, times)
    
    return temperatures, times, upcomingWeekWeatherData, upcomingWeekLength, currentCommonTime, currentTemperature, currentIcon, currentForecast, stringCurrentDate, cityAndState

# return Pi's current IP address or IP address as QR code
def ip_or_qr(get=None):
    # find current IP address where website is available on network
    stream = os.popen("ifconfig wlan0 | egrep -o 'inet ([0-9]{1,3}\.){3}[0-9]{1,3}' | egrep -o '([0-9]{1,3}\.){3}[0-9]{1,3}'")
    
    # append "http://" to make QR code link to website immediately across all devices
    ip_addr = "http://" + stream.read()
    
    # return IP address if specified
    # print("Current IP address: ", ip_addr)
    if get == 'ip':
        return ip_addr
    
    # make and return QR code image if specified
    if get == 'qr':
        # convert IP address to QR code to display on website, 
        # where any phone can scan and connect to it
        return qrcode.make(ip_addr)

# main landing page for website: retrieves all values needed from sensors,
# plots, historical data, forecast, and database to display on website,
# feeds all of these values into index.html file
@app.route("/")
def index():
    # retrieve recent sensor readings from database
    recent_roof_data = SensorData()
    recent_home_data = SensorData()
    recent_roof_data = getRecentData(sensor_name="roof")
    recent_home_data = getRecentData(sensor_name="home")
    
    # retrieve current cooler settings from database
    coolerSetting, desiredTemperature = get_cooler_setting()
    
    # retrive data for displaying forecast
    temperatures, times, upcomingWeekWeatherData, upcomingWeekLength,\
        currentCommonTime, currentTemperature, currentIcon,\
        currentForecast, currentDate, cityAndState = retrieve_forecast_data()
    
    # retrieve current IP address on network
    ip_addr = ip_or_qr(get='ip')
    
    # store all required data in dictionary for easy access on index page
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
    
    # render index template with all of the retrieved data
    return render_template('main/index.html', **templateData)

# main landing page POST for website: retrieves all values needed from sensors,
# plots, historical data, forecast, and database to display on website,
# feeds all of these values into index.html file
@app.route('/', methods=['POST'])
def my_form_post():
    # pull POST request
    req_form = dict(request.form)
    coolerSetting = None
    desiredTemperature = None
    
    # check which submit on website was chosen
    # retrieve new number of days shown for historical data or
    # new cooler setting and desired temperature
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
        # write new cooler settings to database
        write_db(coolerSetting, desiredTemperature)
       
    # retrieve recent sensor readings from database
    recent_roof_data = SensorData()
    recent_home_data = SensorData()
    recent_roof_data = getRecentData(sensor_name="roof")
    recent_home_data = getRecentData(sensor_name="home")
    
    # retrieve data for displaying forecast
    temperatures, times, upcomingWeekWeatherData, upcomingWeekLength,\
        currentCommonTime, currentTemperature, currentIcon,\
        currentForecast, currentDate, cityAndState = retrieve_forecast_data()
    
    # retrieve current IP address on network
    ip_addr = ip_or_qr(get='ip')
    
    # store all required data in dictionary for easy access on index page
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
    
    # render index template with new POST data retrieved
    return render_template('main/index.html', **templateData)

# route for index page to display QR code containing devices IP address
@app.route('/qr_code')
def get_qr_code():
    # retrieve QR code
    qr_code = ip_or_qr(get='qr')
    
    # convert QR code to png image viewable on HTML index page
    output = io.BytesIO()
    qr_code.convert('RGBA').save(output, format='PNG')
    output.seek(0, 0)

    # return QR code image to website
    return send_file(output, mimetype='image/png', as_attachment=False)

# route for index page to plot roof temperature plot
@app.route('/plot/temp_roof')
def plot_temp_roof():
    # need global number of days to retrieve number of days in this function
    global numDays
    
    # retrieve roof temperature data for given number of days from database
    times, temps, hums = read_sensor_db(sensor_name="roof", days=numDays)
    return plot_sensor(temps, loc='outside', sensor='temperature', time=times)

# route for index page to plot roof humidity plot
@app.route('/plot/hum_roof')
def plot_hum_roof():
    # need global number of days to retrieve number of days in this function
    global numDays
    
    # retrieve roof humidity data for given number of days from database
    times, temps, hums = read_sensor_db(sensor_name="roof", days=numDays)
    return plot_sensor(hums, loc='outside', sensor='humidity', time=times)

# route for index page to plot home temperature plot
@app.route('/plot/temp_home')
def plot_temp_home():
    # need global number of days to retrieve number of days in this function
    global numDays
    
    # retrieve home temperature data for given number of days from database
    times, temps, hums = read_sensor_db(sensor_name="home", days=numDays)
    return plot_sensor(temps, loc='inside', sensor='temperature', time=times)

# route for index page to plot home humidity plot
@app.route('/plot/hum_home')
def plot_hum_home():
    # need global number of days to retrieve number of days in this function
    global numDays
    
    # retrieve home humidity data for given number of days from database
    times, temps, hums = read_sensor_db(sensor_name="home", days=numDays)
    return plot_sensor(hums, loc='inside', sensor='humidity', time=times)

# route to display historical cooler settings table
# displays rows of timestamps with each new cooler setting and desired temperature
@app.route('/cooler_settings_log')
def cooler_settings_log():
    # creating a connection cursor
    mycursor = mysql.new_cursor()
    
    # get all historical cooler settings to display
    mycursor.execute(SQL_SELECT_ALL_COOLER_SETTINGS) 
    data = mycursor.fetchall() 
    
    # render cooler settings table page
    return render_template('main/cooler_settings_log.html', value=data)

# disable caching so automatic refresh gathers most up-to-date values for 
# QR code, IP address, sensor readings, and forecasted data
@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    # make caching disabled immediately
    response.headers['Expires'] = '0'
    response.cache_control.max_age = 0
    return response
