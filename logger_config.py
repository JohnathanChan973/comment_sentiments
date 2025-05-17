from pathlib import Path
import logging

def get_logger(log_name: str, level=logging.INFO, stream: bool=False) -> logging.Logger:
    log_dir = Path.cwd() / "data" / "logs" 
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{log_name}.log"

    logger = logging.getLogger(log_name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(processName)s - %(message)s")

        file_handler = logging.FileHandler(log_path, encoding='utf-8') # To properly handle strange characters
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        if stream:    
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    return logger
