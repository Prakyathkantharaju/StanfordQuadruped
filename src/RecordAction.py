import numpy as np 

from datetime import datetime
import time
import os




# Class to record the Data

class DataRecorder:
    def __init__(self, filelocation: str = "/record") -> None:
        filelocation = os.getcwd() + filelocation
        now = datetime.now()
        filepath = now.strftime("%d%m%Y-%H:%M:%S")
        self.filepath = filelocation + '/' + filepath + '.txt'
        self.data = np.array([])
        self.time = time.time()
        f = open(self.filepath, 'w')
        f.write("action")
        f.close()

    def add_data(self, data: np.array):
        data_time = np.append(data.flatten(), time.time() - self.time)
        if len(self.data) < 1:
            # add the time
            self.data = data_time
            self.data = self.data.reshape(-1, 1)
        else:
            print(self.data.shape, data_time.reshape(-1,1))
            self.data = np.append(self.data, data_time.reshape(-1, 1), axis=1)
            np.savetxt(self.filepath, self.data, delimiter=',')
