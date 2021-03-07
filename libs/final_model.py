# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 14:05:03 2021
Last Modified on Mar 6 17:36:12 2021

@author: rjensen, jlimondo
"""

import os, sys

local_module_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'libs')
sys.path.append(local_module_path)

from .cooler_model import *
from .Environment import Environment
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger('AutoSettings') 

def get_auto_setting_debug(level):
    logger.setLevel(level)

def get_auto_setting(T_amb, rh_amb, T_in, rh_in, house_settings, desired_temp=75):
    '''Inside and outside temperatures are obtained, 
    a simulation is then run in each of the five operating modes to determine
    the most suitable mode for operation. 
    The 'Pump' mode is not considered because it is the same as 'Off'.
    The most suitable mode is returned to the controller.'''
    
    # get outside temperature and RH
    # for now, just hard code something, note: temperature in Celsius here
    if isinstance(T_amb, list):
        T_ambient = [f2c(x) for x in T_amb]
    else:
        T_ambient = f2c( T_amb )
    rh_ambient= rh_amb
    T_house = f2c( T_in )
    rh_house = rh_in

    rho_air = 0.00238 # slug/ft**3 (sea level)

    # get settings
    # Cooler parameters:
    v_dot_air = (0, house_settings.lo_fan_volume, house_settings.hi_fan_volume) # ft**3/s, 0 for Off, 70 for Lo, 106 for Hi - based on cooler rating
    m_dot_air = np.array(v_dot_air)*rho_air # kg/s
    cooler_efficiency = house_settings.efficiency
    
    # House parameters:
    house_vol = house_settings.house_volume #ft**3
    desired_temp = f2c( desired_temp ) # Celsius
    
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
    best_next_T = 0
    for mode in modes:
        if mode == 'Pump': break
        logger.info( 'Mode: {}, House: Temp {:0.1f}, Rh {:0.1f}, Ambient: Temp {}, Rh {}'.format(mode, T_house, rh_house, T_ambient, rh_ambient ) )
        result=forecast_inside_conditions(4, 
                                   modes[mode]['fan'], modes[mode]['pump'],
                                   T_ambient, rh_ambient,
                                   T_house, rh_house, v_dot_air, house_vol
                                   )
        score = sum((result.T_house - desired_temp )**2)
        logger.debug( 'Score at time steps\n{}'.format ( (result.T_house - desired_temp )**2 ) )
        logger.debug( 'Temperature at time steps\n{}'.format ( result ) )
        logger.info( 'Final Score {}'.format(score) )

        if score < best_score:
            best_score = score
            best_mode = mode
            best_next_T = result.T_house[0]
    
    # score and return result
    logger.info('Next inside temperature: {}'.format(c2f(k2c( best_next_T ))))
    return best_mode

def forecast_inside_conditions(t, fan, pump, T_ambient, rh_ambient, 
                               T_house, rh_house, v_dot_air, v_house,
                               dt = 5, cooler_efficiency = 0.744):
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
        result.append( (i, T_ambient[i], rh_ambient[i], T_exhaust, rh_exhaust, v_dot_air[fan] * dt, house.tem, house.rh) )
        # time = time + deltat 

    ## T(t) = T0 + dT/dt (t)

    return pd.DataFrame(result, columns = ('time', 'T_amb',  'rh_amb', 'T_ext',  'rh_ext', 'Flow', 'T_house', 'rh_house') )

if __name__ == '__main__':
    print(get_auto_setting())