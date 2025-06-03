class CustomException(Exception):
    def __init__(self, text):
        self.txt = text

    class ParserExceptions(Exception):
        def __init__(self, text):
            self.txt = text

    class ControllerExeptions(Exception):
        def __init__(self, text):
            self.txt = text