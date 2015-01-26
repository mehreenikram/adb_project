__author__ = 'Maira'


class Table:
    def __init__(self, name):
        self.name = name
        #Table attributes will be a list of attribute objects
        self.attributes = []
        #Table fds will be a list of fd objects
        self.fds = []

    def set_attributes(self, attributes):
        self.attributes = attributes

    def set_fds(self, fds):
        self.fds = fds

    def add_fd(self, fd):
        self.fds.append(fd)

    # tbd - implement a function which removes the fd
    # def remove_fd(self, fd):
    #     self.fds.remove(fd)

    @property
    def get_name(self):
        return self.name

    @property
    def get_attributes(self):
        return self.attributes

    @property
    def get_fds(self):
        return self.fds

    def get_fd_by_id(self, fd_id):
        k = 0
        for fd in self.fds:
            if fd_id == k:
                return fd
            k += 1
        return None

    def get_attribute_by_name(self, name):
        for attr in self.attributes:
            if attr.get_name == name:
                return attr