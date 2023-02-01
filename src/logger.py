class logger:
    """
    A customizable logger.

    A logger capable of logging to stdout, a specified log file or through log aggregation like open-telemetry.

    Example:
    ```
    # Creates a logger which writes to stdout aswell as /tmp/log.txt
    logger = logger(logger.STDOUT | logger.FILE, "/tmp/log.txt")
    ```
    """

    # Use bit patterns for deciding which features to use.
    # This has the benefit of making different logging options easily combinable, like:
    # logger = l(l.STDOUT | l.FILE, "/tmp/log.txt")
    STDOUT = 0b0001
    OPENTELEMETRY = 0b0010
    FILE = 0b0100

    def __init__(self, opts, log_file="LOG_OUTPUT.txt"):
        """
        Use bit patterns for deciding which features to use.
        This has the benefit of making different logging options easily combinable, like:
        logger = l(l.STDOUT | l.FILE, "/tmp/log.txt")
        """

        # Clamp the resulting values
        self.stdout = bool(opts & self.STDOUT)
        self.open_telemetry = bool(opts & self.OPENTELEMETRY)
        self.file = bool(opts & self.FILE)

        self.log_file = log_file

        # if a invalid arg is given we toggle self.stdout just to be sure.
        if not opts or opts > self.FILE:
            self.stdout = True

        # init message for the logger
        message = "Starting logging with options: "
        if self.stdout:
            message += "stdout, "
        if self.open_telemetry:
            message += "open_telemetry, "
        if self.file:
            message += f"file ({self.log_file}), "

        # remove the trailing ", "
        self.log(message[:-2])

    # Logs the input through the objects chosen options
    def log(self, input):
        """
        Logs the input.
        """
        if self.stdout:
            print(input)

        if self.file:
            with open(self.log_file, "a") as f:
                f.write(input + "\n")

        if self.open_telemetry:
            # TODO: Actually log here
            pass
