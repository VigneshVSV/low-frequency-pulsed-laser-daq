


class BaseStorage:
    
    def store(self, *data):
        raise NotImplementedError("Implement store method in subclass")
        
    def prepare(self):
        pass