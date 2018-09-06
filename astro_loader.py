import os.path
import numpy
import numpy.random
import boto3
import threading
import random

from astropy.io import fits
from astropy.visualization import ZScaleInterval, LogStretch, AsinhStretch


class ZMaxInterval(ZScaleInterval):
    def __init__(self, *args, **kwargs):
        super(ZMaxInterval, self).__init__(*args, **kwargs)

    def get_limits(self, values):
        zscale_min, zscale_max = super(ZMaxInterval, self).get_limits(values)
        return (zscale_min, values.max())


class AstroLoader:
    def __init__(self, preload=32, limit=65536):
        self.limit = limit
        self.tiles_per_raw_image = 16
        self.nfiles_considered = self.limit // self.tiles_per_raw_image
        self.preload = preload
        self.s3 = boto3.client('s3')
        self.zmax = ZMaxInterval()
        self.zscale = ZScaleInterval()
        self.logstretch = LogStretch()
        self.asinhstretch = AsinhStretch()

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
        print("Randomising and keeping {0} of them".format(self.nfiles_considered))
        random.shuffle(filenames)
        filenames = filenames[0:self.nfiles_considered]

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

            buffer_max = self.tiles_per_raw_image * self.preload
            buffer_free = buffer_max - len(self.tile_buffer)
            if buffer_free < self.tiles_per_raw_image:
                print("Feeder: buffer full, waiting (buffer_free = {0}, buffer_max = {1})".format(buffer_free, buffer_max))
                self.buffer_condition.wait()
                if self.done:
                    return
                else:
                    continue

            print("Feeder: fetching")

            new_tiles = self.cut_into_tiles(
                self.image(
                    self.load_from_s3(
                        self.select_random()
                    )
                )
            )

            for t in range(len(new_tiles)):
                new_tiles[t] = self.transform(self.stretch(new_tiles[t]))

            print("Feeder: here's {0} new tiles".format(len(new_tiles)))
            self.tile_buffer.extend(new_tiles)
            random.shuffle(self.tile_buffer)

            self.buffer_condition.notify()
            self.buffer_condition.release()

    def select_random(self):
        file_num = numpy.random.randint(0, len(self.files))
        return self.files[file_num]

    def load_from_s3(self, key):
        print("Downloading {0}".format(key))
        self.s3.download_file(
            Bucket='stpubdata',
            Key=key,
            Filename='tmp.fits',
            ExtraArgs={'RequestPayer': 'requester'},
        )
        return fits.open('tmp.fits')

    def image(self, fits):
        # Just use the first one
        for plane in fits:
            if plane.name == 'SCI':
                return plane.data

    def cut_into_tiles(self, image):
        divisions = numpy.sqrt(self.tiles_per_raw_image).astype(numpy.int)
        # Round down
        tile_height, tile_width = numpy.floor(image.shape / divisions).astype(numpy.int)
        crop_height = tile_height * divisions
        crop_width = tile_width * divisions
        image = image[0:crop_height, 0:crop_width]
        image_height, image_width = image.shape

        tiles = []

        for tilenum in range(self.tiles_per_raw_image):
            left = (tile_width * tilenum) % image_width
            right = ((tile_width * (tilenum + 1)) - 1) % image_width
            top = (tile_height * tilenum) % image_height
            bottom = ((tile_height * (tilenum + 1)) - 1) % image_height

            tiles.append(image[top:bottom, left:right])

        return tiles

    def stretch(self, image):
        return self.logstretch(self.zmax(image))

    # Re-scale the pixel values to the -1.0 to 1.0 range required by the DCGAN.
    # At this point it's already sitting between 0.0 and 1.0 as this is what the astropy
    # stretch and scale functions give back.
    def transform(self, image):
        return (image * 2) - 1

    def get_tiles(self, batch_size=32):
        batch = []
        self.buffer_condition.acquire()
        if len(self.tile_buffer) < (self.tiles_per_raw_image * (self.preload - 1)):
            print("Waiting for new images to come in")
            self.buffer_condition.wait()

        for i in range(batch_size):
            batch.append(self.tile_buffer.pop())

        self.buffer_condition.notify()
        self.buffer_condition.release()

        return numpy.array(batch, dtype=numpy.float32)
