import numpy as np
import pytest

import autofit as af
from autofit.mock.mock import Gaussian
from autofit.non_linear.grid import sensitivity as s


@pytest.fixture(name="perturbation_model")
def make_perturbation_model():
    return af.PriorModel(Gaussian)


@pytest.fixture(
    name="search"
)
def make_search():
    return af.MockSearch()


@pytest.fixture(name="sensitivity")
def make_sensitivity(
        perturbation_model,
        search
):
    # noinspection PyTypeChecker
    instance = af.ModelInstance()
    instance.gaussian = Gaussian()
    return s.Sensitivity(
        simulation_instance=instance,
        base_model=af.Collection(
            gaussian=af.PriorModel(Gaussian)
        ),
        perturbation_model=perturbation_model,
        simulate_function=image_function,
        analysis_class=Analysis,
        search=search,
        number_of_steps=2,
    )


x = np.array(range(10))


def image_function(instance: af.ModelInstance):
    image = instance.gaussian(x)
    if hasattr(instance, "perturbation"):
        image += instance.perturbation(x)
    return image


class Analysis(af.Analysis):

    def __init__(self, image: np.array):
        self.image = image

    def log_likelihood_function(self, instance):
        image = image_function(instance)
        return np.mean(np.multiply(-0.5, np.square(np.subtract(self.image, image))))


def test_lists(sensitivity):
    assert len(list(sensitivity._perturbation_instances)) == 8


def test_sensitivity(sensitivity):
    results = sensitivity.run()
    assert len(results) == 8


def test_tuple_step_size(sensitivity):
    sensitivity.number_of_steps = (2, 2, 4)

    assert len(sensitivity._lists) == 16


def test_labels(sensitivity):
    labels = list(sensitivity._labels)
    assert labels == [
        "centre_0.25_intensity_0.25_sigma_0.25",
        "centre_0.25_intensity_0.25_sigma_0.75",
        "centre_0.25_intensity_0.75_sigma_0.25",
        "centre_0.25_intensity_0.75_sigma_0.75",
        "centre_0.75_intensity_0.25_sigma_0.25",
        "centre_0.75_intensity_0.25_sigma_0.75",
        "centre_0.75_intensity_0.75_sigma_0.25",
        "centre_0.75_intensity_0.75_sigma_0.75",
    ]


def test_searches(sensitivity):
    assert len(list(sensitivity._searches)) == 8


@pytest.fixture(
    name="job"
)
def make_job(
        perturbation_model,
        search
):
    instance = af.ModelInstance()
    instance.gaussian = Gaussian()
    instance.perturbation = Gaussian()
    image = image_function(instance)
    # noinspection PyTypeChecker
    return s.Job(
        model=af.Collection(
            gaussian=af.PriorModel(Gaussian)
        ),
        perturbation_model=af.PriorModel(Gaussian),
        analysis=Analysis(image),
        search=search,
    )


def test_perform_job(job):
    result = job.perform()
    assert isinstance(result, s.JobResult)
    assert isinstance(result.perturbed_result, af.Result)
    assert isinstance(result.result, af.Result)


def test_job_paths(
        job,
        search
):
    output_path = search.paths.output_path
    assert job.perturbed_search.paths.output_path == f"{output_path}/[perturbed]"
    assert job.search.paths.output_path == f"{output_path}/[base]"
