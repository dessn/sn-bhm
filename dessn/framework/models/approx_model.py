from collections import OrderedDict
import numpy as np
import inspect
import os
from numpy.random import uniform, normal
from scipy.interpolate import interp1d
from collections import Counter

from dessn.framework.model import Model


class ApproximateModel(Model):

    def __init__(self, filename="approximate.stan", num_nodes=4, systematics_scale=1.0, statonly=False):
        if statonly:
            filename = filename.replace(".stan", "_statonly.stan")
        self.statonly = statonly
        file = os.path.abspath(inspect.stack()[0][1])
        directory = os.path.dirname(file)
        stan_file = directory + "/stan/" + filename
        super().__init__(stan_file)
        self.num_redshift_nodes = num_nodes
        self.systematics_scale = systematics_scale

    def get_parameters(self):
        return ["Om", "Ol", "w", "alpha", "beta", "dscale", "dratio", "mean_MB",
                "sigma_MB", "sigma_x1", "sigma_c", "alpha_c", "alpha_x1",
                #"outlier_MB_delta", "outlier_dispersion"
                "delta_alpha", "delta_beta",
                "mean_x1", "mean_c",
                "calibration", "deltas", "intrinsic_correlation"]

    def get_labels(self):
        mapping = OrderedDict([
            ("Om", r"$\Omega_m$"),
            ("Ol", r"$\Omega_\Lambda$"),
            ("w", r"$w$"),
            ("alpha", r"$\alpha$"),
            ("delta_alpha", r"$\delta_\alpha$"),
            ("alpha_c", r"$\alpha_c^{%d}$"),
            ("alpha_x1", r"$\alpha_{x_1}^{%d}$"),
            ("beta", r"$\beta$"),
            ("delta_beta", r"$\delta_\beta$"),
            ("mean_MB", r"$\langle M_B \rangle$"),
            #("outlier_MB_delta", r"$\delta M_B$"),
            #("outlier_dispersion", r"$\sigma_{\rm out}^{%d}$"),
            ("mean_x1", r"$\langle x_1^{%d} \rangle$"),
            ("mean_c", r"$\langle c^{%d} \rangle$"),
            ("sigma_MB", r"$\sigma_{\rm m_B}^{%d}$"),
            ("sigma_x1", r"$\sigma_{x_1}^{%d}$"),
            ("sigma_c", r"$\sigma_{c}^{%d}$"),
            ("dscale", r"$\delta(0)$"),
            ("dratio", r"$\delta(\infty)/\delta(0)$"),
            ("calibration", r"$\delta \mathcal{Z}_{%d}$"),
            ("deltas", r"$\Delta_{%d}$")
        ])
        return mapping

    def get_init(self, **kwargs):
        deta_dcalib = kwargs["deta_dcalib"]
        num_supernova = kwargs["n_sne"]
        num_surveys = kwargs["n_surveys"]
        randoms = {
            "Om": uniform(0.2, 0.4),
            "Ol": uniform(0.3, 0.9),
            "w": uniform(-1.1, -0.9),
            "alpha": uniform(0.1, 0.2),
            "delta_alpha": uniform(-0.1, 0.1),
            "beta": uniform(2.5, 3.5),
            "delta_beta": uniform(-0.1, 0.1),
            "dscale": uniform(0, 0.2),
            "dratio": uniform(0, 1),
            "mean_MB": uniform(-19.5, -19.2),
            "alpha_c": uniform(0, 0.05, size=(num_surveys,)),
            "delta_c": uniform(0, 0.05, size=(num_surveys,)),
            # "alpha_x1": uniform(0, 0.05, size=(num_surveys,)),
            #"outlier_MB_delta": uniform(0.1, 2),
            #"outlier_dispersion": 0.5 + uniform(low=0.1, high=1.0, size=3),
            "mean_x1": uniform(-0.2, 0.2, size=(num_surveys, self.num_redshift_nodes)),
            "mean_c": uniform(-0.1, 0.1, size=(num_surveys, self.num_redshift_nodes)),
            "log_sigma_MB": uniform(-2, -0.5, size=(num_surveys,)),
            "log_sigma_x1": uniform(-2, 1, size=(num_surveys,)),
            "log_sigma_c": uniform(-2, -0.5, size=(num_surveys,)),
            "deviations": normal(scale=0.2, size=(num_supernova, 3)),
            "deltas": normal(scale=0.1, size=(num_surveys, 4)),
            "calibration": uniform(-0.3, 0.3, size=deta_dcalib.shape[2])
        }
        chol = [[[1.0, 0.0, 0.0],
                [np.random.random() * 0.1 - 0.05, np.random.random() * 0.1 + 0.7, 0.0],
                [np.random.random() * 0.1 - 0.05, np.random.random() * 0.1 - 0.05,
                 np.random.random() * 0.1 + 0.7]] for i in range(num_surveys)]
        randoms["intrinsic_correlation"] = chol
        self.logger.info("Initial starting point is: %s" % randoms)
        return randoms

    def get_name(self):
        return "Approx"

    def get_data(self, simulations, cosmology_index, add_zs=None):

        if not type(simulations) == list:
            simulations = [simulations]

        n_snes = [sim.num_supernova for sim in simulations]
        data_list = [s.get_passed_supernova(s.num_supernova, cosmology_index=cosmology_index) for s in simulations]
        print(data_list[0].keys())
        n_surveys = len(data_list)

        global_calibration = self.get_num_global_from_sims(simulations)

        self.logger.info("Got observational data")
        # Redshift shenanigans below used to create simpsons rule arrays
        # and then extract the right redshift indexes from them

        n_z = 2000  # Defines how many points we get in simpsons rule
        num_nodes = self.num_redshift_nodes

        nodes_list = []
        node_weights_list = []
        sim_data_list = []
        num_calibs = []
        mean_masses = []
        survey_map = []
        for i, (data, n_sne, sim) in enumerate(zip(data_list, n_snes, simulations)):
            num_calibs.append(data["deta_dcalib"].shape[2])
            redshifts = data["redshifts"]
            masses = data["masses"]
            mean_masses.append(np.mean(masses))
            survey_map += [i + 1] * redshifts.size  # +1 for Stan being 1 indexed

            if num_nodes == 1:
                node_weights = np.array([[1]] * n_sne)
                nodes = [0.0]
            else:
                zs = np.sort(redshifts)
                nodes = np.linspace(zs[2], zs[-5], num_nodes)
                node_weights = self.get_node_weights(nodes, redshifts)

            nodes_list.append(nodes)
            node_weights_list.append(node_weights)

            if add_zs is not None:
                sim_data = add_zs(sim)
            else:
                sim_data = {}

            sim_data_list.append(sim_data)

        node_weights = np.concatenate(node_weights_list)
        num_calib = np.sum(num_calibs) - (global_calibration * (len(num_calibs) - 1))

        # data_list is a list of dictionaries, aiming for a dictionary with lists
        data_dict = {}
        if len(data_list) == 1:
            data_dict = data_list[0]
            data_dict["n_snes"] = [data_dict["n_sne"]]
        else:
            for key in data_list[0].keys():
                if key == "deta_dcalib":  # Changing shape of deta_dcalib makes this different
                    offset = 0
                    vals = []
                    for data in data_list:
                        nsne = data["n_sne"]
                        blank = np.zeros((nsne, 3, num_calib))
                        n = data["deta_dcalib"].shape[2] - global_calibration
                        blank[:, :, :global_calibration] = data["deta_dcalib"][:, :, :global_calibration]
                        blank[:, :, offset:offset+n] = data["deta_dcalib"][:, :, global_calibration:]
                        offset += n
                        vals.append(blank)
                    data_dict[key] = np.vstack(vals)
                else:
                    if type(data_list[0][key]) in [int, float]:
                        data_dict[key] = [d[key] for d in data_list]
                    else:
                        data_dict[key] = np.concatenate([d[key] for d in data_list])

            data_dict["n_snes"] = data_dict["n_sne"]
            data_dict["n_sne"] = np.sum(data_dict["n_sne"])

        sim_redshifts = np.array([sim["sim_redshifts"] for sim in sim_data_list if "sim_redshifts" in sim.keys()]).flatten()
        redshifts = np.array([z for data in data_list for z in data["redshifts"]])
        zs = sorted(redshifts.tolist() + sim_redshifts.tolist())
        dz = zs[-1] / n_z
        added_zs = [0]
        pz = 0
        for z in zs:
            est_point = int((z - pz) / dz)
            if est_point % 2 == 0:
                est_point += 1
            est_point = max(3, est_point)
            new_points = np.linspace(pz, z, est_point)[1:-1].tolist()
            added_zs += new_points
            pz = z

        n_z = len(zs) + len(added_zs)
        n_simps = int((n_z + 1) / 2)
        to_sort = [(z, -1, -1) for z in added_zs] + [(z, i, -1) for i, z in enumerate(redshifts)]
        if add_zs is not None:
            to_sort += [(z, -1, i) for i, z in enumerate(sim_redshifts)]
        to_sort.sort()
        final_redshifts = np.array([z[0] for z in to_sort])
        sorted_vals = [(z[1], i) for i, z in enumerate(to_sort) if z[1] != -1]
        sorted_vals.sort()
        final = [int(z[1] / 2 + 1) for z in sorted_vals]
        # End redshift shenanigans
        n_calib = data_dict["deta_dcalib"].shape[2]
        update = {
            "n_z": n_z,
            "n_calib": n_calib,
            "n_surveys": n_surveys,
            "survey_map": survey_map,
            "n_simps": n_simps,
            "zs": final_redshifts,
            "zspo": 1 + final_redshifts,
            "zsom": (1 + final_redshifts) ** 3,
            "zsok": (1 + final_redshifts) ** 2,
            "redshift_indexes": final,
            "redshift_pre_comp": 0.9 + np.power(10, 0.95 * redshifts),
            "calib_std": np.ones(n_calib),
            "num_nodes": num_nodes,
            "node_weights": node_weights,
            "nodes": nodes_list,
            "outlier_MB_delta": 0.0,
            "outlier_dispersion": np.linalg.cholesky(np.eye(3)),
            "systematics_scale": self.systematics_scale
        }

        sim_dict = {}
        if add_zs is not None:
            for key in sim_data_list[0].keys():
                sim_dict[key] = [d[key] for d in sim_data_list]
            sim_dict["n_sim"] = sim_dict["n_sim"][0]
            n_sim = sim_dict["n_sim"]
            sim_sorted_vals = [(z[2], i) for i, z in enumerate(to_sort) if z[2] != -1]
            sim_sorted_vals.sort()
            sim_final = [int(z[1] / 2 + 1) for z in sim_sorted_vals]
            update["sim_redshift_indexes"] = np.array(sim_final).reshape((n_surveys, n_sim))
            update["sim_redshift_pre_comp"] = (0.9 + np.power(10, 0.95 * sim_redshifts)).reshape((n_surveys, n_sim))

            sim_node_weights = []
            for sim_data, nodes in zip(sim_data_list, nodes_list):
                if num_nodes == 1:
                    sim_node_weights += [[1]] * sim_data["sim_redshifts"].size
                else:
                    sim_node_weights.append(self.get_node_weights(nodes, sim_data["sim_redshifts"]))
            update["sim_node_weights"] = np.array(sim_node_weights).reshape((n_surveys, n_sim, num_nodes))

        obs_data = np.array(data_dict["obs_mBx1c"])
        self.logger.debug("Obs x1 std is %f, colour std is %f" % (np.std(obs_data[:, 1]), np.std(obs_data[:, 2])))

        # Add in data for the approximate selection efficiency in mB
        means, stds, alphas, correction_skewnorms, norms, signs, covs = [], [], [], [], [], [], []
        for sim in simulations:
            res = sim.get_approximate_correction()
            correction_skewnorm, vals, cov = res
            mean, std, alpha, norm = vals.tolist()
            means.append(mean)
            stds.append(std)
            correction_skewnorms.append(1 if correction_skewnorm else 0)
            covs.append(cov)
            if alpha is not None:
                alphas.append(alpha)
                signs.append(np.sign(alpha))
            else:
                alphas.append(0.01)
                signs.append(1)
            if norm is not None:
                norms.append(norm)
            else:
                norms.append(1)
        update["mB_mean_orig"] = means
        update["mB_width_orig"] = stds
        update["mB_alpha_orig"] = alphas
        update["mB_norm_orig"] = norms
        update["mB_sgn_alpha"] = signs
        update["mB_cov"] = covs
        update["correction_skewnorm"] = correction_skewnorms

        update["mean_mass"] = mean_masses

        final_dict = {**data_dict, **update, **sim_dict}
        return final_dict

    def get_num_global_from_sims(self, simulations):
        num_sims = len(simulations)
        all_labels = [l for s in simulations for l in s.get_systematic_names()]
        counted = Counter(all_labels)
        global_labels = [key for key in counted.keys() if counted[key] == num_sims]
        return len(global_labels)

    def get_systematic_labels(self, simulations):
        label_list = [s.get_systematic_names() for s in simulations]
        if len(label_list[0]) == 0:
            label_list[0].append("Fake")
        global_calibration = self.get_num_global_from_sims(simulations)
        start = label_list[0][:global_calibration]
        for l in label_list:
            start += l[global_calibration:]
        res = [r"$\delta [ %s ]$" % s for s in start]
        return res

    def get_node_weights(self, nodes, redshifts):
        indexes = np.arange(nodes.size)
        interps = interp1d(nodes, indexes, kind='linear', fill_value="extrapolate")(redshifts)
        node_weights = np.array([1 - np.abs(v - indexes) for v in interps])
        end_mask = np.all(node_weights < 0, axis=1)
        node_weights *= (node_weights <= 1) & (node_weights >= 0)
        node_weights[end_mask, -1] = 1.0
        node_weights = np.abs(node_weights)
        reweight = np.sum(node_weights, axis=1)
        node_weights = (node_weights.T / reweight).T
        return node_weights

    def correct_chain(self, dictionary, simulation, data):
        del dictionary["intrinsic_correlation"]
        return dictionary


class ApproximateModelOl(ApproximateModel):
    def __init__(self, filename="approximate_ol.stan", num_nodes=4, systematics_scale=1.0, statonly=False):
        super().__init__(filename, num_nodes=num_nodes, systematics_scale=systematics_scale, statonly=statonly)


class ApproximateModelW(ApproximateModel):
    def __init__(self, filename="approximate_w.stan", num_nodes=4, systematics_scale=1.0, statonly=False, prior=False):
        if prior:
            filename = filename.replace(".stan", "_omprior.stan")
        super().__init__(filename, num_nodes=num_nodes, systematics_scale=systematics_scale, statonly=statonly)


