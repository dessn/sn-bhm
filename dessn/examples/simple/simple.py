import logging
import os
import sys

import numpy as np

from dessn.framework.edge import Edge, EdgeTransformation
from dessn.framework.model import Model
from dessn.framework.parameter import ParameterObserved, ParameterLatent, \
    ParameterUnderlying, ParameterTransformation
from dessn.framework.samplers.ensemble import EnsembleSampler
from scipy import stats


def get_data(n=50, theta_1=100.0, theta_2=20.0, scale=1.0, seed=1):
    np.random.seed(seed)

    data = stats.norm.rvs(size=n, loc=theta_1, scale=theta_2) * scale
    error = 0.2 * np.sqrt(data)
    data += stats.norm.rvs(size=n) * error

    return data, error


class ObservedFlux(ParameterObserved):
    def __init__(self, n=100):
        self.n = n
        flux, error = get_data(n=n, scale=0.5)
        super(ObservedFlux, self).__init__("flux", "$f$", flux, group="Flux")


class ObservedFluxError(ParameterObserved):
    def __init__(self, n=100):
        self.n = n
        flux, error = get_data(n=n, scale=0.5)
        super(ObservedFluxError, self).__init__("flux_error", r"$\sigma_f$", error, group="Flux")


class LatentLuminosity(ParameterLatent):

    def __init__(self, n=100):
        super(LatentLuminosity, self).__init__("luminosity", "$L$", group="Luminosity")
        self.n = n

    def get_num(self):
        return self.n

    def get_suggestion_requirements(self):
        return ["flux"]

    def get_suggestion(self, data):
        return data["flux"]

    def get_suggestion_sigma(self, data):
        return data["flux"] * 0.05


class UnderlyingSupernovaDistribution1(ParameterUnderlying):

    def get_log_prior(self, data):
        """ We framework the prior enforcing realistic values"""
        mean = data["SN_theta_1"]
        if mean < 0 or mean > 200:
            return -np.inf
        return 1

    def __init__(self):
        super(UnderlyingSupernovaDistribution1, self).__init__("SN_theta_1", r"$\theta_1$", group="Supernova")

    def get_suggestion_requirements(self):
        return []

    def get_suggestion(self, data):
        return 50

    def get_suggestion_sigma(self, data):
        return 5


class UnderlyingSupernovaDistribution2(ParameterUnderlying):

    def get_log_prior(self, data):
        """ We framework the prior enforcing realistic values"""
        sigma = data["SN_theta_2"]
        if sigma < 0 or sigma > 100:
            return -np.inf
        return 1

    def __init__(self):
        super(UnderlyingSupernovaDistribution2, self).__init__("SN_theta_2", r"$\theta_2$", group="Supernova")

    def get_suggestion_requirements(self):
        return []

    def get_suggestion(self, data):
        return 5 # Deliberately wrong

    def get_suggestion_sigma(self, data):
        return 0.5


class UselessTransformation(ParameterTransformation):
    def __init__(self):
        super(UselessTransformation, self).__init__("double_luminosity", "$2L$", group="Transformed Luminosity")


class LuminosityToAdjusted(EdgeTransformation):
    def __init__(self):
        super(LuminosityToAdjusted, self).__init__("double_luminosity", "luminosity")

    def get_transformation(self, data):
        return {"double_luminosity": data["luminosity"] * 2.0}


class FluxToLuminosity(Edge):
    def __init__(self):
        super(FluxToLuminosity, self).__init__(["flux", "flux_error"], "luminosity")

    def get_log_likelihood(self, data):
        l = data["luminosity"]
        f = data["flux"]
        e = data["flux_error"]
        return -((f - l) * (f - l) / (2.0 * e * e) - np.log(np.sqrt(2 * np.pi) * e))


class LuminosityToSupernovaDistribution(Edge):
    def __init__(self):
        super(LuminosityToSupernovaDistribution, self).__init__("double_luminosity", ["SN_theta_1", "SN_theta_2"])

    def get_log_likelihood(self, data):
        l = data["double_luminosity"]
        t1 = data["SN_theta_1"]
        t2 = data["SN_theta_2"]
        if t2 < 0:
            return -np.inf
        return -(l - t1) * (l - t1) / (2.0 * t2 * t2) - np.log(np.sqrt(2 * np.pi) * t2)


class ExampleModel(Model):
    def __init__(self):
        super(ExampleModel, self).__init__("ExampleModel")

        n = 30

        flux = ObservedFlux(n=n)
        flux_error = ObservedFluxError(n=n)
        luminosity = LatentLuminosity(n=n)
        useless = UselessTransformation()
        supernova1 = UnderlyingSupernovaDistribution1()
        supernova2 = UnderlyingSupernovaDistribution2()
        self.add_node(flux)
        self.add_node(flux_error)
        self.add_node(luminosity)
        self.add_node(useless)
        self.add_node(supernova1)
        self.add_node(supernova2)

        self.add_edge(FluxToLuminosity())
        self.add_edge(LuminosityToAdjusted())
        self.add_edge(LuminosityToSupernovaDistribution())

        self.finalise()


if __name__ == "__main__":
    only_data = len(sys.argv) > 1
    if only_data:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.DEBUG)
    dir_name = os.path.dirname(__file__)
    logging.info("Creating framework")
    exampleModel = ExampleModel()
    temp_dir = os.path.abspath(dir_name + "/output")

    if not only_data:
        plot_file = os.path.abspath(dir_name + "/output/surfaces.png")
        plot_file2 = os.path.abspath(dir_name + "/output/walk.png")
        pgm_file = os.path.abspath(dir_name + "/output/pgm.png")
        exampleModel.get_pgm(pgm_file)

    logging.info("Starting fit")
    sampler = EnsembleSampler(num_walkers=64, num_steps=15000, num_burn=5000,
                              temp_dir=temp_dir, save_interval=60)
    chain_consumer = exampleModel.fit(sampler)

    if not only_data:
        chain_consumer.configure_general(bins=0.8)
        print(chain_consumer.get_summary())
        chain_consumer.plot_walks(filename=plot_file2)
        chain_consumer.plot(filename=plot_file, figsize=(6, 6), truth=[100, 20], legend=False)
