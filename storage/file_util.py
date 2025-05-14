import os
import re

class FileUtils:
    @staticmethod
    def sanitize_filename(filename: str, reserved_names=None, max_length: int = 100) -> str:
        """
        Sanitize a filename to be safe for use across operating systems.
        
        Args:
            filename: The original filename
            reserved_names: Optional set of reserved names (defaults to Windows reserved names)
            max_length: Maximum allowed filename length
        
        Returns:
            A sanitized filename string
        """
        if reserved_names is None:
            reserved_names = {
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            }

        # Replace restricted characters with a dash
        sanitized = re.sub(r'[\\/*:?|"<>]', '-', filename)

        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()

        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        # Avoid reserved names (for Windows)
        base, ext = os.path.splitext(sanitized)
        if base.upper() in reserved_names:
            sanitized = f"{base}_file{ext}"

        return sanitized
