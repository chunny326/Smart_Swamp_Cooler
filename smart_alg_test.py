import libs

def test_desired_temp():
    # Desired Temp, Outside Temp, Inside Temp, Expected Result
    test_data = [ (75,90,90,"Fan w/Pump"),
                  (75,90,60,"Fan"),
                  (75,60,90,"Fan"),
                  (75,60,60,"Off"), ]
    for data in test_data:
        setting = libs.get_auto_setting(data[1], 30,\
                                        data[2], 30,\
                                        desired_temp=data[0])
        print("Expected: {} \t Received: {}".format(data[3], setting))
        
if __name__ == "__main__":
    test_desired_temp()