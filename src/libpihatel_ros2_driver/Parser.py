import queue
import threading
from typing import Tuple

from libpihatel_ros2_driver import CnbHandler, RtcmHandler
from libpihatel_ros2_driver.ForPrint import for_print
from libpihatel_ros2_driver.Params import Params

params_defenition = {
    "sats_num":       {"type": int, "default": 0},
    "serial":         {"type": str, "default": ""},
    "fix_status":     {"type": str, "default": "undef"},
    "current_coords": {"type": list, "default": [0.0, 0.0, 0.0]},
    "current_port":   {"type": str, "default": ""},
}


class ParserDataASCII:
    data_queue = queue.Queue()
    is_running = False
    params = Params(params_defenition)

    def __init__(self):
        self.func = None

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self.thread_data, name="ASCII Parser")
        self.thread.start()
        return self.is_running

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.data_queue.put(b'unsleep')
            self.thread.join()

    def set_serial(self, serial):
        if self.is_running and self.func != None:
            self.func(serial)

    def thread_data(self):
        while self.is_running:
            try:
                data_out = self.data_queue.get(timeout=1)
            except Exception:
                continue

            if b"GPSCARD" in data_out:
                data = data_out[data_out.index(b"GPSCARD"):]
                fields = data.decode('latin-1', errors='ignore').split()
                if len(fields) >= 3:
                    field_3 = fields[2].strip("\"")
                    field_3 = field_3[:8]
                    serial_forname = field_3
                    try:
                        self.params.set_param("serial", serial_forname)
                    except Exception as e:
                        print(f"ERROR set_serial {e}")
            if b"#BESTPOSA" in data_out:
                data = data_out[data_out.index(b"#BESTPOSA"):]
                fields = data.decode('latin-1', errors='ignore').split(',')
                if len(fields) >= 23:
                    try:
                        fix_status = fields[10]
                        self.params.set_param("fix_status", fields[10])
                        coords_current = [float(fields[11]), float(fields[12]), float(fields[13])]
                        self.params.set_param("current_coords", coords_current)
                        self.params.set_param("sats_num", int(fields[22]))
                    except Exception as e:
                        print(f"Ошибка в парсере! {e}")

            if b"#LOGLISTA" in data_out:
                data = data_out[data_out.index(b"#LOGLISTA"):]
                fields = data.decode('latin-1', errors='ignore').split(',')
                if len(fields) >= 3:
                    fields = fields[1]
                    current_port = fields
                    try:
                        self.params.set_param("current_port", current_port)
                    except Exception as e:
                        print(f"ERROR current_port {e}")

    def append_data(self, bytearray_data):
        self.data_queue.put(bytearray_data)


class ParserDataBinary:
    data_queue = queue.Queue()
    _is_running = False
    _thread = None
    _parse_point = 0
    _current_time = 0.0
    _time_status = False
    subscribersRTCM = []
    subscribersCNB = []
    buff = b''
    _CNB_LEN_CRC = 4
    ploted_data = for_print()

    def __init__(self):
        pass

    def start(self):
        if self._is_running:
            print("Ошибка запуска парсера! Уже запущен.")
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._thread_data, name="BIN Parser")
        self._thread.start()
        return self._is_running

    def stop(self):
        if not self._is_running:
            print("Повторная попытка остановить парсер. Уже остановлен.")
            return
        self._is_running = False
        self.data_queue.put(b'unsleep')
        self._thread.join()
        self.ploted_data.clear()

    def append_data(self, bytearray_data):
        self.data_queue.put(bytearray_data)

    def get_current_time(self):
        if self._time_status:
            return self._current_time
        else:
            return 0.0

    def subscribeRTCM(self, func):
        if func not in self.subscribersRTCM:
            self.subscribersRTCM.append(func)

    def unsubscribeRTCM(self, func):
        if func in self.subscribersRTCM:
            self.subscribersRTCM.remove(func)

    def subscribeCNB(self, func):
        if func not in self.subscribersCNB:
            self.subscribersCNB.append(func)

    def unsubscribeCNB(self, func):
        if func in self.subscribersCNB:
            self.subscribersCNB.remove(func)

    def _thread_data(self):
        while self._is_running:
            try:
                data_out = self.data_queue.get(timeout=1)
                self.buff += data_out[:len(data_out)]
            except Exception:
                continue

            while True:
                packet_find = self._find_packet()
                packet_index, type = packet_find

                if packet_index == -1:
                    self.buff = b''
                    self._parse_point = 0
                    break
                elif packet_index == -2:
                    break

                if type == "rtcm3":
                    packet_len = self._handle_rtcm()
                elif type == "cnb":
                    packet_len = self._handle_cnb()
                else:
                    packet_len = -1

                if packet_len > 0:
                    if type == "rtcm3":
                        temp_buff = self.buff[self._parse_point:self._parse_point + packet_len]
                        for notify in self.subscribersRTCM:
                            notify(temp_buff)
                    elif type == "cnb":
                        temp_buff = self.buff[self._parse_point:self._parse_point + packet_len]
                        for notify in self.subscribersCNB:
                            notify(temp_buff)

                    self.buff = self.buff[packet_index + packet_len:]
                    self._parse_point = 0
                else:
                    print("Invalid packet found!")
                    self._parse_point += 1

    def _find_packet(self) -> Tuple[int, str]:
        data_type = None
        for i in range(self._parse_point, len(self.buff)):
            self._parse_point = i
            if self.buff[i] == 0xd3:
                ret = self._find_packet_rtcm3()
                data_type = "rtcm3"
            elif self.buff[i] == 0xAA:
                ret = self._find_packet_cnb()
                data_type = "cnb"
            else:
                continue

            if ret == -2:
                return -2, data_type
            elif ret == -1:
                continue

            return ret, data_type
        return -1, data_type

    def _find_packet_rtcm3(self) -> int:
        i = self._parse_point
        if self.buff[i] != 0xd3:
            return -1
        if len(self.buff) - i < 4:
            return -2
        pack_len = (self.buff[i + 2] | (self.buff[i + 1] << 8))
        if (pack_len & 0xfc00) != 0:
            return -1
        if (len(self.buff) - i) < pack_len + 6:
            return -2
        return i

    def _find_packet_cnb(self) -> int:
        i = self._parse_point
        if self.buff[i] != 0xAA:
            return -1
        if len(self.buff) - i < 4:
            return -2
        if self.buff[i + 1] != 0x44:
            return -1
        if self.buff[i + 2] != 0x12:
            return -1
        length_header = self.buff[i + 3]
        if (len(self.buff) - i) < length_header:
            return -2
        length_message_frm_header = (self.buff[i + 8] | (self.buff[i + 9] << 8))
        if length_message_frm_header + length_header + self._CNB_LEN_CRC > (len(self.buff) - i):
            return -2
        return i

    def _handle_rtcm(self):
        rtcm = RtcmHandler.RtcmHandler()
        packet_len = rtcm.is_valid(self.buff, self._parse_point)
        if packet_len <= 0:
            print("Невалидный RTCM пакет!")
            return packet_len
        temp = self.buff[self._parse_point:self._parse_point + 5]
        type = rtcm.get_rtcm_type(temp)
        return packet_len

    def _handle_cnb(self):
        cnb = CnbHandler.CnbHandler()
        packet_len = cnb.is_valid(self.buff, self._parse_point)
        if packet_len <= 0: return packet_len
        buff_temp = self.buff[self._parse_point:self._parse_point + packet_len]
        h = cnb.parse_header(buff_temp)

        self._current_time = h.gps_time

        if h.message_id == 101:
            m101 = cnb.parce_cnb_101(buff_temp)
            if m101.clock_status == CnbHandler.ClockStatus.VALID.value and m101.utc_status == CnbHandler.UtcStatus.Valid.value:
                if self._time_status != True and h.gps_time > 1726489158:
                    self._time_status = True

        elif h.message_id == 911:
            m911 = cnb.parce_cnb_911(buff_temp)
            temp_ploted_data = for_print()
            for i in range(len(m911.sats)):
                temp_ploted_data.name.append(str(m911.sats[i].sys) + str(m911.sats[i].num))
                temp_ploted_data.snr.append(0)
                temp_ploted_data.freq_num.append(0)
                for j in range(len(m911.sats[i].S)):
                    if m911.sats[i].S[j] != 0:
                        temp_ploted_data.freq_num[i] += 1
                    if temp_ploted_data.snr[i] < m911.sats[i].S[j]:
                        temp_ploted_data.snr[i] = m911.sats[i].S[j]
                temp_ploted_data.elevation.append(m911.sats[i].elevation)
                temp_ploted_data.azimut.append(m911.sats[i].azimuth)
                temp_ploted_data.name_color.append(m911.sats[i].sys)
            self.ploted_data = temp_ploted_data
        return packet_len
