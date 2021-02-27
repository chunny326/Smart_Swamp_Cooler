# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 14:05:03 2021
Last Modified on Feb 27 13:27:02 2021

@author: rjensen, jlimondo
"""

import os, sys

local_module_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'libs')
print(local_module_path)
sys.path.append(local_module_path)

from .cooler_model import *
from .Environment import Environment
import numpy as np
import pandas as pd

def get_auto_setting(T_amb, rh_amb, T_in, rh_in, desired_temp=75):
    '''Inside and outside temperatures are obtained, 
    a simulation is then run in each of the five operating modes to determine
    the most suitable mode for operation. 
    The 'Pump' mode is not considered because it is the same as 'Off'.
    The most suitable mode is returned to the controller.'''
    
    # get outside temperature and RH
    # for now, just hard code something, note: temperature in Kelvin here
    T_ambient =[c2k( f2c( T_amb ) ), 302.3, 304.5, 306.4, 307.8, 308.7, 309.0, 308.7, 307.8, 306.4, 304.5, 302.3, 300.0, 297.7, 295.5, 293.6, 292.2, 291.3, 291.0, 291.3, 292.2, 293.6, 295.5, 297.7, 300.0]
    rh_ambient=[rh_amb, 25, 25, 25, 25, 25, 25, 26, 27, 28, 29, 30, 31, 29, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27]
    T_house = c2k( f2c( T_in ) )
    rh_house = rh_in

    rho_air = 0.00238 # slug/ft**3 (sea level)

    # get settings
    # Cooler parameters:
    v_dot_air = (0, 70, 106) # ft**3/s, 0 for Off, 70 for Lo, 106 for Hi - based on cooler rating
    m_dot_air = np.array(v_dot_air)*rho_air # kg/s
    cooler_efficiency = 0.744
    
    # House parameters:
    house_vol = 10000 #ft**3
    desired_temp = c2k( f2c( desired_temp ) ) # kelvin
    
    modes={
        'Off':            {'fan':0, 'pump':0},
        'Fan Hi':         {'fan':2, 'pump':0},
        'Fan Lo':         {'fan':1, 'pump':0},
        'Fan Hi (w/Pump)':{'fan':2, 'pump':1},
        'Fan Lo (w/Pump)':{'fan':1, 'pump':1},
        'Pump':           {'fan':0, 'pump':1}
    }
    
    # loop over modes
    best_mode = 'Off'
    best_score = 99999
    for mode in modes:
        if mode == 'Pump': break
        print(mode, T_house, rh_house)
        result=forecast_inside_conditions(4, 
                                   modes[mode]['fan'], modes[mode]['pump'],
                                   T_ambient, rh_ambient,
                                   T_house, rh_house, v_dot_air, house_vol
                                   )
        score = sum((result.T_house - desired_temp )**2)
        print( (result.T_house - desired_temp )**2)
        print(score)
        print("\n")
        if score < best_score:
            best_score = score
            best_mode = mode
    
    # score and return result

    return best_mode

def forecast_inside_conditions(t, fan, pump, T_ambient, rh_ambient, 
                               T_house, rh_house, v_dot_air, v_house,
                               dt = 15, cooler_efficiency = 0.744):
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
    v_dot_air:
        Air flow from cooler (vector of values)
    v_house:
        volume of house
    dt : Interpolation time steps

    Returns
    -------
    Pandas data frame.

    '''
    # time = datetime.datetime(2021, 1, 16, hour=7, minute=30) 
    # deltat = datetime.timedelta(minutes=dt)
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
    
    house   = Environment(T_house, rh_house, v_house)

    for i in range(t):
        T_exhaust, rh_exhaust = calculate_outlet_temp(T_ambient[i], rh_ambient[i], cooler_efficiency * pump)
        exhaust = Environment(T_exhaust, rh_exhaust, v_dot_air[fan] * dt)
#        print(exhaust.__dict__)
        house.remove(exhaust.vol)
        house.mix(exhaust)
#        print(house.__dict__)
        result.append( (i, T_ambient[i], rh_ambient[i], T_exhaust, rh_exhaust, house.tem, house.rh) )
        # time = time + deltat 

    ## T(t) = T0 + dT/dt (t)

    return pd.DataFrame(result, columns = ('time', 'T_amb',  'rh_amb', 'T_ext',  'rh_ext', 'T_house', 'rh_house') )

if __name__ == '__main__':
    print(get_auto_setting())