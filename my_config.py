import os


class MyConfig:
    def __init__(self):
        self.graphic_terminal = True
        self.verbose_log = False
        self.my_configuration = "iotjournal"
        self.result_folder = "results"
        self.data_folder = "dataGA"

        # try:
        #     os.stat(self.result_folder)
        # except:
        #     os.mkdir(self.result_folder)
