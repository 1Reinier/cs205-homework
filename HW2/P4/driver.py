import sys
import os.path
sys.path.append(os.path.join('..', 'util'))

import set_compiler
set_compiler.install()

import pyximport
pyximport.install()

import numpy as np
import pylab

import filtering
from timer import Timer
from threading import Thread


def py_median_3x3(image, iterations=10, num_threads=1):
    """ repeatedly filter with a 3x3 median """
    tmpA = image.copy()
    tmpB = np.empty_like(tmpA)

    for i in range(iterations):
        for j in range(0, image.shape[0], num_threads):
            threads = []
            out = [0]*num_threads
            for n in range(num_threads):
                threads += [Thread(name='{}'.format(n), target=filtering.median_3x3,
                                   args=(tmpA[j+n-1: j-1, j+n+2: j+2], tmpB[j+n-1: j-1, j+n+2: j+2], 0, 1))]
            map(lambda t: t.start(), threads)
            map(lambda t: t.join(), threads)
            for n in range(num_threads):
                tmpB[j] = out[n]


        # swap direction of filtering
        tmpA, tmpB = tmpB, tmpA

    return tmpA


def numpy_median(image, iterations=10):
    """ filter using numpy """
    for i in range(iterations):
        padded = np.pad(image, 1, mode='edge')
        stacked = np.dstack((padded[:-2,  :-2], padded[:-2,  1:-1], padded[:-2,  2:],
                             padded[1:-1, :-2], padded[1:-1, 1:-1], padded[1:-1, 2:],
                             padded[2:,   :-2], padded[2:,   1:-1], padded[2:,   2:]))
        image = np.median(stacked, axis=2)

    return image


if __name__ == '__main__':
    input_image = np.load('image.npz')['image'].astype(np.float32)

    pylab.gray()

    pylab.imshow(input_image)
    pylab.title('original image')

    pylab.figure()
    pylab.imshow(input_image[1200:1800, 3000:3500])
    pylab.title('before - zoom')

    # verify correctness
    from_cython = py_median_3x3(input_image, 2, 5)
    #from_numpy = numpy_median(input_image, 2)
    #assert np.all(from_cython == from_numpy)

    with Timer() as t:
        new_image = py_median_3x3(input_image, 10, 8)

    pylab.figure()
    pylab.imshow(new_image[1200:1800, 3000:3500])
    pylab.title('after - zoom')

    print("{} seconds for 10 filter passes.".format(t.interval))
    pylab.show()
