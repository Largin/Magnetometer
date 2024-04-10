#!/usr/bin/python
class Options:
    def __init__(self):
        self.headers = True
        self.input_delimiter = ';'
        self.input_directory = '.\\data\\'
        self.output_name = '.\\output\\output'
        self.averages = {
            'head_len': 650,  # baseline correction - number of points used to calculate baseline
            'tail_len': 10,
            'drop': False,
            'tail_head_diff': 0.01
        }
        self.filter = {
            'chunk_min': 0,
            'chunk_max': 300,
            'drop': False
        }
        self.functions = [
            {
                'label': 'Standard deviation',
                'callback': fun_std,
                'filter': 0.018,
                'drop': False,
                'drop_corrected': False
            },
            {
                'label': 'Arithmetic mean',
                'callback': fun_mean,
                'filter_min': -1,
                'filter_max': 0,
                'drop': False,  # applies filter to values which are not "corrected"
                                # shifted by the initial offset determined by head_len
                'drop_corrected': True  # filter is applied to the corrected values
            }
        ]

        self.plot_title = 'noise P=-200m #1 aver:1300pts'


def fun_std(in_array):
    import numpy
    res = numpy.std(in_array)
    return res


def fun_mean(in_array):
    import numpy
    res = numpy.mean(in_array)
    return res


class Chunk:
    def __init__(self):
        self.number = None
        self.base_timestamp = None
        self.timestamps = []
        self.values = []
        self.corrected_values = []

        self.dropped = False
        self.malformed = False
        self.head_average = None
        self.tail_average = None

        self.functions = []
        self.functions_corrected = []

    def add_row(self, number: int, value: float, timestamp: float) -> bool:
        if self.number is not None and self.number != number:
            self.compute_averages()
            return False
        self.number = number
        if self.base_timestamp is None:
            self.base_timestamp = timestamp
        self.timestamps.append(timestamp - self.base_timestamp)
        self.values.append(value)
        return True

    def compute_averages(self):
        import math
        self.head_average = sum(self.values[:options.averages['head_len']]) / options.averages['head_len']
        self.tail_average = sum(self.values[-options.averages['tail_len']:]) / options.averages['tail_len']
        if options.averages['drop'] \
                and math.fabs(self.head_average - self.tail_average) > options.averages['tail_head_diff']:
            print(f'Chunk {self.number} marked dropped because of diff in average of head and average of tail')
            self.dropped = True

    def compute(self):
        import math
        # Baseline correction: Computing corrected values - reduce values by head average
        if self.head_average is None:
            self.compute_averages()
        self.corrected_values = [round(val - self.head_average, 5) for val in self.values]

        for fun in options.functions:
            fun_val = fun['callback'](self.values)
            if fun['drop']:
                if 'filter' in fun and math.fabs(fun_val) > fun['filter'] and not self.dropped:
                    print(f'Chunk no {self.number} marked dropped because of filter {fun['label']}.')
                    self.dropped = True
                if 'filter_min' in fun and fun_val < fun['filter_min'] and not self.dropped:
                    print(f'Chunk no {self.number} marked dropped because of filter {fun['label']}.')
                    self.dropped = True
                if 'filter_max' in fun and fun_val > fun['filter_max'] and not self.dropped:
                    print(f'Chunk no {self.number} marked dropped because of filter {fun['label']}.')
                    self.dropped = True
            self.functions.append(fun_val)

            fun_val = fun['callback'](self.corrected_values)
            if fun['drop_corrected']:
                if 'filter' in fun and math.fabs(fun_val) > fun['filter'] and not self.dropped:
                    print(f'Chunk no {self.number} marked dropped because of filter {fun['label']}.')
                    self.dropped = True
                if 'filter_min' in fun and fun_val < fun['filter_min'] and not self.dropped:
                    print(f'Chunk no {self.number} marked dropped because of filter {fun['label']}.')
                    self.dropped = True
                if 'filter_max' in fun and fun_val > fun['filter_max'] and not self.dropped:
                    print(f'Chunk no {self.number} marked dropped because of filter {fun['label']}.')
                    self.dropped = True
            self.functions_corrected.append((fun['callback'](self.corrected_values)))

    def to_array(self):
        return self.values

    def to_array_corrected(self):
        return self.corrected_values


class Data:
    def __init__(self):
        self.chunks = []
        self.chunks_length = None
        self.timestamps_averages = []
        self.timestamps_averages_corrected = []
        self.timestamps_averages_corrected_all = []

    def add_chunk(self, chunk):
        chunk_len = len(chunk.values)
        if self.chunks_length is not None \
                and self.chunks_length != chunk_len \
                and not chunk.dropped:
            print(f'Chunk no {chunk.number} marked dropped because of difference in chunk length. Is {chunk_len}, ' 
                  f'should be {self.chunks_length}.')
            chunk.dropped = True
            chunk.malformed = True

        if False and self.chunks_length is not None \
                and self.chunks[0].timestamps != chunk.timestamps \
                and not chunk.dropped:
            print(f'Chunk no {chunk.number} marked dropped because of difference in timestamps.')
            chunk.dropped = True

        if not chunk.dropped \
                and (chunk.number < options.filter['chunk_min'] or chunk.number > options.filter['chunk_max']) \
                and options.filter['drop']:
            print(f'Chunk no {chunk.number} marked dropped because of difference filter.')
            chunk.dropped = True

        if self.chunks_length is None:
            self.chunks_length = chunk_len

        print(f'Saving chunk no: {chunk.number}')
        self.chunks.append(chunk)
        
    def compute_chunks(self):
        for chunk in self.chunks:
            chunk.compute()

        temp_chunks = [chunk.to_array() for chunk in self.chunks if not chunk.dropped]
        self.timestamps_averages = [round(float(sum(col)) / len(col), 5) for col in zip(*temp_chunks)]
        temp_chunks = [chunk.to_array_corrected() for chunk in self.chunks if not chunk.dropped]
        self.timestamps_averages_corrected = [round(float(sum(col)) / len(col), 5) for col in zip(*temp_chunks)]
        temp_chunks = [chunk.to_array_corrected() for chunk in self.chunks if not chunk.malformed]
        self.timestamps_averages_corrected_all = [round(float(sum(col)) / len(col), 5) for col in zip(*temp_chunks)]
       
    def save_to_file(self, filename):
        import csv
        import numpy

        with open(filename + '.csv', "w", newline='') as csv_file:
            result_1 = [['timestamps\\chunk'] + self.chunks[0].timestamps + [fun['label'] for fun in options.functions]] \
                       + [[row.number] + row.values + row.functions for row in self.chunks if not row.dropped] \
                       + [['average'] + self.timestamps_averages + ['' for fun in options.functions]]
            result = numpy.transpose(result_1)
            print(f'chunks saved: {numpy.size(result,1)-2}')
            writer = csv.writer(csv_file, delimiter = ',')
            writer.writerows(result)

        with open(filename + '_corrected.csv', "w", newline='') as csv_file:
            result_1 = [['timestamps\\chunk'] + self.chunks[0].timestamps + [fun['label'] for fun in options.functions]] \
                       + [[row.number] + row.corrected_values + row.functions_corrected for row in self.chunks if not row.dropped] \
                       + [['average'] + self.timestamps_averages_corrected + ['' for fun in options.functions]]
            result = numpy.transpose(result_1)

            writer = csv.writer(csv_file, delimiter = ',')
            writer.writerows(result)
            
    def plot_all(self, filename):
        from matplotlib.ticker import AutoMinorLocator
        import matplotlib.pyplot as plt

        fig1, ax1 = plt.subplots(figsize=(10, 6))
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        for chunk in self.chunks:
            if not chunk.dropped:
                ax1.plot(chunk.timestamps, chunk.values, linewidth='0.8')
                ax2.plot(chunk.timestamps, chunk.corrected_values, linewidth='0.8')
        ax1.plot(self.chunks[0].timestamps, self.timestamps_averages, 'r', label='averages')
        ax2.plot(self.chunks[0].timestamps, self.timestamps_averages_corrected, 'r', label='averages')
        ax1.set_ylabel('values')
        ax2.set_ylabel('values')
        ax1.set_xlabel('timestamps')
        ax2.set_xlabel('timestamps')
        ax1.legend(loc='best')
        ax2.legend(loc='best')
        ax1.xaxis.set_minor_locator(AutoMinorLocator())
        ax2.xaxis.set_minor_locator(AutoMinorLocator())
        ax1.yaxis.set_minor_locator(AutoMinorLocator())
        ax2.yaxis.set_minor_locator(AutoMinorLocator())
        ax1.grid(True, which='major')
        ax2.grid(True, which='major')
        ax1.grid(True, which='minor', linestyle=':')
        ax2.grid(True, which='minor', linestyle=':')
        plt.title(options.plot_title)
        fig1.savefig(filename + '_all.png')
        fig2.savefig(filename + '_all_corrected.png')

    def plot_averages(self, filename):
        from matplotlib.ticker import AutoMinorLocator
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.chunks[0].timestamps, self.timestamps_averages_corrected, 'r', label='average')
        ax.plot(self.chunks[0].timestamps, self.timestamps_averages_corrected_all, 'b', label='average all')
        ax.set_ylabel('values')
        ax.set_xlabel('timestamps')
        ax.legend(loc='best')
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.grid(True, which='major')
        ax.grid(True, which='minor', linestyle=':')
        plt.title(options.plot_title)
        fig.savefig(filename + '_average.png')

    def plot_functions(self, filename):
        from matplotlib.ticker import AutoMinorLocator
        import matplotlib.pyplot as plt

        temp_chunks_no = [chunk.number for chunk in self.chunks if not chunk.dropped]
        functions = [[chunk.functions_corrected[idx] for chunk in self.chunks if not chunk.dropped]
                     for idx, function in enumerate(options.functions)]

        fig, ax = plt.subplots(figsize=(10, 6))
        for idx, function in enumerate(options.functions):
            ax.plot(temp_chunks_no, functions[idx], label=options.functions[idx]['label'])
        ax.set_ylabel('values')
        ax.set_xlabel('chunks')
        ax.legend(loc='best')
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.grid(True, which='major')
        ax.grid(True, which='minor', linestyle=':')
        plt.title(options.plot_title)
        fig.savefig(filename + '_functions_corrected.png')

    def plot_functions_nc(self, filename):
        from matplotlib.ticker import AutoMinorLocator
        import matplotlib.pyplot as plt

        temp_chunks_no = [chunk.number for chunk in self.chunks if not chunk.dropped]
        functions_nc = [[chunk.functions[idx] for chunk in self.chunks if not chunk.dropped]
                        for idx, function in enumerate(options.functions)]

        fig, ax = plt.subplots(figsize=(10, 6))
        for idx, function in enumerate(options.functions):
            ax.plot(temp_chunks_no, functions_nc[idx], label=options.functions[idx]['label'])
        ax.set_ylabel('values')
        ax.set_xlabel('chunks')
        ax.legend(loc='best')
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.grid(True, which='major')
        ax.grid(True, which='minor', linestyle=':')
        plt.title(options.plot_title + ' not corrected !!')
        fig.savefig(filename + '_functions.png')

        
def read_files():
    import csv
    import glob

    file_list = sorted(glob.glob(options.input_directory + '*.csv'))
    print(f'Files to read: {file_list}')

    chunk = Chunk()
    data = Data()

    for file in file_list:
        print(f'Opening file: {file}')
        f = open(file, newline='')
        reader = csv.reader(f, delimiter=options.input_delimiter)
        if options.headers:
            next(reader)

        for row in reader:
            chunk_no = int(row[0])
            timestamp = float(row[1])
            value = float(row[2])

            if not chunk.add_row(chunk_no, value, timestamp):
                data.add_chunk(chunk)
                chunk = Chunk()
                chunk.add_row(chunk_no, value, timestamp)

    data.add_chunk(chunk)
    return data


def main():
    import sys

    try:
        data = read_files()
        data.compute_chunks()
        data.save_to_file(options.output_name)
        data.plot_all(options.output_name)
        data.plot_averages(options.output_name)
        data.plot_functions(options.output_name)
        data.plot_functions_nc(options.output_name)
    except (IOError, OSError) as e:
        print(e)
        sys.exit(e.errno)
    except Exception as e:
        print(e)
        sys.exit(-1)


if __name__ == "__main__":
    options = Options()
    main()
