
class l:
    # TODO: Make singleton (through module)

    # Use bit patterns for deciding which features to use. 
    # This has the benefit of making different logging options easily combinable, like: 
    # logger = l(l.STDOUT | l.FILE, "/tmp/log.txt")
    STDOUT        = 0b0001
    OPENTELEMETRY = 0b0010
    FILE          = 0b0100

    def __init__(self, opts, log_file="LOG_OUTPUT.txt"):
        self.stdout = bool(opts & 0b0001)
        self.open_telemetry = bool(opts & 0b0010)
        self.file = bool(opts & 0b0100)

        self.log_file = log_file

    def log(self, input):
        if self.stdout:
            print(input)

        if self.FILE:
            with open(self.log_file, "a") as f:
                f.write(input)
        
        if self.open_telemetry:
            # TODO: Actually log here
            pass
