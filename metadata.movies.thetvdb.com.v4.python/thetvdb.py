from resources.lib import actions
from resources.lib.exception_logger import log_exception

with log_exception():
    actions.run()
