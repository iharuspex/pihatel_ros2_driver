import struct
from enum import Enum


POLYCRC32 = 0xEDB88320  # CRC32 polynomial


class CNBHeader:
    def __init__(self):
        self.message_id = 0
        self.gps_time = 0.0


class SatDataUnit:
    def __init__(self):
        self.sys = ""
        self.num = 0
        self.S = [0, 0, 0, 0, 0, 0]
        self.azimuth = 0
        self.elevation = 0


class CNBMessage911:
    def __init__(self):
        self.sats: list[SatDataUnit] = []
        self.satnum: int = 0


class CNBMessage101:
    def __init__(self):
        self.clock_status = None
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.milliseconds = None
        self.utc_status = None


class ClockStatus(Enum):
    VALID = 0
    CONVERGING = 1
    ITERATING = 2
    INVALID = 3
    ERROR = 4


class UtcStatus(Enum):
    Invalid = 0
    Valid = 1
    Warning = 2


class CnbHandler:
    def __init__(self):
        pass

    def _checksum_32_calc(self, buff, calc_len):
        crc = 0
        for i in range(calc_len):
            crc ^= buff[i]
            for j in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ POLYCRC32
                else:
                    crc >>= 1
        return crc

    def gps_time_to_unixtime(self, week, rcvTOW, leapS):
        UTC_time = 604800 * week + rcvTOW + 315964800 - leapS
        return UTC_time

    def prn_to_satn(self, prn):
        retprn = prn
        if 1 <= prn <= 32:  # GPS
            retprn = prn
        elif 38 <= prn <= 61:  # GLONASS
            retprn = prn - 37
        elif 62 <= prn <= 70:  # IRNSS
            retprn = prn - 61
        elif 120 <= prn <= 144:  # SBAS
            retprn = prn
        elif 141 <= prn <= 203:  # BD2
            retprn = prn - 140
        elif 71 <= prn <= 106:  # Galileo
            retprn = prn - 70
        elif 131 <= prn <= 140:  # QZSS
            retprn = prn - 130
        else:  # Unknown
            retprn = prn
        return retprn

    def prn_to_satsystem(self, prn):
        system_char = ' '

        if 1 <= prn <= 32:  # GPS
            system_char = 'G'
        elif 38 <= prn <= 61:  # GLONASS
            system_char = 'R'
        elif 62 <= prn <= 70:  # IRNSS
            system_char = 'I'
        elif 120 + 100 <= prn <= 144 + 100:  # SBAS
            system_char = 'S'
        elif 141 <= prn <= 203:  # BD2
            system_char = 'C'
        elif 71 <= prn <= 106:  # Galileo
            system_char = 'E'
        elif 131 <= prn <= 140:  # QZSS
            system_char = 'Q'
        else:  # Unknown
            system_char = 'N'
        return system_char

    def sys_to_char(self, sys):
        system_char = ' '

        if sys == 0:
            system_char = 'G'
        elif sys == 1:
            system_char = 'R'
        elif sys == 2:
            system_char = 'S'
        elif sys == 3:
            system_char = 'E'
        elif sys == 4:
            system_char = 'C'
        elif sys == 7:
            system_char = 'N'

        return system_char

    def is_valid(self, buff, offset):
        # Проверка пакета на валидность, если не прошел, то -1, если прошел, то length_packet
        if buff[offset] == 0xAA and buff[offset + 1] == 0x44 and buff[offset + 2] == 0x12:
            len_payload = struct.unpack("<H", buff[offset + 8:offset + 10])[0]
            len_packet = len_payload + buff[offset + 3]

            buff_temp = buff[offset:offset + len_packet]
            checksum_calc = self._checksum_32_calc(buff_temp, len_packet)
            checksum_received = struct.unpack("<I", buff[offset + len_packet:offset + len_packet + 4])[0]

            if checksum_calc == checksum_received:
                return len_packet + 4
            else:
                return 0  # ERROR_VALID_CHECKSUM_NOT_MATCH
        else:
            return -1  # ERROR_VALID_PREAMBLE_NOT_FOUND

    def parse_header(self, buff):
        header = CNBHeader()
        header.message_id = struct.unpack("<H", buff[4:6])[0]
        week_gps = struct.unpack("<H", buff[14:16])[0]
        time_gps_week = struct.unpack("<I", buff[16:20])[0] / 1000.0
        header.gps_time = self.gps_time_to_unixtime(week_gps, time_gps_week, 0)
        return header

    def parce_cnb_911(self, buff):
        m911 = CNBMessage911()
        length_header = buff[3]
        m911.satnum = int(buff[length_header])
        freq_flag = int(buff[length_header + 5])
        freqs = 0

        if freq_flag & 0x01:
            freqs += 1
        if freq_flag & 0x02:
            freqs += 1
        if freq_flag & 0x04:
            freqs += 1
        if freq_flag & 0x08:
            freqs += 1
        if freq_flag & 0x10:
            freqs += 1
        if freq_flag & 0x20:
            freqs += 1

        for i in range(m911.satnum):
            unit = SatDataUnit()
            prn = int(buff[length_header + i * (4 + freqs * 4) + 6])
            unit.azimuth = int.from_bytes(buff[length_header + i * (4 + freqs * 4) + 7: length_header + i * (4 + freqs * 4) + 9], byteorder='little')
            unit.elevation = int(buff[length_header + i * (4 + freqs * 4) + 9])

            status = [int(buff[length_header + i * (4 + freqs * 4) + 4 * j + 10]) for j in range(freqs)]
            snr = [int(buff[length_header + i * (4 + freqs * 4) + 4 * j + 11]) for j in range(freqs)]
            rms = [int(buff[length_header + i * (4 + freqs * 4) + 4 * j + 12]) for j in range(freqs)]

            unit.num = self.prn_to_satn(prn)
            unit.sys = self.prn_to_satsystem(prn)

            unit.S = snr
            name = self.sys_to_char(unit.sys) + str(unit.num)
            m911.sats.append(unit)

        return m911

    def parce_cnb_101(self, buff):
        m101 = CNBMessage101()
        length_header = buff[3]

        m101.clock_status = struct.unpack_from('<i', buff, length_header + 0)[0]
        m101.year = struct.unpack_from('<I', buff, length_header + 28)[0]
        m101.month = struct.unpack_from('<B', buff, length_header + 32)[0]
        m101.day = struct.unpack_from('<B', buff, length_header + 33)[0]
        m101.hour = struct.unpack_from('<B', buff, length_header + 34)[0]
        m101.minute = struct.unpack_from('<B', buff, length_header + 35)[0]
        m101.milliseconds = struct.unpack_from('<I', buff, length_header + 36)[0]
        m101.utc_status = struct.unpack_from('<i', buff, length_header + 40)[0]

        return m101