import pyvisa as visa, numpy as np, uproot, progressbar, sys
import matplotlib.pyplot as plt
from Phidget22.Phidget import *
from Phidget22.Devices.TemperatureSensor import *
import time
from datetime import datetime

def display_waveform(x, y, xscale = None, xlabel=None, ylabel=None, xrange=None, yrange=None, title=None):
    fig, (ax0) = plt.subplots(nrows=1, ncols=1, sharey=False, sharex=False, figsize=(8,5))

    ax0.plot(x, y, "black")
    if xrange == None: ax0.set_xlim(x[0], x[-1])
    
    if xrange != None: ax0.set_xlim(xrange)
    if yrange != None: ax0.set_ylim(yrange)
    if xlabel != None: ax0.set_xlabel(xlabel)
    if ylabel != None: ax0.set_ylabel(ylabel)
    if title  != None: ax0.set_title(title)
    
    plt.show()

def to_root(file_name, data):
    # Save data dictionary to a tree in a root file
    # @params: _file_name_ with path to root file and _data_ dict.
    print(f"Saving to: {file_name}.root")
    with uproot.recreate(file_name+".root") as output_file:
        output_file["pulse_information"] = data

def to_npz(file_name, data):
    # Save data dictionary to an npz file
    # @params: _file_name_ with path to npz file and _data_ dict.   
    # print(f"Saving to: {file_name}.npz")
    np.savez_compressed(file_name, **data)

class Sensor:

    def __init__(self, serial=None, hubport=None, timeout=1000, channel=None):
        self.temperature_sensor = TemperatureSensor()
        self.serial  = serial 
        self.hubport = hubport 
        self.timeout = timeout 
        self.channel = channel
        self.temperature_sensor.setHubPort(self.hubport)
        self.temperature_sensor.setDeviceSerialNumber(self.serial)
        self.temperature_sensor.openWaitForAttachment(self.timeout)
        self.temperature_sensor.setChannel(self.channel)

    def read(self):
        return self.temperature_sensor.getTemperature()

    def close(self):
        return self.temperature_sensor.close()


class MDO34():

    def __init__(self, address, timeout):
        
        self.address = address 
        self.timeout = timeout

        self.resource_manager = visa.ResourceManager() 
        self.scope   = self.resource_manager.open_resource(self.address)
        self.scope.timeout = self.timeout 

    def query(self, command):
        return self.scope.query(command)
    
    def write(self, command):
        return self.scope.write(command)
    
    def read_trigger_rate(self):
        rate = self.scope.query(':TRIG:FREQ?')
        try: 
            rate = np.double(rate.strip())
            return rate 
        except: 
            print("Unable to read trigger rate.")
            return None

# Initialize temperature sensors        
temperatureSensor0 = Sensor(serial=620013, hubport=0, channel=0)
temperatureSensor1 = Sensor(serial=620013, hubport=1, channel=0)
        
# Initilialize scope        
scope = MDO34(address = "USB0::0x0699::0x052C::SGVJ0002263::INSTR", timeout = 10000)
scope_id = scope.query('*IDN?')
print(scope_id)

# Set scope parameters
status = scope.write(':DATA:SOURCE CH1')
print(f"Status: {status}")

status = scope.write(':DATA:START  1')
print(f"Status: {status}")

status = scope.write(':DATA:STOP   800')
print(f"Status: {status}")

status = scope.write(':DATA:ENC   ASCii')
print(f"Status: {status}")

# Read scope waveform parameters
NR_pt  = int(scope.query(':WFMOutpre:NR_pt?'))
XUNit  = scope.query(':WFMOutpre:XUNit?')
XZEro  = float(scope.query(':WFMOutpre:XZEro?'))
XINcr  = float(scope.query(':WFMOutpre:XINcr?'))
YUNit  = scope.query(':WFMOutpre:YUNit?')  
YZEro  = float(scope.query(':WFMOutpre:YZEro?'))  
YMUlt  = float(scope.query(':WFMOutpre:YMUlt?'))
BYT_nr = int(scope.query(':WFMOutpre:BYT_nr?'))
print(f"Units: {XUNit}, {YUNit}.")

# Prepare to store waveforms
N = int(sys.argv[2]) 
waveforms = np.zeros((N,800), dtype=float)

visa_status = scope.write('ACQ:SEQ:NUMSEQ 1')


x   = np.arange(0, 800, 1)
x_s = np.asarray([XZEro + XINcr*xi for xi in x])

run_number = int(sys.argv[1])
widgets=[f'Run {run_number}. Channel 0. Preprocessing: ', progressbar.Percentage(), progressbar.Bar('\u2587', '|', '|'), ' ', progressbar.Timer()]

not_busy = scope.query('*OPC?')
not_busy = not_busy.replace("\n","")
print(f"Not Busy: {not_busy} (1 if true)")


# 43.51 V
# pe    = 3.440
# start = 5.440 - 0.5*pe
# stop  = 5.440 + 2.5*pe
# trigger_levels = np.arange(start/1000., stop/1000., step = 0.5*pe/1000.)

# # 40.51 V
pe = 1.4
start = 3.28 - 0.5*pe
stop  = 3.28 + 2.5*pe
trigger_levels = np.arange(start/1000., stop/1000., step = 0.5*pe/1000.)

# print(trigger_levels)

# sys.exit(0)

# trigger_levels = np.arange(0.0015, 0.0025, step = 0.0005)
# print(trigger_levels)
# print(len(trigger_levels))

# trigger_levels = [0.00328]

with open(f"./trigger_study_{run_number:04d}.csv", "w") as file:
    file.write(f" Trigger Level (V), Room Temperature (C), Probe Temperature (C), Trigger Frequency (Hz)\n")

for i in range(0, len(trigger_levels)):
    print(f"{trigger_levels[i]:5.4f}")
    scope.write('*WAI')
    trigger_level = scope.write(f':TRIGger:A:LEVel -{trigger_levels[i]:5.4f}')
    trigger_level = scope.query(':TRIGger:A:LEVel?')


    rooms  = []
    probes = []
    noises = []
    for j in range(0, 30):
        scope.write('*WAI')
        current_time = datetime.now()
        probe = temperatureSensor0.read()
        room  = temperatureSensor1.read()
        trigger_count = scope.read_trigger_rate()
        time_string = current_time.strftime("%H:%M:%S")
        print(f"{time_string}. Room: {room} C. Probe: {probe} C. Trigger Rate: {trigger_count/1000} (kHz)")
        
        rooms.append(room)
        probes.append(probe)
        noises.append(trigger_count)
        time.sleep(1)

    avg_room  = np.average(rooms)
    avg_probe = np.average(probes)
    avg_noise = np.average(noises)

    with open(f"./trigger_study_{run_number:04d}.csv", "a+") as file:
        file.write(f"-{trigger_levels[i]:5.4f}, {avg_room}, {avg_probe}, {avg_noise}\n")

sys.exit(0)

trigger_level = scope.write(':TRIGger:A:LEVel -0.0015')
trigger_level = scope.query(':TRIGger:A:LEVel?')
print("Trigger level: ", trigger_level)

sys.exit(0)

# trigger_count = scope.query(':TRIGger:FREQ?')
trigger_count = scope.read_trigger_rate()
print("Trigger rate: ", trigger_count)



# scope.write('*WAI')
# scope.write('MEASUrement:STATIstics:STATE ON')
# trigger_rate = scope.query('MEASUrement:STATIstics?')
# print(trigger_rate)
with open(f"./noise_info_{run_number:04d}.csv", "w") as file:
    file.write(f" Time, Room Temperature (C), Probe Temperature (C), Trigger Frequency (Hz)\n")

with open(f"./noise_live.csv", "w") as file:
    file.write(f" Time, Room Temperature (C), Probe Temperature (C), Trigger Frequency (Hz)\n")

read = True
while read == True:
    current_time = datetime.now()
    probe = temperatureSensor0.read()
    room  = temperatureSensor1.read()
    trigger_count = scope.read_trigger_rate()

    time_string = current_time.strftime("%H:%M:%S")
    print(f"{time_string}. Room: {room} C. Probe: {probe} C. Trigger Rate: {trigger_count/1000} (kHz)")
    
    with open(f"./noise_info_{run_number:04d}.csv", "a+") as file:
        file.write(f"{time_string}, {room}, {probe}, {trigger_count}\n")

    with open(f"./noise_live.csv", "a+") as file:
        file.write(f"{time_string}, {room}, {probe}, {trigger_count}\n")

    time.sleep(1)


sys.exit(0)

bar = progressbar.ProgressBar(widgets=widgets, maxval=N).start()
i = 0
while i  < N:

    try:
        visa_status = scope.write('ACQ:STATE RUN')
        curve = scope.query('CURVE?')
        curve = curve.replace('\n','')
        waveform = np.asarray([float(element) for element in curve.split(',')])

        y_V = np.asarray([YZEro + YMUlt*yi for yi in waveform])

        for j in range(0, len(y_V)):
            waveforms[i][j] = y_V[j]

        bar.update(i+1)

        if i>1 and i%100 == 0:
            data = {'waveforms':waveforms, 'x_s':x_s}
            to_npz(f"./run-{run_number}.temp", data)

        i += 1 
    
    except:
        print("Unable to read this time.")

data = {'waveforms':waveforms, 'x_s':x_s}

print("\n")
final_file = f"./run-{run_number}"
to_npz(final_file, data)