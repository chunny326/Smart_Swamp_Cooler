#import logging
import libs

"""
TODO: add description
"""
def test_desired_temp():
    #libs.get_auto_setting_debug(logging.WARN)
    # Desired Temp, Outside Temp, Inside Temp, Expected Result
    test_data = [ {"desired_T": 75, "out_T": 90, "in_T": 90, "out_rh": 30, "in_rh": 30, "result": "Fan w/Pump"},
                  {"desired_T": 75, "out_T": 90, "in_T": 60, "out_rh": 30, "in_rh": 30, "result": "Fan"},
                  {"desired_T": 75, "out_T": 60, "in_T": 90, "out_rh": 30, "in_rh": 30, "result": "Fan"},
                  {"desired_T": 75, "out_T": 60, "in_T": 60, "out_rh": 30, "in_rh": 30, "result": "Off"},] 
    
    for data in test_data:
        setting = libs.get_auto_setting(data["out_T"], data["out_rh"],\
                                        data["in_T"], data["in_rh"],\
                                        data["desired_T"])
        print("Expected: {} \t Received: {}".format(data["result"], setting))
        
if __name__ == "__main__":
    test_desired_temp()
