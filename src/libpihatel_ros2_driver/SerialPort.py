import platform
import queue
import threading
import time
import serial


class SerialManager:
    is_connect = False
    is_running = False
    is_error = False
    data_queue = queue.Queue()

    def __init__(self):
        self.ser = None
        self.speed = None
        self.thread = None
        self.selected_port = None

    def get_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if platform.system() == "Linux":
            ports.append("/dev/ttyS0")
        return ports

    def set_setting(self, setting):
        exit_flag = False
        answer_find = False
        data = bytearray(100)
        self.ser.timeout = 0.1
        self.ser.flush()
        self.ser.write(setting)

        data_buffer = b""
        start_time = time.time()

        while not exit_flag:
            num_bytes = self.ser.readinto(data)
            data_buffer += data
            if b"OK!" in data_buffer:
                exit_flag = True
                answer_find = True
            elif time.time() - start_time > 1:
                exit_flag = True
        return answer_find

    def set_settings(self, settings_list):
        result = False
        for setting in settings_list:
            for counter in range(4):
                result = self.set_setting(setting)
                if result:
                    break
            if result:
                print(setting, "Status OK!")
            else:
                print(setting, "FALED!")
                return result
        return result

    def set_baudrate(self, speed):
        self.ser.baudrate = speed
        return

    def send_all_baudrate(self, data):
        previous_speed = self.ser.baudrate
        for i in self.ser.BAUDRATES:
            if 9600 <= i <= 921600:
                self.set_baudrate(i)
                self.ser.write(data)
        self.set_baudrate(previous_speed)
        return

    def connect(self, port_name):
        if self.is_connect:
            print("Уже есть соединение!")
            return self.is_connect
        try:
            if self.ser is None:
                self.ser = serial.Serial(port_name, 115200)
            else:
                self.ser.port = port_name
                self.ser.open()
            if self.ser.isOpen():
                self.is_connect = True
                print("Успешное соединение с сом портом!")
            else:
                self.is_connect = False
                print("Не удалось открыть порт")

            return self.is_connect

        except serial.serialutil.SerialException as e:
            raise FileNotFoundError("Устройство не найдено!")
        except FileNotFoundError as e:
            print(f"Ошибка: {e}. Убедитесь, что порт '{port_name}' существует.")
        except Exception as e:
            raise Exception(f"Exception {e}")

    def disconnect(self):
        if self.is_connect:
            self.is_connect = False
            self.ser.close()

    def start(self):
        self.is_running = True
        self.is_error = False
        self.thread = threading.Thread(target=self.thread_read, name="Serial manager")
        self.thread.start()
        return self.is_running

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.thread.join()

    def thread_read(self):
        if self.ser:
            while self.is_running:
                data = bytearray(1000)
                try:
                    self.ser.timeout = 0.1
                    num_bytes = self.ser.readinto(data)
                    data = data[:num_bytes]
                    if len(data) > 0:
                        self.data_queue.put(data)
                    self.is_error = False
                except serial.SerialException as e:
                    self.is_error = True
                    time.sleep(1)
                except Exception as e:
                    print("ERROR ", str(e))

    def write_data(self, data: bytes):
        if len(data) > 0 and self.is_connect:
            self.ser.write(data)

    def upload(self):
        if self.is_error:
            self.is_error = False
            raise serial.SerialException("Не удалось получить данные c com порта!")
        dataret = b""
        data = self.data_queue.get(timeout=1)
        dataret += data
        return dataret

    def apppend_data(self, data):
        try:
            data_base = data
        except Exception as e:
            print(f"Ошибка при обработке данных: {e}")
            return
        self.ser.write(data_base)

