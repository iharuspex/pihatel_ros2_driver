import math

'''
dict_defenition = {
    "satelites": [
        {"name": "G01", "snr": 12, "freq_num": 4, "name_color": "G", "azimut": 359, "elevation": 90}
        {"name": "G01", "snr": 12, "freq_num": 4, "name_color": "G", "azimut": 359, "elevation": 90}
        {"name": "G01", "snr": 12, "freq_num": 4, "name_color": "G", "azimut": 359, "elevation": 90}
    ]
}
"name_color": "G" - название системы GREC
'''


class for_print:
    def __init__(self):
        self.name = []
        self.azimut = []
        self.elevation = []
        self.snr = []
        self.freq_num = []
        self.name_color = []

    def clear(self):
        self.name = []
        self.azimut = []
        self.elevation = []
        self.snr = []
        self.freq_num = []
        self.name_color = []

    def get_dict(self):
        '''Возвращает массив satelites с вот такими обьектами
            - "name": self.name[i],
            - "snr": self.snr[i],
            - "freq_num": self.freq_num[i],
            - "name_color": self.name_color[i],
            - "azimut": self.azimut[i],
            - "elevation": self.elevation[i],
            - "x_skyplot": x,
            - "y_skyplot": y
        Доп параметры
            - "x_min": -90,
            - "x_max": 90,
            - "y_min": -90,
            - "y_max": 90,
        '''
        ret_dict = {}
        ret_dict["x_min"] = -90
        ret_dict["x_max"] = 90
        ret_dict["y_min"] = -90
        ret_dict["y_max"] = 90
        ret_dict["satelites"] = []
        for i in range(len(self.name)):
            x ,y = self._calc_x_y(self.azimut[i], self.elevation[i])
            if self.azimut[i] == 0 and self.elevation[i] == 0:
                continue
            if self.elevation[i] > 90 or self.elevation[i] < 0:
                continue
            ret_dict["satelites"].append({"name": self.name[i],
                                          "snr": self.snr[i],
                                          "freq_num": self.freq_num[i],
                                          "name_color": self.name_color[i],
                                          "azimut": self.azimut[i],
                                          "elevation": self.elevation[i],
                                          "x_skyplot": x,
                                          "y_skyplot": y})
        return ret_dict

    def _calc_x_y(self, azimut, elevation) -> (float, float):
        r = 90 - elevation
        tetta = azimut

        x = -r*math.sin(math.radians(-tetta))
        y = r*math.cos(math.radians(-tetta))
        return x,y