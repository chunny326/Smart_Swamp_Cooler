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
import numpy as np
import pandas as pd

## T is temperature
## t is time

# volume of house
# inside_temperature
# inside_rh
v_house = 250 # m**3
T_house = cm.c2k( cm.f2c( 90 ) ) # Kelvin
rh_house =  40 # %

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


T_exhaust, rh_exhaust = cm.calculate_outlet_temp(T_ambient, rh_ambient, cooler_efficiency)


h_house = cm.calculate_enthalpy(T_house, rh_house)
Q_house = h_house * rho_air * v_house # kJ

h_exhaust = cm.calculate_enthalpy(T_exhaust, rh_exhaust)



def forecast_inside_conditions(t, fan, pump, T_ambient, rh_ambient, dt = 0.1, cooler_efficiency = 0.744):
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
    dt : Interpolation time steps

    Returns
    -------
    Pandas data frame.

    '''
    time = 0
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
        result.append( (time, T_ambient[i], rh_ambient[i], T_exhaust, rh_exhaust) )
        time += dt 

    ## T(t) = T0 + dT/dt (t)

    return pd.DataFrame(result, columns = ('time', 'T_amb',  'rh_amb', 'T_ext',  'rh_ext') )
T_ambient =[293, 298, 303, 310, 313]
rh_ambient=[25,20,18,15,10]
print( forecast_inside_conditions(10, 0, 0, T_ambient, rh_ambient))