class SettingsComnav:
    base_settings = [
        b"interfacemode compass compass on\r\n",
        b"unlockoutall\r\n",
        b"UNDULATION user 0.0000\r\n",
        b"set anthigh 0.000\r\n",
        b"unlogall\r\n",
        b"rtkrefmode 0\r\n",
        b"ECUTOFF 0.0\r\n",
        b"BD2ECUTOFF 0\r\n",
        b"log version ontime 1\r\n",
    ]

    event_conf = [
        b"markcontrol mark1 enable positive 0 200\r\n",
        b"log marktimeb onnew\r\n"
        b"log markposb onnew\r\n"
    ]

    pps_conf = [
        b"ppscontrol enable positive 1 1000\r\n"
    ]

    static_conf_pre = [
        b"glorawephemb ontime 10\r\n",
        b"rawephemb ontime 10\r\n",
        b"galephemerisb ontime 10\r\n",
        b"bd2rawephemb ontime 10\r\n",
        b"rangecmpb ontime 1\r\n",
        b"satmsgb ontime 1\r\n",
        b"timeb ontime 5\r\n"
        b"bestxyzb ontime 1\r\n",
        b"ionutcb ontime 1\r\n",
        b"bestposa ontime 1\r\n"
    ]

    rtk_settings = [
        b"interfacemode compass compass\r\n",
        b"fix none\r\n",
        b"log bestposa ontime 1\r\n",
        b"interfacemode auto auto on\r\n"
    ]

    predefined_data = {
        "3.0": [b"rtcm1005b ontime 5\r\n", b"rtcm1033b ontime 10\r\n"],
        "3.2": [b"rtcm1006b ontime 5\r\n", b"rtcm1033b ontime 10\r\n"],
        "3.2.radio": [b"rtcm1074b ontime",
                      b"rtcm1084b ontime",
                      b"rtcm1094b ontime",
                      b"rtcm1124b ontime",
                      b"rtcm1005b ontime",
                      b"rtcm1033b ontime"
                      ]
    }

    # settings_radio = [
    #     b"LOCKOUTSYSTEM BD3\r\n"
    # ]

    satellite_commands = {
        "GPS": {
            "3.0": [b"rtcm1004b ontime"],
            "3.2": [b"rtcm1075b ontime"],
        },
        "GLO": {
            "3.0": [b"rtcm1012b ontime"],
            "3.2": [b"rtcm1085b ontime"],
        },
        "GAL": {
            "3.0": [],
            "3.2": [b"rtcm1095b ontime"],
        },
        "BDS": {
            "3.0": [],
            "3.2": [b"rtcm1125b ontime"],
        },
    }

    def __init__(self):
        pass

    def get_rtk_settings(self) -> list:
        return self.rtk_settings

    def get_pps_settings(self) -> list:
        return self.pps_conf

    def get_event_settings(self) -> list:
        return self.event_conf

    def get_rtcm_settings(self, rtcm_type: str, sats: list, interval: int, com_port: str) -> list:
        rtcm_data = []

        if rtcm_type == "3.2.radio":
            if com_port:
                rtcm_data.append(b"Unlogall " + com_port.encode() + b"\r\n")
                rtcm_data.extend(f"log {com_port} {unit.decode()} {interval}\r\n".encode() for unit in self.predefined_data[rtcm_type])
            else:
                rtcm_data.extend(f"log {unit.decode()} {interval}\r\n".encode() for unit in self.predefined_data[rtcm_type])

            # rtcm_data.extend(f"{unit.decode()}".encode() for unit in self.settings_radio)
            return rtcm_data

        else:
            if com_port:
                rtcm_data.append(b"Unlogall " + com_port.encode() + b"\r\n")
                rtcm_data.extend(f"log {com_port} {unit.decode()}".encode() for unit in self.predefined_data[rtcm_type])
            else:
                rtcm_data.extend(f"log {unit.decode()}".encode() for unit in self.predefined_data[rtcm_type])
            for sat in sats:
                if sat in self.satellite_commands:
                    commands = self.satellite_commands[sat][rtcm_type]

                    if com_port:
                        if com_port == "COM1":
                            rtcm_data.extend(f"log com1 {conf.decode()} {interval}\r\n".encode() for conf in commands)
                        elif com_port == "COM2":
                            rtcm_data.extend(f"log com2 {conf.decode()} {interval}\r\n".encode() for conf in commands)
                        elif com_port == "COM3":
                            rtcm_data.extend(f"log com3 {conf.decode()} {interval}\r\n".encode() for conf in commands)
                    else:
                        rtcm_data.extend(f"log {conf.decode()} {interval}\r\n".encode() for conf in commands)
            return rtcm_data

    def get_fix_settings(self, coords_status: str, coords: list) -> list:
        '''Возвращает настройки фиксированных координат (авто/фикс)'''
        return_data = []
        if coords_status == "auto":
            return_data.append(b"fix auto\r\n")
        elif coords_status == "fix":
            return_data.append(
                f"fix position {float(coords[0]):.9f} {float(coords[1]):.9f} {float(coords[2]):.5f}\r\n".encode())
        return return_data

    def get_base_settings(self):
        return_data = []
        for unit in self.base_settings:
            return_data.append(unit)
        return return_data

    def get_bautrate_setting(self, com_port: str, speed: int):
        '''Возвращает строку с настройкой скорости порта
        :param com_port: принимаемые значения (com1 com2 com3)'''
        if com_port not in ["COM1", "COM2", "COM3"]:
            raise ValueError(f"ValueError '{com_port}' shoud be 'COM1 COM2 COM3'")
        return f"com {com_port} {speed}\r\n".encode()

    def get_static_conf(self):
        return_data = []
        for unit in self.static_conf_pre:
            return_data.append(f"log {unit.decode()}".encode())
        return return_data
