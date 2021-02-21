# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 16:36:12 2021

@author: rjensen
"""

class Environment():
    def __init__(self, temp, rh, volume):
        self.tem = temp
        self.rh  = rh
        self.vol = volume
        
    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)
        
    def __print__(self):
        return "%r" % (self.__dict__)
        
    def mix(self, env):
        tvol = self.vol + env.vol
        self.rh  = (self.rh * self.vol + env.rh * env.vol) / tvol
        self.tem = (self.tem* self.vol + env.tem* env.vol) / tvol
        self.vol = tvol
        
    def remove(self, vol):
        self.vol -= vol


if __name__ == '__main__':
    house   = Environment(80, 25,10000)
    exhaust = Environment(70, 35, 1000)
    
    for t in range(20):
        house.remove(exhaust.vol)
        house.mix(exhaust)
        print(house.__dict__)
        

        
    