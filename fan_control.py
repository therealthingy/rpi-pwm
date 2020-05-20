import RPi.GPIO as GPIO
from time import sleep
import os
import sys


# 'Constants'
GPIO_PWM_PIN = int(os.getenv('GPIO_PWM_PIN') or 12)
INVERTED_PWM_SIGNAL = True if os.getenv('INVERTED_PWM_SIGNAL') == 'True' else False

CPU_TEMP_THRESHOLD_DEGREES = float(os.getenv('CPU_TEMP_THRESHOLD_DEGREES') or 54)
UPDATE_INTERVAL_SEC = float(os.getenv('UPDATE_INTERVAL_SEC') or 1.5)
COOLDOWN_FACTOR = 5  # How long the fan should continue spinning before slowing down (= (COOLDOWN_FACTOR +1) x UPDATE_INTERVAL_SEC)

MIN_DC = float(os.getenv('MIN_DC') or 35)
MAX_DC = float(os.getenv('MAX_DC') or 95)
DC_STEP = 5



# Global variables
# ! Invert only on output and comparison w/ static values !
def invertDC(dutycycle):
    return dutycycle if INVERTED_PWM_SIGNAL is False else 100 - dutycycle

dc = invertDC(0)



# --- Methods
def initPWM(pwm_pin):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(pwm_pin, GPIO.OUT)
    return GPIO.PWM(pwm_pin, 50)


def pwmGetDC():
    return dc

def newPwmSetDc(pwm):
    def pwmSetDC(next_dc):
        global dc
        dc = next_dc

        applied_dc = dc
        if invertDC(applied_dc) >= MAX_DC:		    		      	      # MAX_DC
            applied_dc = invertDC(MAX_DC)
        elif (invertDC(applied_dc) != 0 and invertDC(applied_dc) <= MIN_DC): 	      # MIN_DC
            applied_dc = invertDC(MIN_DC)

        # print("Current global dc: %d, applied dc: %d" % (invertDC(dc), invertDC(applied_dc)))
        pwm.ChangeDutyCycle(applied_dc)
    return pwmSetDC


# $$$ Calc methods: required due to inversion $$$
def calcIncDC(current_dc):
    if invertDC(current_dc) < 98:
        return (current_dc + DC_STEP if INVERTED_PWM_SIGNAL is False else current_dc - DC_STEP)
    return current_dc

def calcDecDC(current_dc):
    if invertDC(current_dc) > 2:
        return (current_dc - DC_STEP if INVERTED_PWM_SIGNAL is False else current_dc + DC_STEP)
    return current_dc



def getCPUtemp():
    res = os.popen('vcgencmd measure_temp').readline()
    return float((res.replace("temp=","").replace("'C\n","")))



def logToConsole(temp, cycle):
    print('Current temp: %f ℃, estimated fan dutycycle: %f' % (temp, invertDC(cycle)))




# --- Main program
# - Init PWM
print(f"{GPIO_PWM_PIN=} {INVERTED_PWM_SIGNAL=} {MIN_DC=} {MAX_DC=} {CPU_TEMP_THRESHOLD_DEGREES=} {UPDATE_INTERVAL_SEC=}")

try:
    pwm = initPWM(GPIO_PWM_PIN)
    pwm.start(pwmGetDC())

    pmwSetDC = newPwmSetDc(pwm)
    cool_down = 0

    while True:
        cpu_temp = getCPUtemp()
        tmp_dc = pwmGetDC()
        logToConsole(cpu_temp, tmp_dc)

        if (cpu_temp > CPU_TEMP_THRESHOLD_DEGREES):         # fanUp
            pmwSetDC(calcIncDC(tmp_dc))
            cool_down = COOLDOWN_FACTOR
        elif (cpu_temp < CPU_TEMP_THRESHOLD_DEGREES):       # fanDown
            if cool_down == 0:
                pmwSetDC(calcDecDC(tmp_dc))
            else:
                cool_down -= 1

        sleep(UPDATE_INTERVAL_SEC)

except KeyboardInterrupt:
    pwm.stop()
    GPIO.cleanup()
