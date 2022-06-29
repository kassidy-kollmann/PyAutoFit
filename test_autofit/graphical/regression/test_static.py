from collections import Counter

import pytest

import autofit as af


class StaticSearch(af.NonLinearSearch):
    def __init__(self):
        self.optimisation_counter = Counter()
        self._paths = af.DirectoryPaths()
        self.delta = 1.0

    def fit(
            self,
            model,
            analysis,
            info=None,
            pickle_files=None,
            log_likelihood_cap=None
    ):
        return StaticResult(model)

    def _fit(self, model, analysis, log_likelihood_cap=None):
        pass

    @property
    def config_type(self):
        pass

    @property
    def samples_cls(self):
        pass

    def samples_from(self, model):
        pass

    def samples_via_results_from(self, model):
        pass


class StaticResult:
    def __init__(self, model):
        self.projected_model = model


@pytest.fixture(name="centre")
def make_centre():
    return af.GaussianPrior(mean=1.0, sigma=2.0)


@pytest.fixture(name="analysis_factor_factory")
def make_analysis_factor_factory(centre):
    analysis = af.mock.MockAnalysis()

    def factory():
        return af.AnalysisFactor(
            prior_model=af.Model(
                af.Gaussian,
                centre=centre,
                normalization=af.GaussianPrior(mean=1.0, sigma=2.0),
                sigma=af.GaussianPrior(mean=1.0, sigma=2.0),
            ),
            analysis=analysis
        )

    return factory


@pytest.fixture(name="factor_graph_model")
def make_factor_graph_model(analysis_factor_factory):
    return af.FactorGraphModel(
        analysis_factor_factory()
    )


def test_initial_message(factor_graph_model, centre):
    message = factor_graph_model.mean_field_approximation().mean_field[centre]
    assert message.sigma == centre.sigma


def test_initial_message_multiple(analysis_factor_factory, centre):
    factor_graph_model = af.FactorGraphModel(
        *(
            analysis_factor_factory()
            for _ in range(3)
        )
    )
    message = factor_graph_model.mean_field_approximation().mean_field[centre]
    assert message.sigma == centre.sigma


def test_static(
        factor_graph_model
):
    original_mean_field = factor_graph_model.mean_field_approximation()
    factor = factor_graph_model.graph.factors[0]

    mean_field = original_mean_field

    search = StaticSearch()

    for i in range(3):
        mean_field, _ = search.optimise(
            model_approx=mean_field,
            factor=factor,
        )

        assert list(original_mean_field.mean_field.values()) == list(mean_field.mean_field.values())