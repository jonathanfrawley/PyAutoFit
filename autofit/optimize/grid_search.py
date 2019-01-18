from autofit.mapper.prior import UniformPrior
from autofit.optimize import non_linear
from autofit.optimize import optimizer


class GridSearch(object):
    def __init__(self, step_size=0.1, optimizer_class=non_linear.DownhillSimplex, model_mapper=None,
                 name="grid_search"):
        self.variable = model_mapper
        self.name = name
        self.step_size = step_size
        self.optimizer_class = optimizer_class

    def make_lists(self, grid_priors):
        return optimizer.make_lists(len(grid_priors), step_size=self.step_size, include_upper_limit=False)

    def models_mappers(self, grid_priors):
        grid_priors = set(grid_priors)
        lists = self.make_lists(grid_priors)
        for values in lists:
            priors = [UniformPrior(lower_limit=value, upper_limit=value + self.step_size) for value in values]
            arguments = {source_prior: prior for source_prior, prior in zip(grid_priors, priors)}
            yield self.variable.mapper_from_partial_prior_arguments(arguments)

    def fit(self, analysis, grid_priors):
        results = []
        lists = self.make_lists(grid_priors)
        for values, model_mapper in zip(lists, self.models_mappers(grid_priors)):
            result = self.optimizer_class(model_mapper, "{}/{}".format(self.name, "_".join(map(str, values)))).fit(
                analysis)
            results.append(result)
        return results
