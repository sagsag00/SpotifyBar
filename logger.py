import colorlog

handler = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter(
    "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler.setFormatter(formatter)
 
# Set up the logger
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(colorlog.INFO)  