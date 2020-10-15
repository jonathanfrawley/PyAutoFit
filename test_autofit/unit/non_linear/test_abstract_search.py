import os
import pickle
import shutil

import numpy as np
import pytest

import autofit as af
from autoconf import conf
from autofit.non_linear.mock.mock_search import MockSamples
from autofit import mock

directory = os.path.dirname(os.path.realpath(__file__))
pytestmark = pytest.mark.filterwarnings("ignore::FutureWarning")


@pytest.fixture(autouse=True)
def set_config_path():
    conf.instance = conf.Config(
        os.path.join(directory, "files/nlo/config"),
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
        samples=MockSamples(gaussian_tuples=[(0, 0), (1, 0)]), previous_model=mapper, search=mock.MockSearch()
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
        assert copy.paths.name == "name/one"

    def test_copy_with_name_extension(self):
        search = af.MockSearch(af.Paths("name", tag="tag"))
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
        assert ["one", "two", "three", "four"] == model.model_component_and_parameter_names

    def test_label_config(self):
        assert conf.instance["notation"]["label"]["label"]["one"] == "one_label"
        assert conf.instance["notation"]["label"]["label"]["two"] == "two_label"
        assert conf.instance["notation"]["label"]["label"]["three"] == "three_label"
        assert conf.instance["notation"]["label"]["label"]["four"] == "four_label"


test_path = "{}/files/phase".format(os.path.dirname(os.path.realpath(__file__)))


class TestMovePickleFiles:

    def test__move_pickle_files(self):

        output_path = "{}/files/nlo/output/test_phase/mock/pickles".format(os.path.dirname(os.path.realpath(__file__)))

        if os.path.exists(output_path):
            shutil.rmtree(output_path)

        search = af.MockSearch(paths=af.Paths(name="test_phase", ))

        pickle_paths = ["{}/files/pickles".format(os.path.dirname(os.path.realpath(__file__)))]

        arr = np.ones((3, 3))

        with open(f"{pickle_paths[0]}/test.pickle", "wb") as f:
            pickle.dump(arr, f)

        pickle_paths = ["{}/files/pickles/test.pickle".format(os.path.dirname(os.path.realpath(__file__)))]

        search.move_pickle_files(pickle_files=pickle_paths)

        with open(f"{output_path}/test.pickle", "rb") as f:
            arr_load = pickle.load(f)

        assert (arr == arr_load).all()

        if os.path.exists(test_path):
            shutil.rmtree(test_path)
