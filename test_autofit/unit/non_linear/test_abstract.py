import os
import shutil

import pytest

import autofit as af
from autoconf import conf
from autofit.non_linear.mock.mock_nlo import MockSamples
from test_autofit.mock import (
    GeometryProfile,
    MockClassNLOx4,
)

directory = os.path.dirname(os.path.realpath(__file__))
pytestmark = pytest.mark.filterwarnings("ignore::FutureWarning")


@pytest.fixture(autouse=True)
def set_config_path():
    conf.instance = conf.Config(
        config_path=os.path.join(directory, "files/nlo/config"),
        output_path=os.path.join(directory, "files/nlo/output")
    )


@pytest.fixture(name="mapper")
def make_mapper():
    return af.ModelMapper()


@pytest.fixture(name="mock_list")
def make_mock_list():
    return [af.PriorModel(MockClassNLOx4), af.PriorModel(MockClassNLOx4)]


@pytest.fixture(name="result")
def make_result():
    mapper = af.ModelMapper()
    mapper.profile = GeometryProfile
    # noinspection PyTypeChecker
    return af.Result(
        samples=MockSamples(gaussian_tuples=[(0, 0), (1, 0)]),
        previous_model=mapper,
    )


class TestInitialize:

    def test__prior__points_sample_priors(self):

        model = af.PriorModel(MockClassNLOx4)
        model.one = af.UniformPrior(lower_limit=0.099, upper_limit=0.101)
        model.two = af.UniformPrior(lower_limit=0.199, upper_limit=0.201)
        model.three = af.UniformPrior(lower_limit=0.299, upper_limit=0.301)
        model.four = af.UniformPrior(lower_limit=0.399, upper_limit=0.401)

        non_linear = af.Emcee(initialize_method="prior")

        points = non_linear.initial_points_from_model(number_of_points=2, model=model)

        assert 0.099 < points[0,0] < 0.101
        assert 0.099 < points[1,0] < 0.101
        assert 0.199 < points[0,1] < 0.201
        assert 0.199 < points[1,1] < 0.201
        assert 0.299 < points[0,2] < 0.301
        assert 0.299 < points[1,2] < 0.301
        assert 0.399 < points[0,3] < 0.401
        assert 0.399 < points[1,3] < 0.401

    def test__ball__points_sample_centre_of_priors(self):

        model = af.PriorModel(MockClassNLOx4)
        model.one = af.UniformPrior(lower_limit=0.0, upper_limit=1.0)
        model.two = af.UniformPrior(lower_limit=0.0, upper_limit=2.0)
        model.three = af.UniformPrior(lower_limit=0.0, upper_limit=3.0)
        model.four = af.UniformPrior(lower_limit=0.0, upper_limit=4.0)

        non_linear = af.Emcee(
            initialize_method="ball",
            initialize_ball_lower_limit=0.4999,
            initialize_ball_upper_limit=0.5001
        )

        points = non_linear.initial_points_from_model(number_of_points=2, model=model)

        assert 0.499 < points[0,0] < 0.501
        assert 0.499 < points[1,0] < 0.501
        assert 0.999 < points[0,1] < 1.001
        assert 0.999 < points[1,1] < 1.001
        assert 1.499 < points[0,2] < 1.501
        assert 1.499 < points[1,2] < 1.501
        assert 1.999 < points[0,3] < 2.001
        assert 1.999 < points[1,3] < 2.001

        non_linear = af.Emcee(
            initialize_method="ball",
            initialize_ball_lower_limit=0.7999,
            initialize_ball_upper_limit=0.8001
        )

        points = non_linear.initial_points_from_model(number_of_points=2, model=model)

        assert 0.799 < points[0,0] < 0.801
        assert 0.799 < points[1,0] < 0.801
        assert 1.599 < points[0,1] < 1.601
        assert 1.599 < points[1,1] < 1.601
        assert 2.399 < points[0,2] < 2.401
        assert 2.399 < points[1,2] < 2.401
        assert 3.199 < points[0,3] < 3.201
        assert 3.199 < points[1,3] < 3.201


class TestResult:
    def test_model(self, result):
        profile = result.model.profile
        assert profile.centre_0.mean == 0
        assert profile.centre_1.mean == 1
        assert profile.centre_0.sigma == 0.05
        assert profile.centre_1.sigma == 0.05

    def test_model_absolute(self, result):
        profile = result.model_absolute(a=2.0).profile
        assert profile.centre_0.mean == 0
        assert profile.centre_1.mean == 1
        assert profile.centre_0.sigma == 2.0
        assert profile.centre_1.sigma == 2.0

    def test_model_relative(self, result):
        profile = result.model_relative(r=1.0).profile
        assert profile.centre_0.mean == 0
        assert profile.centre_1.mean == 1
        assert profile.centre_0.sigma == 0.0
        assert profile.centre_1.sigma == 1.0

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
        optimizer = af.MockNLO(af.Paths("phase_name", tag="tag"))
        copy = optimizer.copy_with_name_extension("one")

        self.assert_non_linear_attributes_equal(copy)
        assert optimizer.paths.tag == copy.paths.tag


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


class TestDirectorySetup:
    def test__1_class__correct_directory(self, nlo_setup_path):
        conf.instance.output_path = nlo_setup_path + "1_class"
        af.MockNLO(af.Paths(name=""))

        assert os.path.exists(nlo_setup_path + "1_class")


class TestLabels:
    def test_param_names(self):
        model = af.PriorModel(MockClassNLOx4)
        assert [
                   "one",
                   "two",
                   "three",
                   "four",
               ] == model.parameter_names

    def test_label_config(self):
        assert conf.instance.label.label("one") == "x4p0"
        assert conf.instance.label.label("two") == "x4p1"
        assert conf.instance.label.label("three") == "x4p2"
        assert conf.instance.label.label("four") == "x4p3"