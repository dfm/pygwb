import os
import unittest

import bilby
import gwpy
import numpy as np

from pygwb import baseline, network, omega_spectra


class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.interferometer_1 = bilby.gw.detector.get_empty_interferometer("H1")
        self.interferometer_2 = bilby.gw.detector.get_empty_interferometer("H1")
        self.interferometer_2.name = "H2"
        self.interferometer_3 = bilby.gw.detector.get_empty_interferometer("L1")
        self.duration = 4.0
        self.sampling_frequency = 2048.0
        self.frequencies = np.arange(100)
        self.test_from_baselines()
        self.test_network_initialisation()

    def tearDown(self):
        del self.interferometer_1
        del self.interferometer_2
        del self.interferometer_3
        del self.duration
        del self.frequencies

    def test_network_initialisation(self):
        ifos = [self.interferometer_1, self.interferometer_2, self.interferometer_3]
        self.net_ifos = network.Network("test_net", ifos)
        self.assertTrue(ifos[0].name, self.net_ifos.interferometers[0].name)

    def test_from_baselines(self):
        pickled_base_1 = baseline.Baseline.load_from_pickle(
            "test/test_data/H1L1_1247644138-1247645038.pickle"
        )
        pickled_base_2 = baseline.Baseline.load_from_pickle(
            "test/test_data/H1L1_1247644138-1247645038.pickle"
        )
        bases = [pickled_base_1, pickled_base_2]
        self.net_load = network.Network.from_baselines("test_net", bases)

    def test_set_duration_from_ifo_1(self):
        self.interferometer_1.duration = self.duration
        ifos = [self.interferometer_1, self.interferometer_2, self.interferometer_3]
        net = network.Network("test_net", ifos)
        self.assertTrue(net.duration, self.duration)

    def test_set_duration_from_ifos(self):
        ifos = [self.interferometer_1, self.interferometer_2, self.interferometer_3]
        for ifo in ifos:
            ifo.duration = self.duration
        net = network.Network("test_net", ifos)
        self.assertTrue(net.duration, self.duration)

    def test_set_duration_from_network(self):
        ifos = [self.interferometer_1, self.interferometer_2, self.interferometer_3]
        net = network.Network("test_net", ifos, duration=self.duration)
        self.assertTrue(net.duration, self.duration)
        for ifo in net.interferometers:
            self.assertTrue(ifo.duration, self.duration)

    def test_set_interferometer_data_from_simulator(self):
        ifos = [self.interferometer_1, self.interferometer_2]
        duration = 10
        GWB_intensity = gwpy.frequencyseries.FrequencySeries(
            1.0e-45 * np.ones(64), frequencies=np.arange(64)
        )
        N_segments = 4
        sampling_frequency = 128
        for ifo in ifos:
            ifo.duration = duration
            ifo.sampling_frequency = sampling_frequency
            ifo.power_spectral_density = bilby.gw.detector.PowerSpectralDensity(
                ifo.frequency_array,
                np.nan_to_num(ifo.power_spectral_density_array, posinf=1.0e-41),
            )
        net = network.Network("test_net", ifos)
        net.set_interferometer_data_from_simulator(
            GWB_intensity, N_segments, sampling_frequency
        )
        self.assertFalse(
            np.isnan(net.interferometers[0].strain_data.time_domain_strain).any()
        )
        net.save_interferometer_data_to_file()
        os.remove('test_net_STRAIN-0-40.hdf5')

    #    def test_save_interferometer_data_to_file(self):

    def test_combine_point_estimate_sigma_spectra(self):
        self.net_load.combine_point_estimate_sigma_spectra()
        self.assertFalse(np.isnan(self.net_load.point_estimate_spectrum).any())
        self.assertFalse(np.isnan(self.net_load.sigma_spectrum).any())

    def test_break_combine_point_estimate_sigma_spectra(self):
        with self.assertRaises(AttributeError):
            self.net_ifos.combine_point_estimate_sigma_spectra()
        pickled_base_1 = baseline.Baseline.load_from_pickle(
            "test/test_data/H1L1_1247644138-1247645038.pickle"
        )
        pickled_base_2 = baseline.Baseline.load_from_pickle(
            "test/test_data/H1L1_1247644138-1247645038.pickle"
        )
        pickled_base_1.point_estimate_spectrum = omega_spectra.OmegaSpectrum(pickled_base_1.point_estimate_spectrum.value, alpha=5, fref=100, h0=1)
        bases = [pickled_base_1, pickled_base_2]
        net_break = network.Network.from_baselines("test_net", bases)
        with self.assertRaises(ValueError):
            net_break.combine_point_estimate_sigma_spectra()

    def test_set_point_estimate_sigma(self):
        self.net_load.set_point_estimate_sigma()
        self.assertEqual(self.net_load.point_estimate, -7.744999856880781e-06)
        self.assertEqual(self.net_load.sigma, 1.7148320693913875e-06)
        self.net_load.set_point_estimate_sigma(notch_list_path='./test/test_data/Official_O3_HL_notchlist.txt')
        self.assertEqual(self.net_load.point_estimate, -6.172642194145591e-06)
        self.assertEqual(self.net_load.sigma, 1.8090361433171534e-06)

if __name__ == "__main__":
    unittest.main()
