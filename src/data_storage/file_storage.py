import os 
import typing
from .base import BaseStorage

class FileStorage(BaseStorage):
    """File storage class to store data in a file"""

    def __init__(self, path : str, filename : str, separator : str = '\t', columns : typing.List[str] = []):
        self.path = path
        self.filename = filename
        self.separator = separator
        if not os.path.exists(self.path):
            os.makedirs(self.path)     
        if not os.path.isfile(fr'{self.path}\{self.filename}'):
            with open(fr'{self.path}\{self.filename}', 'w') as file:
                headerline = self.separator.join(columns)
                file.write(headerline + '\n')

    def store(self, *data):
        dataline = self.separator.join(['{}'.format(val) for val in data])
        with open(fr'{self.path}\{self.filename}', 'a') as file:
            file.write(dataline + '\n')

    def store_in_new(self, filename : str, relative_path : str = '', 
                        file_writer_hook : typing.Callable[[typing.Any], typing.Any] = None,  
                        data : typing.Any = None):
        if not os.path.exists(fr'{self.path}\{relative_path}'):
            os.makedirs(fr'{self.path}\{relative_path}')
        fullpath = fr'{self.path}\{relative_path}\{filename}'
        if file_writer_hook:
            file_writer_hook(fullpath, data)
        else:
            with open(fullpath, 'w') as file:
                file.write('{}'.format(data))