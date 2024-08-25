


class FileStorage:
    def __init__(self, path):
        self.path = path

    def store(self, *data):
        with open(self.path, 'w') as f:
            for d in data:
                f.write(str(d) + '\n')