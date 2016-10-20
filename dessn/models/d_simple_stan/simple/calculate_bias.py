import os

import numpy as np
from astropy.cosmology import FlatwCDM
from chainconsumer import ChainConsumer
from dessn.models.d_simple_stan.simple.run_stan import get_analysis_data, get_truths_labels_significance
from scipy.misc import logsumexp
from scipy.stats import multivariate_normal

from dessn.models.d_simple_stan.simple.load_stan import load_stan_from_folder


def calculate_bias(chain_dictionary, supernovae, cosmologies, filename="stan_output/biases.npy"):

    if os.path.exists(filename):
        return np.load(filename)

    mask = supernovae[:, 6] == 1
    supernovae = supernovae[mask, :]
    supernovae = supernovae[:20000, :]
    masses = supernovae[:, 4]
    redshifts = supernovae[:, 5]
    apparents = supernovae[:, 1]
    colours = supernovae[:, 3]
    stretches = supernovae[:, 2]
    existing_prob = supernovae[:, 7]

    weight = []

    print(list(chain_dictionary.keys()))
    for i in range(chain_dictionary["mean_MB"].size):
        om = np.round(chain_dictionary["Om"][i], decimals=3)
        key = "%0.3f" % om
        mus = cosmologies[key](redshifts)

        dscale = chain_dictionary["dscale"][i]
        dratio = chain_dictionary["dratio"][i]
        redshift_pre_comp = 0.9 + np.power(10, 0.95 * redshifts)
        mass_correction = dscale * (1.9 * (1 - dratio) / redshift_pre_comp + dratio)
        mabs = apparents - mus + chain_dictionary["alpha"][i] * stretches - chain_dictionary["beta"][i] * colours + mass_correction * masses

        mbx1cs = np.vstack((mabs, stretches, colours)).T
        chain_MB = chain_dictionary["mean_MB"][i]
        chain_x1 = chain_dictionary["mean_x1"][i]
        chain_c = chain_dictionary["mean_c"][i]
        chain_sigmas = np.array([chain_dictionary["sigma_MB"][i], chain_dictionary["sigma_x1"][i], chain_dictionary["sigma_c"][i]])
        chain_sigmas_mat = np.dot(chain_sigmas[:, None], chain_sigmas[None, :])
        chain_correlations = np.dot(chain_dictionary["intrinsic_correlation"][i], chain_dictionary["intrinsic_correlation"][i].T)
        chain_pop_cov = chain_correlations * chain_sigmas_mat
        chain_mean = np.array([chain_MB, chain_x1, chain_c])

        chain_prob = multivariate_normal.logpdf(mbx1cs, chain_mean, chain_pop_cov)
        reweight = logsumexp(chain_prob - existing_prob)
        weight.append(reweight)
        print(weight[-1])

    weights = np.array(weight)
    np.save(filename, weights)
    return weights


if __name__ == "__main__":

    file = os.path.abspath(__file__)
    dir_name = os.path.dirname(__file__) or "."
    output_dir = os.path.abspath(dir_name + "/../output")
    stan_output_dir = os.path.abspath(dir_name + "/stan_output")
    pickle_file = output_dir + os.sep + "supernovae2.npy"
    supernovae = np.load(pickle_file)
    chain_dictionary, post, t, p, fp, nw = load_stan_from_folder(stan_output_dir, replace=False)

    weights = calculate_bias(chain_dictionary, supernovae)

    del chain_dictionary["intrinsic_correlation"]
    for key in list(chain_dictionary.keys()):
        if "_" in key:
            chain_dictionary[key.replace("_", "")] = chain_dictionary[key]
            del chain_dictionary[key]

    vals = get_truths_labels_significance()
    truths = {k[0].replace("_", ""): k[1] for k in vals if not isinstance(k[2], list)}

    n_sne = get_analysis_data()["n_sne"]
    logw = n_sne * weights
    print(logw.min(), logw.max())
    logw -= logw.min() + 0
    print(logw.min(), logw.max())
    print(weights.min(), weights.max(), weights.mean())
    weights = np.exp(-logw)
    print(weights.min(), weights.max(), weights.mean())

    c = ChainConsumer()
    c.add_chain(chain_dictionary, name="Unweighted")
    c.add_chain(chain_dictionary, weights=weights, name="Reweighted")
    c.plot(filename="../output/plot_comparison.png", truth=truths)