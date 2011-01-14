"""Reading an STC file

STC files contain activations on cortex ie. source
reconstructions
"""
print __doc__

import fiff

fname = 'MNE-sample-data/MEG/sample/sample_audvis-ave-7-meg-lh.stc'

stc = fiff.read_stc(fname)

n_vertices, n_samples = stc['data'].shape
print "tmin : %s (s)" % stc['tmin']
print "tstep : %s" % stc['tstep']
print "tmax : %s (s)" % (stc['tmin'] + stc['tstep'] * n_samples)
print "stc data size: %s (nb of vertices) x %s (nb of samples)" % (
                                                    n_vertices, n_samples)