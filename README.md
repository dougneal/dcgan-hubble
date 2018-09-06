# Running Hubble images through a DCGAN

Acquiring images from the Hubble Space Telescope through the Space Telescope Science Institute's
[MAST API](https://mast.stsci.edu/api/v0/) and feeding them to a Deep Convolutional Generative
Adversarial Network.

## Requirements

 * Tensorflow
 * A GPU
 * An AWS account

## Usage

### Training

```
$ python main.py --width 517 --height 257 --epochs 250 --train
$ python main.py --width 1036 --height 515 --epochs 250 --train
```

## Authors and copyright

 * [Julie Hill](https://github.com/juliefhill)
 * [Doug Neal](https://github.com/dougneal)

## Credits

Code liberally borrowed from [Taehoon Kim](https://github.com/carpedm20)'s
[DCGAN-tensorflow](https://github.com/carpedm20/DCGAN-tensorflow/) project.

 * [Space Telescope Science Institute](https://www.stsci.edu/)
 * [HST Public Data in AWS](https://registry.opendata.aws/hst/)

See LICENSE

