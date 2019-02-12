"""
Logging formatter factory

@author: Jason Zhu
@email: jason_zhuyx@hotmail.com
"""

import logging


def factory(fmt="%(levelno)s: %(msg)s"):
    """
    Logging formatter factory to get colored logging formatter
    """
    return LoggingFormatter(fmt, use_color=True)


class LoggingFormatter(logging.Formatter):
    """
    A colored formatter for console logging
    """
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
    # The first code (before semi-colon) -
    # 0=Normal; 1=Bold; 2=Dim; 4=Underline; 5=Blink; 7=Inverse; 8=Hidden
    # The bg color + 40, foreground + 30; lighter color + 60 more
    # The sequences to set color text
    SEQ_BFONT = "\033[1m"   # bold font
    SEQ_COLOR = "\033[1;%dm"
    SEQ_DTIME = "\033[90m"  # dim
    SEQ_MNAME = "\033[36m"  # cyan for module name
    SEQ_GREEN = "\033[32m"  # green
    SEQ_RESET = "\033[0m"

    COLORS = {
        'CRITICAL': MAGENTA,
        'ERROR': RED,
        'WARNING': YELLOW,
        'INFO': WHITE,
        'DEBUG': BLUE,
    }

    FORMATS = {
        'DEFAULT':
            "\n%(asctime)s [%(module)s] %(message)s",
        logging.DEBUG:
            "\n%(asctime)s [%(name)s #%(lineno)d] %(levelname)s: %(message)s",
        logging.INFO:
            "\n%(asctime)s [%(name)s]: %(message)s",
        logging.WARNING:
            "\n%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        logging.ERROR:
            "\n%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        logging.CRITICAL:
            "\n%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    }

    def __init__(self, fmt="%(levelno)s: %(msg)s", use_color=True):
        """
        Initialize an instance of LoggerFormatter
        """
        logging.Formatter.__init__(self, fmt)
        self.use_color = use_color is None or use_color is True

    def format(self, record):
        """
        Format logging text and record level with colors
        """
        orig_format = self._fmt
        name_format = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])

        if self.use_color:
            time_format = self.SEQ_DTIME + '%(asctime)s' + self.SEQ_RESET
            name_format = name_format.replace('%(asctime)s', time_format)
            name = bold_name = record.levelname

            record.name = self.SEQ_GREEN + record.name + self.SEQ_RESET

            if record.levelno > logging.WARNING:
                bold_name = self.SEQ_BFONT + name

            if record.levelname in self.COLORS:
                colored_seq = self.SEQ_COLOR % (30 + self.COLORS[name])
                colored_name = colored_seq + bold_name + self.SEQ_RESET
                record.levelname = colored_name

        self._fmt = name_format
        result = logging.Formatter.format(self, record)
        self._fmt = orig_format

        return result
