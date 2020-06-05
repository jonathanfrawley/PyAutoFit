import os

import pytest

import autofit as af
from test_autofit.mock import GeometryProfile, Galaxy


@pytest.fixture(name="results")
def make_results_collection():
    results = af.ResultsCollection()

    results.add("first phase", "one")
    results.add("second phase", "two")

    return results


class TestResultsCollection:
    def test_with_name(self, results):
        assert results.from_phase("first phase") == "one"
        assert results.from_phase("second phase") == "two"

    def test_with_index(self, results):
        assert results[0] == "one"
        assert results[1] == "two"
        assert results.first == "one"
        assert results.last == "two"
        assert len(results) == 2

    def test_missing_result(self, results):
        with pytest.raises(af.exc.PipelineException):
            results.from_phase("third phase")


class MockPhase(af.AbstractPhase):
    def make_result(self, result, analysis):
        pass

    @af.convert_paths
    def __init__(self, paths, optimizer=None):
        super().__init__(paths)
        self.optimizer = optimizer or af.MockNLO(paths=paths)

    def save_metadata(self, *args, **kwargs):
        pass


class TestPipeline:
    def test_unique_phases(self):
        af.Pipeline("name", MockPhase(af.Paths("one")), MockPhase(af.Paths("two")))
        with pytest.raises(af.exc.PipelineException):
            af.Pipeline("name", MockPhase(af.Paths("one")), MockPhase(af.Paths("one")))

    def test_optimizer_assertion(self, model):
        paths = af.Paths("Phase Name")
        optimizer = af.MockNLO(paths)
        phase = MockPhase(phase_name="Phase_Name", optimizer=optimizer)
        phase.model.profile = GeometryProfile

        try:
            os.makedirs(phase.paths.make_path())
        except FileExistsError:
            pass



        phase.model.profile.centre_0 = af.UniformPrior()

    def test_name_composition(self):
        first = af.Pipeline("first")
        second = af.Pipeline("second")

        assert (first + second).pipeline_name == "first + second"



# noinspection PyUnresolvedReferences
class TestPhasePipelineName:
    def test_name_stamping(self):
        one = MockPhase(af.Paths("one"))
        two = MockPhase(af.Paths("two"))
        af.Pipeline("name", one, two)

        assert one.pipeline_name == "name"
        assert two.pipeline_name == "name"

    def test_no_restamping(self):
        one = MockPhase(af.Paths("one"))
        two = MockPhase(af.Paths("two"))
        pipeline_one = af.Pipeline("one", one)
        pipeline_two = af.Pipeline("two", two)

        composed_pipeline = pipeline_one + pipeline_two

        assert composed_pipeline[0].pipeline_name == "one"
        assert composed_pipeline[1].pipeline_name == "two"

        assert one.pipeline_name == "one"
        assert two.pipeline_name == "two"
