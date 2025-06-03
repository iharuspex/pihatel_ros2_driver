import datetime
import os
import platform
import threading
import time
import queue
import serial.tools.list_ports

from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus, TimeReference

# from src.structures.ForPrint import for_print
# from src.utils.Console import print
from libpihatel_ros2_driver.SerialPort import SerialManager
# from src.connections.TcpClient import TcpClient
from libpihatel_ros2_driver import Parser
# from src.converters.СonverterCNB import ConverterCNB
# from src.structures.SettingsJson import SettingsJson
from libpihatel_ros2_driver.SettingsComnav import SettingsComnav
from libpihatel_ros2_driver.Params import Params
# from src.output.LocalNtrip import LocalNtrip
# from src.output.RemoteNtrip import RemoteNtrip
# from src.output.FileRecorder import FileRecorder
# from src.output.NtripClient import NtripClient
from libpihatel_ros2_driver.CustomException import CustomException as CE
# from src.services.PointController import PointController
# from src.converters.RtcmStreamHandler import RtcmStreamHandler
# from src.services.CSController import ControllerCS
# from src.services.FTPController import FTPController
from libpihatel_ros2_driver.Buzzer import Buzzer

params_defenition = {
    "work_mode": {"type": str, "default": "default", "values": ("default", "processing", "error")},
    "data_hub": {"type": bool, "default": False},           # Статус работы
    "serial_manager": {"type": bool, "default": False},     # Статус работы
    "binary_parser": {"type": bool, "default": False},      # Статус работы
    "ascii_parser": {"type": bool, "default": False},       # Статус работы
    "to_com_manager": {"type": bool, "default": False},     # Статус работы
    "ntrip_remote": {"type": bool, "default": False},       # Статус работы
    "ntrip_local": {"type": bool, "default": False},        # Статус работы
    "ntrip_client": {"type": bool, "default": False},
    "tcp_remote": {"type": bool, "default": False},
    "file_is_rotate": {"type": bool, "default": False},     # Если True то новый файл уже создан
    "name_point": {"type": str, "default": "point"},        # Название точки
    "status_work_convert": {"type": bool, "default": False},
    "status_work_ftp_client": {"type": bool, "default": False},
    "status_work_buzzer": {"type": bool, "default": False}
}


class Controller (Node):
    _instance = None
    FIRMWARE_VERSION = 1.9
    satellite_constellations = ["GPS", "GLO", "GAL", "BDS"]

    def __init__(self):
        super().__init__('pihatel_ros2_driver')

        self.link = None

        self.fix_pub = self.create_publisher(NavSatFix, 'fix', 10)


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Controller, cls).__new__(cls)
            cls.params = Params(params_defenition)
        return cls._instance

    def set_class_reference(
            self,
            serial_port: SerialManager,
            ascii_parser: Parser.ParserDataASCII,
            # binary_parser: Parser.ParserDataBinary,
            # settings_json: SettingsJson,
            settings_comnav: SettingsComnav,
            # ntrip_remote: RemoteNtrip,
            # ntrip_local: LocalNtrip,
            # tcp_client: TcpClient,
            # file_recorder: FileRecorder,
            # to_com_obj: SerialManager,
            # ntrip_client: NtripClient,
            # convert_cnb: ConverterCNB,
            # points_cont: PointController,
            # rtcm_handler: RtcmStreamHandler,
            # cs_cont: ControllerCS,
            # tcp_remote: TcpClient,
            # ftp_cont: FTPController,
            buzzer: Buzzer,
    ):
        self.serial_port = serial_port
        self.ascii_parser = ascii_parser
        # self.binary_parser = binary_parser
        # self.settings_json = settings_json
        self.settings_comnav = settings_comnav
        # self.ntrip_remote = ntrip_remote
        # self.ntrip_local = ntrip_local
        # self.tcp_client = tcp_client
        # self.file_recorder = file_recorder
        # self.to_com_obj = to_com_obj
        # self.ntrip_client = ntrip_client
        # self.convert_cnb = convert_cnb
        # self.points_cont = points_cont
        # self.rtcm_handler = rtcm_handler
        # self.cont_cs = cs_cont
        # self.tcp_remote = tcp_remote
        # self.ftp_cont = ftp_cont
        self.buzzer = buzzer

    # def get_firmware_version(self) -> float:
    #     return self.FIRMWARE_VERSION

    # def get_plot_data(self) -> for_print:
    #     return self.binary_parser.ploted_data

    # def get_plot_data_dict(self):
    #     return self.binary_parser.ploted_data.get_dict()

    def get_ports(self) -> list:
        return self.serial_port.get_ports()

    def get_serial(self) -> str:
        return self.ascii_parser.params.get_param("serial")

    # def get_current_port(self) -> str:
    #     return self.ascii_parser.params.get_param("current_port")

    # def get_fix_status(self) -> str:
    #     '''Статус навигационного решения'''
    #     return self.ascii_parser.params.get_param("fix_status")

    # def get_current_coords(self) -> list:
    #     ret_obj = []
    #     for unit in self.ascii_parser.params.get_param("current_coords"):
    #         ret_obj.append(unit)
    #     return ret_obj

    # def get_sats_num(self) -> str:
    #     return str(self.ascii_parser.params.get_param("sats_num"))

    # def get_file_status(self) -> str:
    #     if self.file_recorder.status_file == "open":
    #         file_path = os.path.join(self.file_recorder.file_path, self.file_recorder.filename)
    #         file_size = "error"
    #         if os.path.exists(file_path):
    #             file_size = os.path.getsize(file_path)
    #         if type(file_size) == int:
    #             file_size = self._format_size(file_size)
    #         out_string = f"{self.file_recorder.filename} Size: {file_size}"
    #     else:
    #         out_string = f"stoped"
    #     return out_string

    # def get_ntrip_status(self) -> str:
    #     '''Возвращает строковый статус ntrip'''
    #     remote = self.params.get_param("ntrip_remote")
    #     local = self.params.get_param("ntrip_local")

    #     status_message = ""
    #     if remote:
    #         status_message += f"Remote: {self.ntrip_remote.host}:{self.ntrip_remote.port} mountpoint {self.ntrip_remote.mountpoint} "
    #     if local:
    #         if len(status_message) != 0:
    #             status_message += "\n"
    #         tcpstat = "on" if self.ntrip_local.tcp_out_status == True else "off"
    #         status_message += f"Local: 2101 Mountpoint: {self.ntrip_local.ntripMountpoint} TCP: {tcpstat} port {self.ntrip_local.tcp_out_port} "
    #     if len(status_message) == 0:
    #         status_message += "disabled"
    #     return status_message

    # def save_params(self, params_dict):
    #     ''':param params_dict: смотри SettingsJson'''
    #     self.settings_json.params.update(params_dict)
    #     self.settings_json.write_settings()
    #     print("Настройки сохранены!")
    #     return

    # def load_params(self) -> dict:
    #     ''':return: params_dict - смотри SettingsJson'''
    #     return self.settings_json.params.to_dict()

    # def update_params(self, val: dict):
    #     all_params = self.settings_json.params.to_dict()
    #     all_params[val["key"]] = val["val"]
    #     self.save_params(all_params)

    # def get_list_points(self):
    #     list_points = self.points_cont.get_list_points(False)
    #     return list_points

    # def save_input_points(self, name, coords):
    #     self.points_cont.save_input_points(name, coords)

    # def update_point(self, uuid, name, coords):
    #     self.points_cont.update_point(uuid, name, coords)

    # def sync_points(self):
    #     return self.points_cont.sync_points()

    # def delete_point(self, uuid):
    #     self.points_cont.delete_point(uuid)

    # def start_convert_cnb(self, file):
    #     threading.Thread(target=self.convert_cnb.convert_cnb, args=(file,)).start()

    # def get_convert_result_link(self):
    #     if self.convert_cnb.firstRequest:
    #         try:
    #             convert_result_list = self.convert_cnb.request_convert_scope()
    #             self.convert_cnb.data_list = convert_result_list
    #             self.convert_cnb.firstRequest = False
    #         except Exception:
    #             pass
    #     return self.convert_cnb.get_data_list()

    # def data_hub_callback_rtcm(self, data):
    #     '''Обработка данных RTCM'''
    #     self.rtcm_handler.handelPackets(data)

    # def data_hub_callback_cnb(self, data):
    #     '''Обработка данных CNB'''
    #     cur_time = self.binary_parser.get_current_time()
    #     if cur_time != 0.0:
    #         if self.file_recorder.status_file == "close":
    #             self.file_recorder.make_filename(cur_time)
    #             self.file_recorder.open_file()
    #         dt = datetime.datetime.utcfromtimestamp(cur_time)
    #         if dt.minute == 0 and not self.params.get_param("file_is_rotate"):

    #             file = self.file_recorder.delete_files()
    #             self.ftp_cont.set_status_deleted(file)
    #             self.ftp_cont.delete_file_from_json()

    #             self.ftp_cont.set_status_record(self.file_recorder.filename, 1)
    #             if self.params.get_param("status_work_ftp_client"):
    #                 self.ftp_cont.start_thread_send()

    #             self.file_recorder.make_filename(cur_time)
    #             self.file_recorder.new_file()
    #             self.ftp_cont.set_status_record(self.file_recorder.filename, 2)

    #             self.params.set_param("file_is_rotate", True)
    #         if dt.minute != 0 and self.params.get_param("file_is_rotate"):
    #             self.params.set_param("file_is_rotate", False)

    #         self.file_recorder.write(data)

    def data_hub_thread(self):
        queue_empty_counter = 0
        while self.status_primary_thread:
            try:
                data_recive = b""
                data = self.serial_port.upload()
                data_recive += data
                self.ascii_parser.append_data(data_recive)
                # self.binary_parser.append_data(data_recive)
                queue_empty_counter = 0
            except serial.SerialException as e:
                print("Error serial.SerialException:", str(e))
                threading.Thread(target=self.stop_controller).start()
                threading.Thread(target=lambda self: [time.sleep(30), self.start_controller(self.load_params())]).start()
                break
            except queue.Empty as e:
                queue_empty_counter += 1
                if queue_empty_counter >= 100:
                    threading.Thread(target=self.stop_controller).start()
                    threading.Thread(target=lambda self: [time.sleep(30), self.start_controller(self.load_params())]).start()
            except Exception as e:
                print("Error in structures hub", str(e))
                threading.Thread(target=self.stop_controller).start()
        self.status_primary_thread = False

    def get_frame_id(self):
        frame_id = self.declare_parameter('frame_id', 'gps').value
        prefix = self.declare_parameter('tf_prefix', '').value
        if len(prefix):
            return '%s/%s' % (prefix, frame_id)
        return frame_id

    def publish(self, frame_id):
        current_fix = NavSatFix()
        fix_params = self.ascii_parser.params.to_dict()
        
        # print(fix_params["current_coords"])

        # FIXME
        current_time = self.get_clock().now().to_msg()
        
        current_fix.header.stamp = current_time
        current_fix.header.frame_id = frame_id
        
        current_fix.status.status = NavSatStatus.STATUS_FIX
        current_fix.status.service = NavSatStatus.SERVICE_GPS

        latitude = fix_params['current_coords'][0]
        longitude = fix_params['current_coords'][1]
        altitude = fix_params['current_coords'][2]

        current_fix.latitude = latitude
        current_fix.longitude = longitude
        current_fix.altitude = altitude

        self.fix_pub.publish(current_fix)


    def data_thread_callback(self, data):
        self.serial_port.apppend_data(data)

    def wait_serial(self, timeout: int):
        '''Ожидание когда появится серийный номер модуля'''
        counter = 0
        while counter < timeout:
            if self.get_serial() != "":
                break
            time.sleep(0.1)
            counter += 0.1
        if counter >= timeout:
            raise CE.ControllerExeptions("Не удалось получить серийный номер устройства.")

    # def wait_current_port(self, timeout: int):
    #     counter = 0
    #     while counter < timeout:
    #         if self.get_current_port() != "":
    #             break
    #         time.sleep(0.1)
    #         counter += 0.1
    #     if counter >= timeout:
    #         raise CE.ControllerExeptions("Не удалось получить текущий порт.")

    def start_controller(self, params_val):
        print(f"Порт подключения : {params_val['port_name']}")
        # print(f"Координаты: {params_val['coords_input']}")
        # print(f"Статус фиксированных координат: {params_val['coords_status']}")
        # print(f"Версия RTCM протокола: {params_val['rtcm_type']}")
        # print(f"Интервал RTCM: {params_val['entry_interval_rtcm']}")
        # print(f"Отправка на удаленный сервер NTRIP: {params_val['ntrip_remote']}")
        # print(f"Локальный сервер NTRIP: {params_val['ntrip_local']}")
        # print(f"Локальный сервер TCP: {params_val['tcp_local']}")
        # print(f"Порт TCP сервера: {params_val['tcp_local_port']}")
        # print(f"PPS-выход: {params_val['pps_output']}")
        # print(f"Вход Event: {params_val['event_input']}")
        # print(f"Отправка данных в COM-порт: {params_val['to_com']}")
        # print(f"COM-порт для отправки: {params_val['to_com_port']}")
        # print(f"COM-порт1: {params_val['hardware_checkbox1'], params_val['hardware_speed1'], params_val['hardware_comport1']}")
        # print(f"COM-порт2: {params_val['hardware_checkbox2'], params_val['hardware_speed2'], params_val['hardware_comport2']}")
        # print(f"COM-порт3: {params_val['hardware_checkbox3'], params_val['hardware_speed3'], params_val['hardware_comport3']}")
        # print(f"Максимальное количество файлов: {params_val['max_num_files']}")

        try:
            # self.params.set_param("serial_manager", True)
            self.start_serial_port(params_val["port_name"])
            self.start_and_receive_configure_gnss(params_val)
            # self.ftp_cont.create_data_json()

            if not self.ascii_parser.start():
                raise CE.ControllerExeptions("Ошибка запуска ASCII парсера.")
            self.params.set_param("ascii_parser", True)

            # if params_val["to_com"]:
            #     if params_val["to_com_port"] == "":
            #         raise CE.ControllerExeptions("Ошибка при отправки данных в COM-порт. Выберите COM-порт из выпадающего списка")
            #     if params_val["to_com_port"] == params_val["port_name"]:
            #         raise CE.ControllerExeptions(f"Порт {params_val['to_com_port']} уже находится в работе. Выберите другой COM-порт")
            #     else:
            #         self.to_com_obj.connect(params_val["to_com_port"])
            #         self.rtcm_handler.subscribersPackedRTCM(self.to_com_obj.write_data)
            #         self.params.set_param("to_com", True)

            # if not self.binary_parser.start():
            #     raise CE.ControllerExeptions("Ошибка запуска BINARY парсера.")
            # self.params.set_param("binary_parser", True)

            if not self.start_data_hub():
                raise CE.ControllerExeptions("Ошибка запуска DATA_HUB.")
            self.params.set_param("data_hub", True)

            self.wait_serial(10)
            print(f"Серийный номер модуля: {self.get_serial()}")

            # self.start_setting_ports(params_val)

            # if params_val["ntrip_local"]:
            #     self.start_local_caster(params_val["tcp_local"], params_val["tcp_local_port"])
            #     self.params.set_param("ntrip_local", True)

            # if params_val["ntrip_remote"]:
            #     self.start_remote_caster(params_val['caster_host'], params_val['caster_port'], params_val['caster_password'], params_val['caster_mount_point'])
            #     self.params.set_param("ntrip_remote", True)

            # if params_val["tcp_remote"]:
            #     if params_val["tcp_remote_port"] == "":
            #         raise CE.ControllerExeptions(
            #             "Ошибка при запуске TCP Remote. Введите порт!")
            #     if params_val["tcp_remote_host"] == "":
            #         raise CE.ControllerExeptions(
            #             "Ошибка при запуске TCP Remote. Введите хост!")
            #     self.start_tcp_remote(params_val["tcp_remote_host"], params_val["tcp_remote_port"])
            #     self.params.set_param("tcp_remote", True)

            # if params_val["max_num_files"]:
            #     self.file_recorder.set_max_files(params_val["max_num_files"])
            #     file = self.file_recorder.delete_files()
            #     self.ftp_cont.set_status_deleted(file)
            #     self.ftp_cont.delete_file_from_json()

            # if params_val["statusCS_application"]:
            #     select_cs = self.cont_cs.get_select_cs()
            #     if select_cs is None:
            #         raise CE.ControllerExeptions("Выберите ситему координат!")
            #     if params_val["periodCS_sending"] == "":
            #         raise CE.ControllerExeptions("Установите интервал для СК!")
            #     self.rtcm_handler.set_params_packed(params_val["statusCS_application"], int(params_val["periodCS_sending"]), select_cs)

            # if "reset_status" in params_val:
            #     if params_val["reset_status"]:
            #         if params_val['port_name'] == "/dev/ttyS0":
            #             os.system("gpioset gpiochip0 22=1")
            #         else:
            #             raise CE.ControllerExeptions("К устройству нельзя применить reset!")

            # if "status_work_ftp" in params_val:
            #     if params_val["status_work_ftp"]:
            #         self.params.set_param("status_work_ftp_client", True)
            #         self.ftp_cont.set_params_to_connect(
            #             params_val["ftp_host"],
            #             params_val["ftp_port"],
            #             params_val["ftp_login"],
            #             params_val["ftp_password"]
            #         )

            if "work_buzzer" in params_val:
                if params_val["work_buzzer"]:
                    if self.buzzer.connect():
                        self.buzzer.start_buzzer()
                        self.params.set_param("status_work_buzzer", True)

            # self.binary_parser.subscribeCNB(self.data_hub_callback_cnb)
            # self.binary_parser.subscribeRTCM(self.data_hub_callback_rtcm)

            print("Процесс успешно запущен.")
            self.params.set_param("work_mode", "processing")
            return True

        except Exception as e:
            print(f"Ошибка запуска: {e}")
            if self.params.get_param("status_work_buzzer"):
                self.buzzer.error_buzzer()
            self.stop_controller()
            raise Exception(e)

    def start_and_receive_configure_gnss(self, params_dict):
        speed_settings = b"interfacemode compass compass on\r\n"
        speed_settings += self.settings_comnav.get_bautrate_setting("COM1", 115200)
        speed_settings += self.settings_comnav.get_bautrate_setting("COM2", 115200)
        speed_settings += self.settings_comnav.get_bautrate_setting("COM3", 115200)
        print('[DEBUG]: speed settings = ' + str(speed_settings))
        self.serial_port.send_all_baudrate(speed_settings)
        result_setting = self.serial_port.set_setting(speed_settings)
        if not result_setting:
            raise CE.ControllerExeptions("Ошибка настройки скорости порта.")
        settings = []
        settings += self.settings_comnav.get_base_settings()
        settings += self.settings_comnav.get_fix_settings(params_dict["coords_status"], params_dict["coords_input"])
        if "rtcm_type" in params_dict:
            settings += self.settings_comnav.get_rtcm_settings(params_dict["rtcm_type"], self.satellite_constellations, params_dict["entry_interval_rtcm"], "")
        else:
            settings += self.settings_comnav.get_rtcm_settings("3.2", self.satellite_constellations, params_dict["entry_interval_rtcm"], "")
        settings += self.settings_comnav.get_static_conf()
        if "pps_output" in params_dict:
            if params_dict["pps_output"]:
                settings += self.settings_comnav.get_pps_settings()
        if "event_input" in params_dict:
            if params_dict["event_input"]:
                settings += self.settings_comnav.get_event_settings()
        if params_dict["hardware_checkbox1"] == True or params_dict["hardware_checkbox2"] == True or params_dict["hardware_checkbox3"]:
            settings.append(b"log loglista ontime 1 \r\n")

        print('[DEBUG]: settings = ' + str(settings))

        self.serial_port.set_settings(settings)
        self.serial_port.start()

    # def hardware_port_setting(self, params_dict):
    #     settings_hardware = []
    #     port_settings = {
    #         "COM1": {
    #             "checkbox": params_dict["hardware_checkbox1"],
    #             "comport": params_dict["hardware_comport1"],
    #         },
    #         "COM2": {
    #             "checkbox": params_dict["hardware_checkbox2"],
    #             "comport": params_dict["hardware_comport2"],
    #         },
    #         "COM3": {
    #             "checkbox": params_dict["hardware_checkbox3"],
    #             "comport": params_dict["hardware_comport3"],
    #         },
    #     }

    #     for port, settings in port_settings.items():
    #         if settings["checkbox"]:
    #             if self.get_current_port() == port:
    #                 raise CE.ControllerExeptions(f"Вы подключены к порту {port}. Выберите другой порт для настройки!")
    #             if settings["comport"] != "3.2.radio":
    #                 if len(params_dict["hardware_sats_system"]) == 0:
    #                     raise CE.ControllerExeptions(f"Не выбрана ни одна спутниковая группировка!")
    #             if not settings["comport"]:
    #                 continue
    #             settings_hardware += self.settings_comnav.get_rtcm_settings(
    #                 settings["comport"],
    #                 params_dict["hardware_sats_system"],
    #                 params_dict["hardware_interval_rtcm"],
    #                 port,
    #             )
    #             settings_hardware.append(self.settings_comnav.get_bautrate_setting(port, params_dict[f"hardware_speed{port[3]}"]))

    #     settings_hardware.append(b"unlog loglista ontime 1 \r\n")
    #     if not settings_hardware:
    #         return
    #     if not self.serial_port.set_settings(settings_hardware):
    #         raise CE.ControllerExeptions("Ошибка установки настроек порта")

    # def start_setting_ports(self, params_val):
    #     if params_val["hardware_checkbox1"] == True or params_val["hardware_checkbox2"] == True or params_val["hardware_checkbox3"]:
    #         self.wait_current_port(10)
    #         print(f"Текущий порт: {self.get_current_port()}")
    #         self.serial_port.stop()
    #         self.hardware_port_setting(params_val)
    #         self.serial_port.start()
    #     else:
    #         return

    def start_serial_port(self, port_name):
        '''Подключение к COM порту'''
        if len(port_name) == 0 or port_name == "":
            raise CE.ControllerExeptions("COM порт не выбран. Выберите COM порт.")
        ret = self.serial_port.connect(port_name)
        if not ret:
            raise CE.ControllerExeptions("Ошибка подключения к COM порту.")

    def start_data_hub(self):
        self.data_hub_t = threading.Thread(target=self.data_hub_thread, name="DATA Hub")
        self.status_primary_thread = True
        self.data_hub_t.start()
        return True

    # def start_remote_caster(self, host, port, pwd, mount):
    #     if host == "":
    #         host = "pidt.net"
    #     if port == "":
    #         port = 2101
    #     if pwd == "":
    #         pwd = "1234"
    #     if host == "pidt.net" or mount == "" or mount == "PH":
    #         mount = "PH" + self.get_serial()
    #     self.ntrip_remote.set_settings(host, port, pwd, mount)
    #     self.ntrip_remote.make_ntrip_request()
    #     self.ntrip_remote.start()
    #     self.rtcm_handler.subscribersPackedRTCM(self.ntrip_remote.append_data)

    # def start_local_caster(self, tcp: bool, tcp_port: int):
    #     self.ntrip_local.change_mountpoint("PH" + self.get_serial())
    #     self.ntrip_local.set_tcpout(tcp, tcp_port)
    #     if not self.ntrip_local.launch_str2str():
    #         raise CE.ControllerExeptions("Ошибка запуска локального кастера.")
    #     self.tcp_client.set_tcp_port(self.ntrip_local.tcpserverPort)
    #     time.sleep(0.1)
    #     if not self.tcp_client.connect_tcp():
    #         raise CE.ControllerExeptions("Ошибка подключения сервисного TCP клиента.")
    #     if not self.tcp_client.start_tcp():
    #         raise CE.ControllerExeptions("Ошибка создания потока TCP клиента.")
    #     self.rtcm_handler.subscribersPackedRTCM(self.tcp_client.append_data)
    #     return True

    # def start_tcp_remote(self, host, port):
    #     self.tcp_remote.set_tcp_port(port)
    #     self.tcp_remote.set_tcp_host(host)
    #     if not self.tcp_remote.connect_tcp():
    #         raise CE.ControllerExeptions("Ошибка подключения сервисного TCP клиента.")
    #     if not self.tcp_remote.start_tcp():
    #         raise CE.ControllerExeptions("Ошибка создания потока TCP клиента.")
    #     self.rtcm_handler.subscribersPackedRTCM(self.tcp_remote.append_data)

    def stop_controller(self):
        try:
            # self.binary_parser.unsubscribeCNB(self.data_hub_callback_cnb)
            # self.binary_parser.unsubscribeRTCM(self.data_hub_callback_rtcm)
            if self.params.get_param("data_hub"):
                self.stop_data_hub()
            #     self.params.set_param("data_hub", False)
            # if self.params.get_param("ntrip_client"):
            #     self.ntrip_client.stop()
            #     self.ntrip_client.unsubscribeClient(self.data_thread_callback)
            #     self.ntrip_client.disconnect()
            #     self.params.set_param("ntrip_client", False)
            if self.params.get_param("serial_manager"):
                self.serial_port.disconnect()
                self.serial_port.stop()
            # self.params.set_param("serial_manager", False)
            if self.params.get_param("ascii_parser"):
                self.ascii_parser.stop()
                self.params.set_param("ascii_parser", False)
            # if self.params.get_param("binary_parser"):
            #     self.binary_parser.stop()
            #     self.params.set_param("binary_parser", False)

            # if self.file_recorder.filename != "":
            #     self.ftp_cont.set_status_record(self.file_recorder.filename, 1)
            # self.file_recorder.close_file()

            # if self.params.get_param("ntrip_local"):
            #     self.tcp_client.disconnect()
            #     self.tcp_client.stop_tcp()
            #     self.ntrip_local.stop_str2str()
            #     self.params.set_param("ntrip_local", False)
            # if self.params.get_param("ntrip_remote"):
            #     self.ntrip_remote.disconnect()
            #     self.ntrip_remote.stop()
            #     self.params.set_param("ntrip_remote", False)
            # if self.params.get_param("to_com_manager"):
            #     self.to_com_obj.stop()
            #     self.params.set_param("to_com_manager", False)
            # if self.params.get_param("tcp_remote"):
            #     self.tcp_remote.disconnect()
            #     self.tcp_remote.stop_tcp()
            #     self.params.set_param("tcp_remote", False)
            if self.params.get_param("status_work_buzzer"):
                self.buzzer.stop_buzzer()
            print("Процесс успешно остановлен.")
            # self.params.set_param("work_mode", "default")
        except Exception as e:
            # self.params.set_param("work_mode", "error")
            raise Exception(f"Stop ERROR {e}")

    def stop_data_hub(self):
        if not self.status_primary_thread:
            return
        self.status_primary_thread = False
        if self.data_hub_t is not None:
            self.data_hub_t.join()
            self.data_hub_t = None

    # def device_delete_file(self, filepath):
    #     try:
    #         file_path = os.path.join(self.file_recorder.file_path, filepath)
    #         if os.path.exists(file_path):
    #             os.remove(file_path)
    #             print(f"Файл {filepath} успешно удален.")
    #         else:
    #             print(f"Файл {filepath} не существует.")
    #     except Exception as e:
    #         print(f"Ошибка при удалении файла {filepath}: {e}.")

    # def device_update(self):
    #     if platform.system() == "Linux":
    #         os.system("git pull --rebase")
    #         os.system("venv/bin/pip install -r requirements.txt")
    #         os.system("systemctl restart pisun.service")
    #     else:
    #         raise SystemError("Автоматическое обновление недоступно на вашей операционной системе.")

    def _format_size(self, size_bytes):
        suffixes = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(suffixes) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {suffixes[i]}"