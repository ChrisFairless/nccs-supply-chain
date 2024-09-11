# This file extends CLIMADA Data API Client, allowing the client to check for the existence of already-downloaded 
# datasets in its cache before it redownloads them.
#
# The methods where we want to check the cache first are overloaded in the new class. A decorator @check_cache_first is 
# added to each of them (with the method's signature staying the same)


import logging
from climada.util.api_client import Client

LOGGER = logging.getLogger(__name__)

class NCCSClimadaClient(Client):
    def __init__(self, cache_enabled=None):
        super().__init__(cache_enabled)

    @staticmethod
    def check_cache_first(func):
        def wrapper(self, *args, **kwargs):
            api_logger = logging.getLogger('climada.util.api_client')
            original_log_level = api_logger.getEffectiveLevel()
            original_online_status = self.online

            try:
                if self.cache.enabled:
                    LOGGER.debug('Checking the cache for existing API data')
                    self.online = False           # When the client is offline it checks its cache instead of downloading data
                    api_logger.setLevel('ERROR')  # The client throws a warning when it accesses the cache and we don't want to hear it 
                    return func(self, *args, **kwargs)
            except Client.NoConnection:
                LOGGER.debug('...No data found in the API cache')
            finally:
                # Set things back to how they started 
                api_logger.setLevel(original_log_level)
                self.online = original_online_status

            # If that didn't work, do it the old fashioned way
            LOGGER.debug(f'Downloading from the CLIMADA data API via {func.__name__}')
            return func(self, *args, **kwargs)
        return wrapper
    
    @check_cache_first
    def get_litpop(self, *args, **kwargs):
        return super().get_litpop(*args, **kwargs)
    
    @check_cache_first
    def get_exposures(self, *args, **kwargs):
        return super().get_exposures(*args, **kwargs)

    @check_cache_first
    def get_hazard(self, *args, **kwargs):
        return super().get_hazard(*args, **kwargs)
    
    # TODO write some tests that run requests in a temporary cache