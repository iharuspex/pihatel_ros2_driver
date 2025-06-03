import os
import platform
import time
import psutil


def process_status(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return True
    return False


class Buzzer:
    is_connect = False
    pi = None
    pigpio = None

    def __init__(self) -> None:
        self.pin = 12

        self.mode_error = [(300, 50), (300, 50), (300, 50)]

        self.mode_start = [(2000, 25), (0, 200), (2000, 50), (2500, 50), (0, 200),
                           (2000, 50), (2500, 50), (0, 200), (2000, 50), (2500, 50)]

        self.mode_stop = [(2500, 25), (0, 200), (2500, 50), (2000, 50), (0, 200),
                          (2500, 50), (2000, 50), (0, 200), (2500, 50), (2000, 50)]

    def connect(self):
        if self.is_connect:
            return self.is_connect
        try:
            self.check_if_pigpio_running()
            time.sleep(3)
            import pigpio
            self.pigpio = pigpio
        except ModuleNotFoundError:
            print(f"[error]: buzzer is not supported for your device")
            self.is_connect = False
            return self.is_connect

        if self.pigpio is None:
            print("[error]: buzzer is not ready")
            self.is_connect = False
            return self.is_connect

        self.pi = self.pigpio.pi()
        self.is_connect = True

        if not self.pi.connected:
            print("[error]: could not connect to pigpiod")
            self.is_connect = False
            return self.is_connect

        return self.is_connect

    def start_buzzer(self):
        if self.pi is None or not self.pi.connected:
            print("[error]: could not connect to pigpiod")
            return

        try:
            self.pi.set_mode(self.pin, self.pigpio.OUTPUT)
            self.play_buzzer(self.mode_start)
            self.pi.write(self.pin, 0)
            self.is_connect = False
        except Exception as e:
            print(f"[error] could not connect to buzzer: {e}")
            self.pi.stop()

    def stop_buzzer(self):
        if self.pi is None or not self.pi.connected:
            print("[error]: could not connect to pigpiod")
            return

        try:
            self.pi.set_mode(self.pin, self.pigpio.OUTPUT)
            self.play_buzzer(self.mode_stop)
            self.pi.write(self.pin, 0)
            self.is_connect = False
        except Exception as e:
            print(f"[error] could not connect to buzzer: {e}")
        finally:
            self.pi.stop()

    def error_buzzer(self):
        if self.pi is None or not self.pi.connected:
            print("[error]: could not connect to pigpiod")
            return

        try:
            self.pi.set_mode(self.pin, self.pigpio.OUTPUT)
            self.play_buzzer(self.mode_error)
            self.pi.write(self.pin, 0)
        except Exception as e:
            print(f"[error] could not connect to buzzer: {e}")
        finally:
            self.pi.stop()

    def play_buzzer(self, mode):
        for freq, duration in mode:
            self.pi.hardware_PWM(self.pin, freq, 500000)
            time.sleep(duration / 1000.0)
            self.pi.hardware_PWM(self.pin, 0, 0)
            time.sleep(0.04)

    def check_if_pigpio_running(self):
        if not process_status('pigpiod'):
            raise SystemError("pigpio daemon isn't running")
