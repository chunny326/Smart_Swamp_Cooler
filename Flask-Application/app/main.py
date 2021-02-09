from flask import (Flask, render_template, request, url_for, make_response, send_file)
from flask_mysql_connector import MySQL
import json
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

# unique IDs for Zigbee sensor nodes
ROOF_SENSOR_ID = "0013a200Ac21216"
HOME_SENSOR_ID = "0013a200Ac1f102"

app = Flask(__name__) #Needs to be used in every flask application

# Connect the mySQL database and provide login credentials
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
"""

SQL_SELECT_RECENT_DATA = """
  SELECT *
  FROM sensor_data
  WHERE sensor_id=%s
  ORDER BY timestamp
  DESC LIMIT 1
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
  
  mycursor.execute(SQL_SELECT_RECENT_DATA, params)
  
  # this will extract row headers
  row_headers = [x[0] for x in mycursor.description] 
  myresult = mycursor.fetchall()

  json_data = []
  for result in myresult:
    json_data.append(dict(zip(row_headers,result)))

  data = json.dumps(json_data, indent=4, sort_keys=True, default=str)
  data = json.loads(data)
  
  # print out all json data entries
  for i in range(len(data)):
      print(data[i])
      sensor_data = map_to_object(data[i])
  
  return sensor_data

# Read named sensor entries from database
def read_sensor_db(sensor_name="", days=0):
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
    
  mycursor.execute(SQL_SELECT_SENSOR_DATA, params)
  
  data = mycursor.fetchall()
  dates = []
  temps = []
  hums = []
  for row in data:
      dates.append(row[2])
      temps.append(row[3])
      hums.append(row[4])
  
  return dates, temps, hums

@app.route("/")
def index():
    recent_roof_data = SensorData()
    recent_home_data = SensorData()
    recent_roof_data = getRecentData(sensor_name="roof")
    recent_home_data = getRecentData(sensor_name="home")
    
    templateData = {
        'time_roof': recent_roof_data.timestamp,
        'temp_roof': recent_roof_data.temperature,
        'hum_roof': recent_roof_data.humidity,
        'time_home': recent_home_data.timestamp,
        'temp_home': recent_home_data.temperature,
        'hum_home': recent_home_data.humidity
    }
    return render_template('main/index.html', **templateData)

@app.route('/plot/temp_roof')
def plot_temp_roof():
    times, temps, hums = read_sensor_db(sensor_name="roof", days=14)
    ys = temps
    print("These are my outside temperature values:\n", ys)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Temperature [°F]")
    axis.set_xlabel("Time")
    axis.grid(True)
    xs = range(len(times))
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route('/plot/hum_roof')
def plot_hum_roof():
    times, temps, hums = read_sensor_db(sensor_name="roof", days=14)
    ys = hums
    print("These are my outside humidity values:\n", ys)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Humidity [%]")
    axis.set_xlabel("Time")
    axis.grid(True)
    xs = range(len(hums))
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route('/plot/temp_home')
def plot_temp_home():
    times, temps, hums = read_sensor_db(sensor_name="home", days=14)
    ys = temps
    print("These are my inside temperature values:\n", ys)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Temperature [°F]")
    axis.set_xlabel("Time")
    axis.grid(True)
    xs = range(len(temps))
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route('/plot/hum_home')
def plot_hum_home():
    times, temps, hums = read_sensor_db(sensor_name="home", days=14)
    ys = hums
    print("These are my inside humidity values:\n", ys)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Humidity [%]")
    axis.set_xlabel("Time")
    axis.grid(True)
    xs = range(len(hums))
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route('/cooler')
def cooler_window():
    autoOn = True
    fanOn = False
    pumpOn = False
    return render_template('main/cooler.html', autoOn=autoOn, fanOn=fanOn, pumpOn=pumpOn)
