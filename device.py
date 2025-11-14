import uiautomator2 as u2
import logging

logger = logging.getLogger(__name__)


def connect_device(serial=None):
    try:
        if serial:
            device = u2.connect(serial)
        else:
            device = u2.connect()

        return device
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        raise


def get_device_info(device):
    return device.info
