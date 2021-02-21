# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 14:05:03 2021

@author: rjensen
"""

import os, sys

local_module_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'libs')
print(local_module_path)
sys.path.append(local_module_path)

#from cooler_model import *
import cooler_model as cm
from Environment import Environment
import numpy as np
import pandas as pd
import datetime

## T is temperature
## t is time

# volume of house  250 # m**3
# inside_temperature cm.c2k( cm.f2c( 90 ) ) # Kelvin
# inside_rh 40%
house = Environment(cm.c2k( cm.f2c( 90 ) ) , 40, 250)

# outside conditions
T_ambient = cm.c2k( cm.f2c( 95 ) ) # Kelvin
rh_ambient = 20 # %
rho_air = 1.23 # kg/m**3 (sea level)


# exhaust_T
# exhaust_rh
# exhaust_flow
# =============================================================================
# 6500 CFM
# 1725 RPM high speed = 3 m**3/s
# 4300 CFM
# 1140 RPM low speed = 2 m**3/s
# =============================================================================
# cooler air flow per fan speed
v_dot_air = (0, 2, 3) # m**3/s 
m_dot_air = np.array(v_dot_air)*rho_air # kg/s
cooler_efficiency = 0.744





def forecast_inside_conditions(t, fan, pump, T_ambient, rh_ambient, 
                               T_house, rh_house,
                               dt = 30, cooler_efficiency = 0.744):
    '''
    Forecast condtions inside the house 

    Parameters
    ----------
    t : int
        How far into the future to forecast.
    fan : int
        Fan setting 0=off, 1=low, 2=high.
    pump : int
        Pump setting 0=off, 1=on.
    T_ambient : 
        list of forecast temperatures
    rh_ambient : 
        list of forecast humidities
    T_house: 
        Starting temperature
    rh_house:
        Starting humidity
    dt : Interpolation time steps

    Returns
    -------
    Pandas data frame.

    '''
    time = datetime.datetime(2021, 1, 16, hour=7, minute=30) 
    deltat = datetime.timedelta(minutes=dt)
    result = []
    if type(T_ambient) is not list:
        T_ambient = [T_ambient,] * t
    n = len(T_ambient)
    
    if n < t:
        T_ambient = T_ambient * ( t // n + 1)

    if type(rh_ambient) is not list:
        rh_ambient = [rh_ambient,] * t
    n = len(rh_ambient)
    
    if n < t:
        rh_ambient = rh_ambient * ( t // n + 1)
    
    
    for i in range(t):
        T_exhaust, rh_exhaust = cm.calculate_outlet_temp(T_ambient[i], rh_ambient[i], cooler_efficiency)
        exhaust = Environment(T_exhaust, rh_exhaust, v_dot_air[2] * dt)

        house.remove(exhaust.vol)
        house.mix(exhaust)
#        print(house.__dict__)
        result.append( (time, T_ambient[i], rh_ambient[i], T_exhaust, rh_exhaust, house.tem, house.rh) )
        time = time + deltat 

    ## T(t) = T0 + dT/dt (t)

    return pd.DataFrame(result, columns = ('time', 'T_amb',  'rh_amb', 'T_ext',  'rh_ext', 'T_house', 'rh_house') )

def get_auto_setting():
    return_strings=[
        'Off',
        'Fan Hi',
        'Fan Lo',
        'Fan Hi (w/Pump)',
        'Fan Lo (w/Pump)',
        'Pump'
    ]

    return return_strings[1]

bob = ''
if __name__ == '__main__':
    T_ambient =[300.0, 302.3, 304.5, 306.4, 307.8, 308.7, 309.0, 308.7, 307.8, 306.4, 304.5, 302.3, 300.0, 297.7, 295.5, 293.6, 292.2, 291.3, 291.0, 291.3, 292.2, 293.6, 295.5, 297.7, 300.0]
    rh_ambient=[225, 25, 25, 25, 25, 25, 25, 26, 27, 28, 29, 30, 31, 29, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27]
    bob=forecast_inside_conditions(10, 0, 0, T_ambient, rh_ambient, 350, 8.5)
    print(bob)
    print(get_auto_setting())