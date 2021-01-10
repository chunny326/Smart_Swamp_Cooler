# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 08:24:54 2021

@author: rjensen

All conversions and constants from NASA TN D-8401
or 
Calculations of the outlet air conditions in the direct evaporative cooler
August 2012
DOI: 10.21608/jesaun.2012.114509
Waleed A Abdel-FadeelWaleed A Abdel-FadeelSoubhi A. Hassanein
"""

def c2k(c):
    ''' Celcius to Kelvin '''
    return c+273

def k2c(k):
    ''' Kelvin to Celcius '''
    return k-273

def f2c(f):
    ''' Fahrenheit to Celcius '''
    return (f-32)*5/9

def c2f(c):
    ''' Celsius to Fahrenheit '''
    return (c)*9/5 + 32

def U(ta, tw, p=1013.25):
    ''' ta - ambient temperature kelvin,
        tw - wet bulb temperature kelvin,
        p - pressure millibars,
        returns relative humidity in decimal
        '''
    a =-4.9283
    b= -2937.4
    c= 23.5518
    f=6.6e-4
    g=7.570e-7
    ## NASA TN D-8401 eq 24
    rh = 10**(-(c + b/ta )) * ta**(-a) * (
         10**(  c + b/tw)   * tw**( a) - (f+g*tw) * p * (ta-tw))
    return(rh)

def calculate_t_wet(t_amb, rh):
    ''' t_amb - ambient temperature celcius, rh - relative humidity %
    returns wet temperature in celcius
    '''
    ### abdel-faheed eq 9
    a1=-2.21e-6
    n1=1.724
    b1=7.87e-5
    a2=9.58e-4
    n2=1.549
    b2=6.91e-2
    a3=1.5924
    n3=0.727
    b3=-7.843
    
    return( (a1*t_amb**n1 + b1) * rh**2 + (a2*t_amb**n2 + b2) * rh +(a3*t_amb**n3 + b3) )
 
def calculate_outlet_temp(t_amb, rh, efficiency = 0.75):
    ''' t_amb - ambient temperature celcius, rh - relative humidity %
    efficiency = (t_amb - t_exh) / (t_amb - t_wet)
    return calculated cooler output temperature
    '''
    ### abdel-faheed eq 2, solved for t_wet
    t_wet = calculate_t_wet(t_amb, rh)
    t_exh = t_amb - efficiency * (t_amb - t_wet)
    rh_exh = U(c2k(t_exh), c2k(t_wet)) * 100
    return(t_exh, rh_exh)

def calculate_cooler_efficiency(t_amb, t_exh, t_wet):
    '''
    temperatures in the same units,
    returns calculated cooler efficieny in decimal
    '''
    ### abdel-faheed eq 2
    return ((t_amb - t_exh) / (t_amb - t_wet))

def unitTestRH():
    for t_amb in range(75, 130, 5):
        for rh in range(5, 105, 5):
            tw = calculate_t_wet(f2c(t_amb), rh)
            u  = U( c2k(f2c(t_amb)), c2k(tw) ) * 100
            print('{t_amb} -> {tw:0.1f} {rh} = {u:0.1f}'.format(t_amb=t_amb, rh=rh, tw=c2f(tw), u=u ))
            
            
            
def unitTest_outlet_temp( efficiency = 0.75 ):
    rhs=[2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
    for rh in rhs:
        print('\t{rh}'.format(rh=rh), end='')
    print()
        
    for t_amb in range(75, 130, 5):
        print('{}'.format(t_amb), end='')
        for rh in rhs:   
            t_exh, rh_exh = calculate_outlet_temp(f2c(t_amb), rh,  efficiency )
            print('\t{:.0f}'.format(c2f(t_exh) ), end='')
        print()
            
            
            
            
            
            
            