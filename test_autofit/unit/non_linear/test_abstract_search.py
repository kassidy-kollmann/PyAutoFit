import os
import shutil

import pytest

import autofit as af
from autoconf import conf
from autofit.non_linear.mock.mock_search import MockSamples
from test_autofit import mock

directory = os.path.dirname(os.path.realpath(__file__))
pytestmark = pytest.mark.filterwarnings("ignore::FutureWarning")


@pytest.fixture(autouse=True)
def set_config_path():
    conf.instance = conf.Config(
        config_path=os.path.join(directory, "files/nlo/config"),
        output_path=os.path.join(directory, "files/nlo/output"),
    )


@pytest.fixture(name="mapper")
def make_mapper():
    return af.ModelMapper()


@pytest.fixture(name="mock_list")
def make_mock_list():
    return [af.PriorModel(mock.MockClassx4), af.PriorModel(mock.MockClassx4)]


@pytest.fixture(name="result")
def make_result():
    mapper = af.ModelMapper()
    mapper.component = mock.MockClassx2Tuple
    # noinspection PyTypeChecker
    return af.Result(
        samples=MockSamples(gaussian_tuples=[(0, 0), (1, 0)]), previous_model=mapper
    )


class TestResult:
    def test_model(self, result):
        component = result.model.component
        assert component.one_tuple.one_tuple_0.mean == 0
        assert component.one_tuple.one_tuple_1.mean == 1
        assert component.one_tuple.one_tuple_0.sigma == 0.2
        assert component.one_tuple.one_tuple_1.sigma == 0.2

    def test_model_absolute(self, result):
        component = result.model_absolute(a=2.0).component
        assert component.one_tuple.one_tuple_0.mean == 0
        assert component.one_tuple.one_tuple_1.mean == 1
        assert component.one_tuple.one_tuple_0.sigma == 2.0
        assert component.one_tuple.one_tuple_1.sigma == 2.0

    def test_model_relative(self, result):
        component = result.model_relative(r=1.0).component
        assert component.one_tuple.one_tuple_0.mean == 0
        assert component.one_tuple.one_tuple_1.mean == 1
        assert component.one_tuple.one_tuple_0.sigma == 0.0
        assert component.one_tuple.one_tuple_1.sigma == 1.0

    def test_raises(self, result):
        with pytest.raises(af.exc.PriorException):
            result.model.mapper_from_gaussian_tuples(
                result.samples.gaussian_tuples, a=2.0, r=1.0
            )


class TestCopyWithNameExtension:
    @staticmethod
    def assert_non_linear_attributes_equal(copy):
        assert copy.paths.name == "phase_name/one"

    def test_copy_with_name_extension(self):
        search = af.MockSearch(af.Paths("phase_name", tag="tag"))
        copy = search.copy_with_name_extension("one")

        self.assert_non_linear_attributes_equal(copy)
        assert search.paths.tag == copy.paths.tag


@pytest.fixture(name="nlo_setup_path")
def test_nlo_setup():
    nlo_setup_path = "{}/files/nlo/setup/".format(
        os.path.dirname(os.path.realpath(__file__))
    )

    if os.path.exists(nlo_setup_path):
        shutil.rmtree(nlo_setup_path)

    os.mkdir(nlo_setup_path)

    return nlo_setup_path


@pytest.fixture(name="nlo_model_info_path")
def test_nlo_model_info():
    nlo_model_info_path = "{}/files/nlo/model_info/".format(
        os.path.dirname(os.path.realpath(__file__))
    )

    if os.path.exists(nlo_model_info_path):
        shutil.rmtree(nlo_model_info_path)

    return nlo_model_info_path


@pytest.fixture(name="nlo_wrong_info_path")
def test_nlo_wrong_info():
    nlo_wrong_info_path = "{}/files/nlo/wrong_info/".format(
        os.path.dirname(os.path.realpath(__file__))
    )

    if os.path.exists(nlo_wrong_info_path):
        shutil.rmtree(nlo_wrong_info_path)

    os.mkdir(nlo_wrong_info_path)

    return nlo_wrong_info_path



class TestLabels:
    def test_param_names(self):
        model = af.PriorModel(mock.MockClassx4)
        assert ["one", "two", "three", "four"] == model.parameter_names

    def test_label_config(self):
        assert conf.instance.label.label("one") == "x4p0"
        assert conf.instance.label.label("two") == "x4p1"
        assert conf.instance.label.label("three") == "x4p2"
        assert conf.instance.label.label("four") == "x4p3"