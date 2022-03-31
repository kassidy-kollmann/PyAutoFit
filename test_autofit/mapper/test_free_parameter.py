import pytest

import autofit as af
from autofit.non_linear.analysis.analysis import FreeParameterAnalysis
from autofit.non_linear.mock.mock_search import MockOptimizer


@pytest.fixture(
    name="model"
)
def make_model():
    return af.Model(af.Gaussian)


def test_copy():
    model = af.Model(af.Gaussian)
    copy = model.copy()

    collection = af.Collection(model, copy)

    assert collection.prior_count == model.prior_count


class Analysis(af.Analysis):
    def log_likelihood_function(self, instance):
        return 1.0 if isinstance(
            instance,
            af.Gaussian
        ) else 0.0


def test_log_likelihood(
        modified,
        combined_analysis
):
    assert combined_analysis.log_likelihood_function(
        modified.instance_from_prior_medians()
    ) == 2


def test_analyses_example():
    model = af.Model(af.Gaussian)
    analyses = []

    for prior, image in [
        (af.UniformPrior(), 0),
        (af.UniformPrior(), 1),
    ]:
        copy = model.copy()
        copy.centre = prior
        analyses.append(
            Analysis(

            )
        )


@pytest.fixture(
    name="combined_analysis"
)
def make_combined_analysis(model):
    return (Analysis() + Analysis()).with_free_parameters(
        model.centre
    )


def test_multiple_free_parameters(model):
    combined_analysis = (Analysis() + Analysis()).with_free_parameters(
        model.centre,
        model.sigma
    )
    first, second = combined_analysis.modify_model(model)
    assert first.centre is not second.centre
    assert first.sigma is not second.sigma


def test_add_free_parameter(
        combined_analysis
):
    assert isinstance(
        combined_analysis,
        FreeParameterAnalysis
    )


@pytest.fixture(
    name="modified"
)
def make_modified(
        model,
        combined_analysis
):
    return combined_analysis.modify_model(model)


def test_modify_model(
        modified
):
    assert isinstance(modified, af.Collection)
    assert len(modified) == 2


def test_modified_models(
        modified
):
    first, second = modified

    assert isinstance(
        first.sigma,
        af.Prior
    )
    assert first.sigma == second.sigma
    assert first.centre != second.centre


def test_integration(
        combined_analysis,
        model
):
    optimizer = MockOptimizer()
    result = optimizer.fit(
        model,
        combined_analysis
    )
    result_1, result_2 = result

    assert result_1._model.centre is not result_2._model.centre
    assert result_1._model.sigma is result_2._model.sigma


def test_tuple_prior(model):
    model.centre = af.TuplePrior(
        centre_0=af.UniformPrior()
    )
    combined = (Analysis() + Analysis()).with_free_parameters(
        model.centre
    )

    first, second = combined.modify_model(model)
    assert first.centre.centre_0 != second.centre.centre_0


def test_prior_model(model):
    model = af.Collection(
        model=model
    )
    combined = (Analysis() + Analysis()).with_free_parameters(
        model.model
    )
    modified = combined.modify_model(model)
    first = modified[0].model
    second = modified[1].model

    assert first is not second
    assert first != second
    assert first.centre != second.centre