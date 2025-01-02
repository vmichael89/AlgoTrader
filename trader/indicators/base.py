from abc import ABC, abstractmethod


class Indicator(ABC):

    @abstractmethod
    def process_data_point(self, index, row):
        pass
