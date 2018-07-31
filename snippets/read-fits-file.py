import sys
from astropy.io import fits

fits_file = fits.open(sys.argv[1])
print(fits_file.info())
sci_hdu = fits_file[1]
data = sci_hdu.data
print("dtype: ", data.dtype)
print("shape: ", data.shape)
