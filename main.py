# First crack at coding up a DCGAN based on Taehoon Kim's code
# at https://github.com/carpedm20/DCGAN-tensorflow

import os
import numpy
import pprint

from model import DCGAN
from s3_export import export_images_to_s3

import tensorflow as tf

flags = tf.app.flags

# Leaving these as-is as I don't yet fully understand what they do
flags.DEFINE_integer("epochs", 25, "Number of epochs to train [25]")
flags.DEFINE_float("learning_rate", 0.0002,
                   "Learning rate of for adam [0.0002]")
flags.DEFINE_float("beta1", 0.5, "Momentum term of adam [0.5]")
flags.DEFINE_float("train_size", numpy.inf,
                   "The size of train images [numpy.inf]")
flags.DEFINE_integer("batch_size", 64, "The size of batch images [64]")

# The original images are 4096x2048.
# For speed during development we're resizing down to 512x256.
# There will be a way to make this adjustable at some point.
flags.DEFINE_integer("height", 256, "Image height")
flags.DEFINE_integer("width", 512, "Image width")

flags.DEFINE_string("checkpoint_dir", "checkpoint",
                    "Directory name to save the checkpoints [checkpoint]")
flags.DEFINE_string("logs_dir", "logs",
                    "Directory name to save the logs [logs]")

# These look fine
flags.DEFINE_boolean(
    "train", False, "True for training, False for testing [False]")
flags.DEFINE_boolean("visualize", False,
                     "True for visualizing, False for nothing [False]")
flags.DEFINE_integer("generate_test_images", 100,
                     "Number of images to generate during test. [100]")

FLAGS = flags.FLAGS

pp = pprint.PrettyPrinter()


def tf_main(_):
    # Hoping there's a nicer way of factoring this as 'flags.FLAGS.__flags' is bloody horrible
    pp.pprint(flags.FLAGS.__flags)

    if not os.path.exists(FLAGS.checkpoint_dir):
        os.makedirs(FLAGS.checkpoint_dir)

    if not os.path.exists(FLAGS.logs_dir):
        os.makedirs(FLAGS.logs_dir)

    run_config = tf.ConfigProto()
    run_config.gpu_options.allow_growth = True  # no clue

    with tf.Session(config=run_config) as sess:
        dcgan = DCGAN(
            sess,
            width=FLAGS.width,
            height=FLAGS.height,
            checkpoint_dir=FLAGS.checkpoint_dir,
            logs_dir=FLAGS.logs_dir,
            batch_size=FLAGS.batch_size,
            sample_num=FLAGS.batch_size,
        )

        # this is the show_all_variables() function in upstream (model.py)
        model_vars = tf.trainable_variables()
        tf.contrib.slim.model_analyzer.analyze_vars(
            model_vars, print_info=True)

        if FLAGS.train:
            dcgan.train(FLAGS)
        else:
            if not dcgan.load(FLAGS.checkpoint_dir)[0]:
                raise Exception("Model needs training first")

        z_sample = numpy.random.uniform(-0.5, 0.5, size=(FLAGS.batch_size, dcgan.z_dim))
        samples = sess.run(
            dcgan.sampler,
            feed_dict={dcgan.z: z_sample}
        )
        export_images_to_s3(
            samples,
            label=dcgan.session_timestamp,
            setnum=0,
        )


if __name__ == '__main__':
    if not tf.test.is_built_with_cuda():
        print('CUDA not enabled')
        os.exit(1)

    print('CUDA enabled', tf.test.gpu_device_name())

    tf.app.run(
        main=tf_main
    )
