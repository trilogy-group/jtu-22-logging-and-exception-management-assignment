import logging

# Set baseConfig level to INFO to log all messages except the DEBUG ones
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s :: %(levelname)s :: %(message)s",
)

logger = logging.getLogger(__name__)
