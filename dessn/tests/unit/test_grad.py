from ...framework.model import Model
from ...framework.parameter import ParameterUnderlying, ParameterObserved, ParameterLatent
from ...framework.edge import Edge
import numpy as np


class Observed(ParameterObserved):
    def __init__(self):
        super().__init__("obs", "obs", np.array([0.0]))


class Underlying(ParameterUnderlying):
    def __init__(self):
        super().__init__("mean", "mean")

    def get_suggestion_sigma(self, data):
        return 2.0

    def get_suggestion(self, data):
        return 0.0

    def get_log_prior(self, data):
        return 0.0


class TheEdge(Edge):
    def __init__(self):
        super().__init__("obs", "mean")

    def get_log_likelihood(self, data):
        o, m = data["obs"], data["mean"]
        return -0.5 * (o - m)**2 - np.log(np.sqrt(2 * np.pi) * 1.0)


def test_gradient():
    m = Model("Model")
    m.add_node(Underlying())
    m.add_node(Observed())
    m.add_edge(TheEdge())
    m.finalise()
    x = 2.0
    expected = [-x]
    grad = m._get_log_posterior_grad([x])
    assert np.allclose(grad, expected)


def test_fit():
    m = Model("Model")
    m.add_node(Underlying())
    m.add_node(Observed())
    m.add_edge(TheEdge())
    m.finalise()
    np.random.seed(0)
    m.fit_model(num_steps=8010, num_burn=10)
    consumer = m.get_consumer()
    consumer.configure_general(bins=1.4)
    summary = np.array(consumer.get_summary()[0]["mean"])
    expected = np.array([-1.0, 0.0, 1.0])
    threshold = 0.1
    diff = np.abs(expected - summary)
    assert np.all(diff < threshold)
