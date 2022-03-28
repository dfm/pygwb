import numpy as np
from bilby.gw.detector.strain_data import Notch


class StochNotch(Notch):
    def __init__(self, minimum_frequency, maximum_frequency, description):
        """A notch object storing the maximum and minimum frequency of the notch, as well as a description

        Parameters
        ==========
        minimum_frequency, maximum_frequency: float
            The minimum and maximum frequency of the notch
        description: str
            A description of the origin/reason of the notch

        """
        super().__init__(minimum_frequency, maximum_frequency)
        self.description = description

    def print_notch(self):
        print(self.minimum_frequency, self.maximum_frequency, self.description)


class StochNotchList(list):
    def __init__(self, notch_list):
        """A list of notches

        Parameters
        ==========
        notch_list: list
            A list of length-3 tuples of the (min, max) frequency; description for the notches.

        Raises
        ======
        ValueError
            If the list is malformed.
        """

        if notch_list is not None:
            for notch in notch_list:
                if isinstance(notch, tuple) and len(notch) == 3:
                    self.append(StochNotch(*notch))
                else:
                    msg = f"notch_list {notch_list} is malformed"
                    raise ValueError(msg)

    def check_frequency(self, freq):
        """Check if freq is inside the notch list

        Parameters
        ==========
        freq: float
            The frequency to check

        Returns
        =======
        True/False:
            If freq inside any of the notches, return True, else False
        """

        for notch in self:
            if notch.check_frequency(freq):
                return True
        return False

    def get_idxs(self, frequency_array):
        """Get a boolean mask for the frequencies in frequency_array in the notch list

        Parameters
        ==========
        frequency_array: np.ndarray
            An array of frequencies

        Returns
        =======
        idxs: np.ndarray
            An array of booleans which are True for frequencies in the notch list
        inv_idxs: np.ndarray
            An array of booleans which are False for frequencies in the notch list

        """

        df = np.abs(frequency_array[2]-frequency_array[1])
        idxs = []
        df_str = str(df)
        precision = df_str[::-1].find('.')
        for my_iter in range(len(frequency_array)):          
            temp = 0
            if my_iter == 0:
                for notch in self:
                    if not(notch.maximum_frequency <= round(frequency_array[my_iter],precision)-df)  and not ( notch.minimum_frequency >= round(frequency_array[my_iter+1],precision)):
                        temp = True
                        break
                    else:
                        temp = False
            elif my_iter == len(frequency_array)-1:
                for notch in self:
                    if not(notch.maximum_frequency <= round(frequency_array[my_iter-1],precision))  and not ( notch.minimum_frequency >= round(frequency_array[my_iter],precision)+df):
                        temp = True
                        break
                    else:
                        temp = False
            else:
                for notch in self:
                    if not(notch.maximum_frequency <= round(frequency_array[my_iter-1],precision) ) and not ( notch.minimum_frequency >= round(frequency_array[my_iter+1],precision)): 
                        
               
                        
                        temp = True
                        break
                    else:
                        temp = False
            idxs.append(temp)
        inv_idxs = [not elem for elem in idxs]
        return idxs, inv_idxs

    def save_to_txt(self, filename):
        """Save the nocth list to a txt-file (after sorting)

        Parameters
        ==========
        filename: str
            Name of the target file

        """

        fmin = []
        fmax = []
        desc = []
        self.sort_list()
        for n in self:
            fmin.append(n.minimum_frequency)
            fmax.append(n.maximum_frequency)
            desc.append(n.description)

        np.savetxt(
            filename,
            np.transpose([fmin, fmax, desc]),
            fmt=("%-20s  ,  %-20s  ,  %-" + str(len(max(desc)) + 5) + "s"),
        )

    def sort_list(self):
        """Sorts the notch list based on the minimum frequency of the notches

        Parameters
        ==========

        """

        self.sort(key=lambda elem: elem.minimum_frequency)

    @classmethod
    def load_from_file(cls, filename):
        """Load an already existing notch list from a txt-file (with formatting as produced by this code)

        Parameters
        ==========
        filename: str
            Filename of the file containing the notchlist to be read in

        """

        fmin, fmax = np.loadtxt(filename, delimiter=",", unpack=True, usecols=(0, 1))
        desc = np.loadtxt(
            filename, delimiter=",", unpack=True, usecols=(2), dtype="str"
        )

        cls = StochNotchList([])
        if type(fmin) == list:
            for i in range(len(fmin)):
                cls.append(StochNotch(fmin[i], fmax[i], desc[i]))
        else:
            cls.append(StochNotch(fmin, fmax, desc))

        return cls

    @classmethod
    def load_from_file_pre_pyGWB(cls, filename):
        """Load an already existing notch list from a txt-file (with formatting as produced by old code)

        Parameters
        ==========
        filename: str
            Filename of the file containing the notchlist to be read in


        """

        fmin, fmax = np.loadtxt(
            filename, skiprows=1, unpack=True, usecols=(0, 1), dtype=str
        )
        for i in range(len(fmin)):
            fmin[i] = fmin[i][1:-1]
            fmax[i] = fmax[i][:-1]
        _, desc = np.loadtxt(
            filename, skiprows=1, delimiter="\t", unpack=True, usecols=(0, 1), dtype=str
        )

        fmin_b = np.zeros(len(fmin))
        fmax_b = np.zeros(len(fmax))
        for i in range(len(fmin)):
            fmin_b[i] = float(fmin[i])
            fmax_b[i] = float(fmax[i])

        print(fmin, fmax)

        cls = StochNotchList([])
        for i in range(len(fmin_b)):
            cls.append(StochNotch(fmin_b[i], fmax_b[i], desc[i]))

        return cls


def power_lines(fundamental=60, nharmonics=40, df=0.2):
    """
    Create list of power line harmonics (nharmonics*fundamental Hz) to remove

    Parameters
    ==========
    fundamental: float
        Fundamental frequency of the first harmonic
    nharmonics: float
        Number of harmonics (should include all harmonics within studied frequency range of the study)

    Returns
    =======
    notches: list of NoiseLine objects
        List of lines you want to be notched in NoisLine format

    """
    freqs = fundamental * np.arange(1, nharmonics + 1)

    notches = StochNotchList([])
    for f0 in freqs:
        notch = StochNotch(f0 - df / 2, f0 + df / 2, "Power Lines")
        notches.append(notch)

    return notches


def comb(f0, f_spacing, n_harmonics, df, description=None):
    """
    Create a list of comb lines to remove with the form 'f0+n*f_spacing, n=0,1,...,n_harmonics-1'

    Parameters
    ==========
    f0: float
        Fundamental frequency of the first harmonic
    f_spacing: float
        spacing between two subsequent harmonics
    nharmonics: float
        Number of harmonics (should include all harmonics within studied frequency range of the study)
    df: float
        Width of the comb-lines
    description: str (Optional)
        Optional additional description, e.g. known source of the comb

    Returns
    =======
    notches: list of NoiseLine objects
        List of lines you want to be notched in NoisLine format

    """

    notches = StochNotchList([])
    freqs = [f0 + n * f_spacing for n in range(n_harmonics)]
    for f in freqs:
        TotalDescription = f"Comb with fundamental freq {f0} and spacing {f_spacing}"
        if description:
            TotalDescription += " " + description
        notch = StochNotch(f - df / 2, f + df / 2, TotalDescription)
        notches.append(notch)

    return notches


def pulsar_injections(filename, t_start, t_end, doppler=1e-4):
    """
    Create list of frequencies contaminated by pulsar injections

    Parameters
    ==========
    filename: str
        Filename of list containing information about pulsar injections. e.g. for O3 at https://git.ligo.org/stochastic/stochasticdetchar/-/blob/master/O3/notchlists/make_notchlist/input/pulsars.dat
    t_start: int
        GPS start time of run/analysis
    t_end: int
        GPS end time of run/analysis
    doppler: float
        Doppler shift; typical value of v/c for Earth motion in solar system = 1e-4 (default)

    Returns
    =======
    notches: list of NoiseLine objects
        List of lines you want to be notched in NoisLine format
    """

    """
    f_start: pulsar freq at start of time period
    f_end:   pulsar freq at end of time period
    f1:      allow for doppler shifting
    f2:      allow for doppler shifting
    f0:      central freq over entire period
    df:      width
    """

    t_refs, f_refs, f_dots = np.loadtxt(filename, unpack=True)
    notches = StochNotchList([])

    for t_ref, f_ref, f_dot in zip(t_refs, f_refs, f_dots):
        f_start = f_ref + f_dot * (t_start - t_ref)
        f_end = f_ref + f_dot * (t_end - t_ref)
        f1 = f_start * (1 + doppler)
        f2 = f_end * (1 - doppler)
        f0 = (f1 + f2) / 2.0
        df = f1 - f2
        notch = StochNotch(f0 - df / 2, f0 + df / 2, "Pulsar injection")
        notches.append(notch)
    return notches
