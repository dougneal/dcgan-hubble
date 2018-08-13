import astropy.io.fits
import astropy.nddata.utils


# A really rough first pass at this function that makes an assumption
# that the files are all (2048,4096) and that we want to resize down
# to (256,512).
def get_scaled_fits_image(filename):
    fullsize = astropy.io.fits.getdata(filename)
    if fullsize.shape != (2048, 4096):
        raise(Exception("{0} isn't the expected shape, it's {1}".format(filename, fullsize.shape)))

    reduced = astropy.nddata.utils.block_reduce(fullsize, 8)
    return reduced
