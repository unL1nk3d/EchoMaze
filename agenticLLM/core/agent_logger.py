import logging
import os
from datetime import datetime

class AgentLogger:
    """Centralized logger for EchoMaze Agentic operations."""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentLogger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        # Determine log path (root of project)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_file = os.path.join(base_dir, "echomaze_agent.log")
        
        self.logger = logging.getLogger("EchoMazeAgent")
        self.logger.setLevel(logging.DEBUG)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            # File Handler
            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setLevel(logging.DEBUG)
            
            # Format
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            
            self.logger.addHandler(fh)
            
    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)

    def debug(self, msg):
        self.logger.debug(msg)

    def warning(self, msg):
        self.logger.warning(msg)

def get_logger():
    return AgentLogger()
