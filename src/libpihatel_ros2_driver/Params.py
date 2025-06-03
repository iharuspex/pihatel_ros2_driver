
class Params:
    def __init__(self, params_defenition, params=None):
        self._params = {}
        self.params_values = params_defenition
        for key, value in self.params_values.items():
            self._params[key] = value["default"]

        if params is not None:
            self.update(params)

    def update(self, params):

        for key, value in params.items():
            if key not in self._params:
                raise ValueError(f"Parameter '{key}' does not exist.")
            # print(key, value, type(value))
            self.set_param(key, value)

    def set_param(self, param, value):

        if param not in self._params:
            raise ValueError(f"Parameter '{param}' does not exist.")

        if not isinstance(value, self.params_values[param]["type"]):
            raise ValueError(f"Param '{param}' has type '{type(value)}', but shoud be '{self.params_values[param]['type']}'")

        if "values" in self.params_values[param]:
            if self.params_values[param]["type"] == list:
                values = self.params_values[param]["values"]
                for item in value:
                    if item not in values:
                        raise ValueError(
                            f"Item in '{param}' equal '{item}', acceptable values '{self.params_values[param]['values']}'")
            else:
                if value not in self.params_values[param]["values"]:
                    raise ValueError(f"Unacceptable value '{param}' equal '{value}', acceptable values '{self.params_values[param]['values']}'")

        if self.params_values[param]["type"] == list:
            default_value = self.params_values[param]["default"]
            type_value = type(default_value[0])
            for item in value:
                if not isinstance(item, type_value):
                    raise ValueError(f"Param '{param}' should be a list of {type(type_value)}.")

        self._params[param] = value
        return True

    def get_param(self, param):
        if param not in self._params:
            raise KeyError(f"Parameter '{param}' does not exist.")

        return self._params[param]

    def to_dict(self):
        return self._params