import RPi.GPIO as GPIO
from time import sleep
import os
import sys

from datetime import datetime



# 'Constants'
LOGGING_ENABLED = True if os.getenv('LOGGING_ENABLED') == 'True' else False

GPIO_PWM_PIN = int(os.getenv('GPIO_PWM_PIN') or 12)
INVERTED_PWM_SIGNAL = True if os.getenv('INVERTED_PWM_SIGNAL') == 'True' else False

CPU_TEMP_THRESHOLD_DEGREES = float(os.getenv('CPU_TEMP_THRESHOLD_DEGREES') or 54)
UPDATE_INTERVAL_SEC = float(os.getenv('UPDATE_INTERVAL_SEC') or 1.5)
COOLDOWN_FACTOR = 5  # How long the fan should continue spinning before slowing down (= COOLDOWN_FACTOR x UPDATE_INTERVAL_SEC)

INIT_DC = 0          # WHEN STARTING APP: FAN OFF
DC_STEP = 5
MIN_DC = float(os.getenv('MIN_DC') or 0)
MAX_DC = float(os.getenv('MAX_DC') or 100)



# Global variables
# ! Invert only on output and comparison w/ static values !
def invertDC(dc):
    return dc if INVERTED_PWM_SIGNAL is False else 100 - dc

calc_dc = invertDC(INIT_DC)



# --- Methods
def initPWM(pwm_pin):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(pwm_pin, GPIO.OUT)
    return GPIO.PWM(pwm_pin, 50)


def getPwmCalcDC():
    return calc_dc

def newSetPwmCalcDC(pwm):
    def setPwmCalcDC(next_calc_dc):
        global calc_dc
        calc_dc = next_calc_dc

        applied_dc = calc_dc
        if invertDC(applied_dc) >= MAX_DC:                                # MAX_DC
            applied_dc = invertDC(MAX_DC)
        elif (invertDC(applied_dc) != 0 and invertDC(applied_dc) <= MIN_DC):          # MIN_DC
            applied_dc = invertDC(MIN_DC)

        pwm.ChangeDutyCycle(applied_dc)
        return [calc_dc, applied_dc]
    return setPwmCalcDC


# $$$ Calc methods: required due to inversion $$$
def calcIncDC(current_dc):
    if invertDC(current_dc) < 98:
        return (current_dc + DC_STEP if INVERTED_PWM_SIGNAL is False else current_dc - DC_STEP)
    return current_dc

def calcDecDC(current_dc):
    if invertDC(current_dc) > 2:
        return (current_dc - DC_STEP if INVERTED_PWM_SIGNAL is False else current_dc + DC_STEP)
    return current_dc



def getCPUTemp():
    res = os.popen('vcgencmd measure_temp').readline()
    return float((res.replace("temp=","").replace("'C\n","")))



def logToConsole(temp, calc_dc, applied_dc):
    print('%s --- Current temp: %f ℃, calc. fan dutycycle: %f, applied dutycycle: %f' % (datetime.now().astimezone().isoformat(timespec='seconds'), temp, invertDC(calc_dc), invertDC(applied_dc)))




# --- Main program
# - Init PWM
print("Running as user '%s' on '%s'" %(os.path.split(os.path.expanduser('~'))[-1], os.uname()[1]))
print(f"{LOGGING_ENABLED=} {GPIO_PWM_PIN=} {INVERTED_PWM_SIGNAL=} {INIT_DC=} {DC_STEP=} {MIN_DC=} {MAX_DC=} {CPU_TEMP_THRESHOLD_DEGREES=} {UPDATE_INTERVAL_SEC=}")
print("\n")

try:
    pwm = initPWM(GPIO_PWM_PIN)
    pwm.start(getPwmCalcDC())

    setPwmCalcDC = newSetPwmCalcDC(pwm)
    cool_down, cpu_temp = 0, 0
    calc_dc = applied_dc = getPwmCalcDC()

    while True:
        cpu_temp = getCPUTemp()

        if (cpu_temp > CPU_TEMP_THRESHOLD_DEGREES):         # fanUp
            calc_dc, applied_dc = setPwmCalcDC(calcIncDC(calc_dc))
            cool_down = COOLDOWN_FACTOR -1
        elif (cpu_temp < CPU_TEMP_THRESHOLD_DEGREES):       # fanDown
            if cool_down == 0:
                calc_dc, applied_dc = setPwmCalcDC(calcDecDC(calc_dc))
            else:
                cool_down -= 1

        if LOGGING_ENABLED:
            logToConsole(cpu_temp, calc_dc, applied_dc)

        sleep(UPDATE_INTERVAL_SEC)

except KeyboardInterrupt:
    pwm.stop()
    GPIO.cleanup()
