import uiautomator2 as u2
import logging

logger = logging.getLogger(__name__)


def connect_device(serial=None):
    try:
        if serial:
            device = u2.connect(serial)
            logger.info(f"Connected to device: {serial}")
        else:
            device = u2.connect()
            logger.info("Connected to default device")
        
        logger.info(f"Device info: {device.info}")
        return device
    except Exception as e:
        logger.error(f"Failed to connect to device: {e}")
        raise


def get_device_info(device):
    return device.info
