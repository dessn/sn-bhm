from dessn.framework.parameter import ParameterUnderlying
import numpy as np


class OmegaM(ParameterUnderlying):
    def __init__(self):
        super(OmegaM, self).__init__("omega_m", r"$\Omega_m$", group="Cosmology")

    def get_log_prior(self, data):
        om = data["omega_m"]
        if om < 0.05 or om > 0.7:
            return -np.inf
        # return -(om-0.4)*(om-0.4)/(2*0.001*0.001)
        return 1

    def get_suggestion(self, data):
        return 0.30

    def get_suggestion_sigma(self, data):
        return 0.05


class Hubble(ParameterUnderlying):
    def __init__(self):
        super(Hubble, self).__init__("H0", "$H_0$", group="Cosmology")

    def get_log_prior(self, data):
        h0 = data["H0"]
        if h0 < 50 or h0 > 100:
            return -np.inf
        # return -(((h0-80)/(2*0.1))**2)
        return 1

    def get_suggestion(self, data):
        return 72

    def get_suggestion_sigma(self, data):
        return 5


class Magnitude(ParameterUnderlying):
    def __init__(self):
        super(Magnitude, self).__init__("mag", r"$M_B$", group="SNIa")

    def get_log_prior(self, data):
        m = data["mag"]
        if m < -22 or m > -17:
            return -np.inf
        return 1

    def get_suggestion(self, data):
        return -19.3

    def get_suggestion_sigma(self, data):
        return 0.5


class IntrinsicScatter(ParameterUnderlying):
    def __init__(self):
        super(IntrinsicScatter, self).__init__("scatter", r"$\sigma_{\rm int}$", group="SNIa")
        self.prefactor = np.log(np.sqrt(2 * np.pi) * 0.01)

    def get_log_prior(self, data):
        if data["scatter"] < 0 or data["scatter"] > 1:
            return -np.inf
        val = np.log10(data["scatter"])
        return -(val + 2) * (val + 2) / (0.01 * 0.01 * 2) - self.prefactor

    def get_suggestion(self, data):
        return 0.1  # Deliberately wrong to test recovery

    def get_suggestion_sigma(self, data):
        return 0.09


class AlphaStretch(ParameterUnderlying):
    def __init__(self):
        super().__init__("alpha", r"$\alpha$", group="Corrections")

    def get_suggestion_sigma(self, data):
        return 0.5

    def get_suggestion(self, data):
        return 0.1

    def get_log_prior(self, data):
        if data["alpha"] < -2 or data["alpha"] > 2:
            return -np.inf
        return 1


class BetaColour(ParameterUnderlying):
    def __init__(self):
        super().__init__("beta", r"$\beta$", group="Corrections")

    def get_suggestion_sigma(self, data):
        return 2

    def get_suggestion(self, data):
        return 3

    def get_log_prior(self, data):
        if data["beta"] < -10 or data["beta"] > 10:
            return -np.inf
        return 1
