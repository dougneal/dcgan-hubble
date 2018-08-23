import os.path
import numpy
import numpy.random
import boto3
#import IPython
import threading
import random

from astropy.io import fits
from astropy.visualization import ZScaleInterval


class ZMaxInterval(ZScaleInterval):
    def __init__(self, *args, **kwargs):
        super(ZMaxInterval, self).__init__(*args, **kwargs)

    def get_limits(self, values):
        zscale_min, zscale_max = super(ZMaxInterval, self).get_limits(values)
        return (zscale_min, values.max())


class AstroLoader:
    def __init__(self):
        self.tiles_per_raw_image = 16
        self.preload = 4
        self.s3 = boto3.client('s3')
        self.zmax = ZMaxInterval()

        filenames = []
        with open(os.path.join(os.path.dirname(__file__), 'astroquery-index.csv'), 'r') as index:
            while True:
                line = index.readline()
                if line == "":
                    break

                line = line.rstrip('\n')
                cols = line.split(',')
                s3uri = cols[1]
                s3key = s3uri.replace('s3://stpubdata/', '')
                filenames.append(s3key)

        print("{0} file URLs loaded".format(len(filenames)))
        self.files = numpy.array(filenames)

        self.tile_buffer = []
        self.buffer_condition = threading.Condition()
        self.feeder = threading.Thread(target=self.feed_loop)

        self.done = False
        self.feeder.start()

    def finish(self):
        self.done = True

    def feed_loop(self):
        while not self.done:
            self.buffer_condition.acquire()

            buffer_space = (self.tiles_per_raw_image * self.preload) - len(self.tile_buffer)
            if buffer_space == 0:
                print("Feeder: buffer full, waiting")
                self.buffer_condition.wait()
                print("Feeder: continuing")

            images = self.images(self.load_from_s3(self.select_random()))
            new_tiles = []
            for i in images:
                new_tiles.extend(self.cut_into_tiles(i))

            for t in range(len(new_tiles)):
                new_tiles[t] = self.stretch(new_tiles[t])

            print("Feeder: here's {0} new tiles".format(len(new_tiles)))
            self.tile_buffer.extend(new_tiles)
            random.shuffle(self.tile_buffer)

            self.buffer_condition.notify()
            self.buffer_condition.release()

    def select_random(self):
        return self.files[numpy.random.randint(0, len(self.files))]

    def load_from_s3(self, key):
        print("Downloading {0}".format(key))
        self.s3.download_file(
            Bucket='stpubdata',
            Key=key,
            Filename='tmp.fits',
            ExtraArgs={'RequestPayer': 'requester'},
        )
        return fits.open('tmp.fits')

    def images(self, fits):
        return tuple([plane.data for plane in fits if plane.name == 'SCI'])

    def cut_into_tiles(self, image):
        image_height, image_width = image.shape
        tile_height, tile_width = image.shape / numpy.log2(self.tiles_per_raw_image)
        tiles = []

        for tilenum in range(self.tiles_per_raw_image):
            left = int((tile_width * tilenum) % image_width)
            right = int(((tile_width * (tilenum + 1)) - 1) % image_width)
            top = int((tile_height * tilenum) % image_height)
            bottom = int(((tile_height * (tilenum + 1)) - 1) % image_height)

            tiles.append(image[top:bottom, left:right])

        return tiles

    def stretch(self, image):
        return self.zmax(image)

    def get_tiles(self, batch_size=32):
        if batch_size % self.tiles_per_raw_image != 0:
            raise Exception("Batch size must be a multiple of {0}".format(
                self.tiles_per_raw_image
            ))

        batch = []
        self.buffer_condition.acquire()
        if len(self.tile_buffer) < self.tiles_per_raw_image * self.preload:
            print("Waiting for new images to come in")
            self.buffer_condition.wait()

        for i in range(batch_size):
            batch.append(self.tile_buffer.pop())

        self.buffer_condition.notify()
        self.buffer_condition.release()

        return batch
