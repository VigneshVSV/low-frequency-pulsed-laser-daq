import os 
import typing
from .base import StorageBase

class FileStorage(StorageBase):
    """File storage class to store data in a file"""

    def __init__(self, path : str, filename : str, separator : str = r'\t', columns : typing.List[str] = []):
        self.path = path
        if not os.path.exists(self.path):
            os.makedirs(self.path)     
        with open(f'{self.path}\{self.filename}', 'w') as f:
            headerline = '\t'.join(columns)
            f.write(headerline + '\n')
        self.filename = filename
        self.separator = separator

    def store(self, *data):
        dataline = self.separator.join(['{}'.format(val) for val in data])
        with open(f'{self.path}\{self.filename}', 'w') as f:
            f.write(dataline + '\n')

    def store_in_new_file(self, filename : str, relative_path : str = '', 
                        file_writer_hook : typing.Callable[[typing.Any], typing.Any] = None,  
                        data : typing.Any = None):
        with open(f'{self.path}\{relative_path + '\\' if relative_path else ''}\{filename}', 'w') as f:
            if file_writer_hook:
                file_writer_hook(f, data)
            else:
                f.write('{}'.format(data))