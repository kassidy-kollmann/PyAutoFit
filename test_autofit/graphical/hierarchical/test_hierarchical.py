import numpy as np
import pytest
from scipy import stats

from autofit import graphical as g
from autofit.mapper.variable import Variable
from autofit.messages.normal import NormalMessage


def normal_loglike(x, centre, precision):
    diff = np.asanyarray(x) - centre
    se = np.square(diff)
    return np.sum(-precision * se - np.log(2 * np.pi) + np.log(precision)) / 2


def normal_loglike_jacobian(x, centre, precision):
    diff = np.asanyarray(x) - centre
    se = np.square(diff)
    loglike = np.sum(-precision * se - np.log(2 * np.pi) + np.log(precision)) / 2
    jac_x = -precision * diff
    jac_c = np.sum(precision * diff)
    jac_p = np.sum(1 / precision - se) / 2

    return loglike, (jac_x, jac_c, jac_p)


def normal_loglike_t(x, centre, precision):
    # Make log transform of precision so that optimisation is unbounded
    _precision = np.exp(precision)
    return normal_loglike(x, centre, _precision)


def normal_loglike_t_jacobian(x, centre, precision):
    # Make log transform of precision so that optimisation is unbounded
    _precision = np.exp(precision)
    val, jac = normal_loglike_jacobian(x, centre, _precision)
    jac_x, jac_c, jac_p = jac
    jac_p *= _precision
    return val, (jac_x, jac_c, jac_p)


n = 10


@pytest.fixture(name="centres")
def make_centres():
    mu = 0.5
    sigma = 0.5
    centre_dist = stats.norm(loc=mu, scale=sigma)

    return centre_dist.rvs(n)


@pytest.fixture(name="widths")
def make_widths():
    a = 10
    b = 4000
    precision_dist = stats.invgamma(a, scale=b)

    return precision_dist.rvs(n) ** -0.5


@pytest.fixture(name="model_approx")
def make_model_approx(centres, widths):
    centres_ = [Variable(f"x_{i}") for i in range(n)]
    mu_ = Variable("mu")
    logt_ = Variable("logt")

    centre_likelihoods = [
        NormalMessage(c, w).as_factor(x) for c, w, x in zip(centres, widths, centres_)
    ]
    normal_likelihoods = [
        g.FactorJac(
            normal_loglike_t,
            centre,
            mu_,
            logt_,
            factor_jacobian=normal_loglike_t_jacobian,
        )
        for centre in centres_
    ]

    model = g.utils.prod(centre_likelihoods + normal_likelihoods)

    model_approx = g.EPMeanField.from_approx_dists(
        model,
        {
            mu_: NormalMessage(0, 10),
            logt_: NormalMessage(0, 10),
            **{x_: NormalMessage(0, 10) for x_ in centres_},
        },
    )

    return model_approx


def test(model_approx):
    laplace = g.LaplaceOptimiser()
    ep_opt = g.EPOptimiser(model_approx, default_optimiser=laplace)
    new_approx = ep_opt.run(model_approx, max_steps=10)
    print(new_approx)
