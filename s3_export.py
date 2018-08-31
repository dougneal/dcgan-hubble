import boto3
import io
import imageio
import numpy

s3 = boto3.resource('s3')
bucket = s3.Bucket('jh-dn-dcgan-hubble')


def export_images_to_s3(images, label, training=False, epoch=None, setnum=None):
    # Remove extra dimensions: (height, width, 1) -> (height, width)
    images = numpy.squeeze(images)

    # Map the -1.0 to 1.0 range back up to the 0-255 range
    images = (images + 1.0) * 127.5
    images = images.astype(numpy.uint8)

    for i in range(len(images)):
        bytesio = io.BytesIO()
        imageio.imwrite(
            uri=bytesio,
            im=images[i],
            format='png',
        )
        bytesio.seek(0)

        if training:
            s3key = "training/{0}/epoch_{1:04d}/{2:04d}.png".format(
                label, epoch, i
            )
        else:
            s3key = "samples/{0}/set_{1:04d}/{2:04d}.png".format(
                label, setnum, i
            )

        s3obj = bucket.Object(s3key)
        s3obj.upload_fileobj(bytesio)
