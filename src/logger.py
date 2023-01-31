


class l:
    # TODO: Make singleton

    STDOUT        = 0b0001
    OPENTELEMETRY = 0b0010
    FILE          = 0b0100

    def __init__(self, opts, log_file="LOG_OUTPUT.txt"):
        self.stdout = opts & 0b0001
        self.open_telemetry = opts & 0b0010
        self.file = opts & 0b0100

        self.log_file = log_file

    def log(self, input):
        pass
