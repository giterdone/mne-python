import os.path as op
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_equal
from nose.tools import assert_true

from ...datasets import sample
from ...label import read_label, label_sign_flip
from ...event import read_events
from ...epochs import Epochs
from ...source_estimate import SourceEstimate
from ... import fiff, Covariance, read_forward_solution
from ..inverse import apply_inverse, read_inverse_operator, \
                      apply_inverse_raw, apply_inverse_epochs, \
                      make_inverse_operator

examples_folder = op.join(op.dirname(__file__), '..', '..', '..', 'examples')
data_path = sample.data_path(examples_folder)
fname_inv = op.join(data_path, 'MEG', 'sample',
                            # 'sample_audvis-meg-eeg-oct-6-meg-eeg-inv.fif')
                            'sample_audvis-meg-oct-6-meg-inv.fif')
fname_vol_inv = op.join(data_path, 'MEG', 'sample',
                            'sample_audvis-meg-vol-7-meg-inv.fif')
fname_data = op.join(data_path, 'MEG', 'sample',
                            'sample_audvis-ave.fif')
fname_cov = op.join(data_path, 'MEG', 'sample',
                            'sample_audvis-cov.fif')
fname_fwd = op.join(data_path, 'MEG', 'sample',
                            'sample_audvis-meg-oct-6-fwd.fif')
                            # 'sample_audvis-meg-eeg-oct-6-fwd.fif')
fname_raw = op.join(data_path, 'MEG', 'sample',
                            'sample_audvis_filt-0-40_raw.fif')
fname_event = op.join(data_path, 'MEG', 'sample',
                            'sample_audvis_filt-0-40_raw-eve.fif')
label = 'Aud-lh'
fname_label = op.join(data_path, 'MEG', 'sample', 'labels', '%s.label' % label)

inverse_operator = read_inverse_operator(fname_inv)
label = read_label(fname_label)
raw = fiff.Raw(fname_raw)
snr = 3.0
lambda2 = 1.0 / snr ** 2
dSPM = True


def test_inverse_operator():
    """Test MNE inverse computation

    With and without precomputed inverse operator.
    """
    evoked = fiff.Evoked(fname_data, setno=0, baseline=(None, 0))

    stc = apply_inverse(evoked, inverse_operator, lambda2, dSPM=False)

    assert_true(stc.data.min() > 0)
    assert_true(stc.data.max() < 10e-10)
    assert_true(stc.data.mean() > 1e-11)

    stc = apply_inverse(evoked, inverse_operator, lambda2, dSPM=True)

    assert_true(np.all(stc.data > 0))
    assert_true(np.all(stc.data < 35))

    assert_true(stc.data.min() > 0)
    assert_true(stc.data.max() < 35)
    assert_true(stc.data.mean() > 0.1)

    # Test MNE inverse computation starting from forward operator
    noise_cov = Covariance(fname_cov)
    evoked = fiff.Evoked(fname_data, setno=0, baseline=(None, 0))
    fwd_op = read_forward_solution(fname_fwd, surf_ori=True)
    my_inv_op = make_inverse_operator(evoked.info, fwd_op, noise_cov,
                                      loose=0.2, depth=0.8)

    my_stc = apply_inverse(evoked, my_inv_op, lambda2, dSPM)

    assert_equal(stc.times, my_stc.times)
    assert_array_almost_equal(stc.data, my_stc.data, 2)


def test_inverse_operator_volume():
    """Test MNE inverse computation on volume source space"""
    evoked = fiff.Evoked(fname_data, setno=0, baseline=(None, 0))
    inverse_operator = read_inverse_operator(fname_vol_inv)
    stc = apply_inverse(evoked, inverse_operator, lambda2, dSPM)
    stc.save('tmp-vl.stc')
    stc2 = SourceEstimate('tmp-vl.stc')
    assert_true(np.all(stc.data > 0))
    assert_true(np.all(stc.data < 35))
    assert_array_almost_equal(stc.data, stc2.data)
    assert_array_almost_equal(stc.times, stc2.times)


def test_apply_mne_inverse_raw():
    """Test MNE with precomputed inverse operator on Raw"""
    start = 3
    stop = 10
    _, times = raw[0, start:stop]
    stc = apply_inverse_raw(raw, inverse_operator, lambda2, dSPM=True,
                            label=label, start=start, stop=stop, nave=1,
                            pick_normal=False)
    assert_true(np.all(stc.data > 0))
    assert_array_almost_equal(stc.times, times)


def test_apply_mne_inverse_epochs():
    """Test MNE with precomputed inverse operator on Epochs
    """
    event_id, tmin, tmax = 1, -0.2, 0.5

    picks = fiff.pick_types(raw.info, meg=True, eeg=False, stim=True,
                            ecg=True, eog=True, include=['STI 014'])
    reject = dict(grad=4000e-13, mag=4e-12, eog=150e-6)
    flat = dict(grad=1e-15, mag=1e-15)

    events = read_events(fname_event)[:15]
    epochs = Epochs(raw, events, event_id, tmin, tmax, picks=picks,
                    baseline=(None, 0), reject=reject, flat=flat)
    stcs = apply_inverse_epochs(epochs, inverse_operator, lambda2, dSPM,
                                label=label, pick_normal=True)

    assert_true(len(stcs) == 4)
    assert_true(3 < stcs[0].data.max() < 10)


    data = sum(stc.data for stc in stcs) / len(stcs)
    flip = label_sign_flip(label, inverse_operator['src'])

    label_mean = np.mean(data, axis=0)
    label_mean_flip = np.mean(flip[:, np.newaxis] * data, axis=0)

    assert_true(label_mean.max() < label_mean_flip.max())
