import copy
import os

from autofit import conf
from autofit import exc
from autofit.mapper.prior_model import AbstractPriorModel, CollectionPriorModel
from autofit.mapper.model import AbstractModel, ModelInstance
from autofit.mapper.prior import GaussianPrior, cast_collection, PriorNameValue, \
    ConstantNameValue, Prior
from autofit.mapper.prior_model.util import PriorModelNameValue

path = os.path.dirname(os.path.realpath(__file__))


class ModelMapper(AbstractModel):
    """A mapper of priors formed by passing in classes to be reconstructed
        @DynamicAttrs
    """

    def __init__(self, **classes):
        """
        Examples
        --------
        # The ModelMapper converts a set of classes whose input attributes may be
        # modeled using a non-linear search, to parameters with priors attached.

        # A config is passed into the model mapper to provide default setup values for
        the priors:

        mapper = ModelMapper(config)

        # All class instances that are to be generated by the model mapper are
        specified by adding classes to it:
        
        mapper = ModelMapper()

        mapper.sersic = light_profiles.AbstractEllipticalSersic
        mapper.gaussian = light_profiles.EllipticalGaussian
        mapper.any_class = SomeClass

        # A PriorModel instance is created each time we add a class to the mapper. We
        can access those models using # the mapper attributes:

        sersic_model = mapper.sersic

        # This allows us to replace the default priors:

        mapper.sersic.intensity = GaussianPrior(mean=2., sigma=5.)

        # Or maybe we want to tie two priors together:

        mapper.sersic.phi = mapper.other_sersic.phi

        # This statement reduces the number of priors by one and means that the two
        sersic instances will always share # the same rotation angle phi.

        # We can then create instances of every class for a unit hypercube vector
        with length equal to # len(mapper.priors):

        model_instance = mapper.model_instance_for_vector([.4, .2, .3, .1])

        # The attributes of the model_instance are named the same as those of the
        mapper:

        sersic_1 = mapper.sersic_1

        # But this attribute is an instance of the actual AbstractEllipticalSersic:P
        class

        # A ModelMapper can be concisely constructed using keyword arguments:

        mapper = prior.ModelMapper(
            source_light_profile=light_profile.AbstractEllipticalSersic,
            lens_mass_profile=mass_profile.EllipticalCoredIsothermal,
            lens_light_profile=light_profile.EllipticalCoreSersic
        )
        """
        super(ModelMapper, self).__init__()

        for name, cls in classes.items():
            self.__setattr__(name, cls)

    def __setattr__(self, key, value):
        super(ModelMapper, self).__setattr__(key, AbstractPriorModel.from_object(value))

    @property
    def prior_count(self):
        return len(self.prior_tuples_ordered_by_id)

    @property
    def constant_count(self):
        return len(self.constant_tuples)

    @property
    @cast_collection(PriorModelNameValue)
    def prior_model_tuples(self):
        """
        Returns
        -------
        prior_model_tuples: [(String, PriorModel)]
        """
        return list(filter(lambda t: isinstance(t[1], AbstractPriorModel),
                           self.__dict__.items()))

    @property
    @cast_collection(PriorModelNameValue)
    def list_prior_model_tuples(self):
        """
        Returns
        -------
        list_prior_model_tuples: [(String, ListPriorModel)]
        """
        return list(filter(lambda t: isinstance(t[1], CollectionPriorModel),
                           self.__dict__.items()))

    @property
    @cast_collection(PriorModelNameValue)
    def flat_prior_model_tuples(self):
        """
        Returns
        -------
        prior_model_tuples: [(String, PriorModel)]
            A list of tuples with the names of prior models and associated prior models.
            Names are fully qualified by all objects in which they are embedded.
        """
        return [
            ("{}".format(prior_model_name), flat_prior_model) for
            prior_model_name, prior_model in
            self.prior_model_tuples for
            flat_prior_model_name, flat_prior_model in
            prior_model.flat_prior_model_tuples
        ]

    @property
    @cast_collection(PriorNameValue)
    def prior_tuples(self):
        """
        Returns
        -------
        prior_tuple_dict: [(Prior, PriorTuple)]
            The set of all priors associated with this mapper
        """
        return {
            prior_tuple.prior: prior_tuple
            for name, prior_model in self.prior_model_tuples
            for prior_tuple in prior_model.prior_tuples
        }.values()

    @property
    def priors(self):
        return [prior_tuple.prior for prior_tuple in self.prior_tuples]

    @property
    def prior_prior_name_dict(self):
        return {
            prior_tuple.prior: prior_tuple.name
            for prior_tuple in self.prior_tuples
        }

    @property
    @cast_collection(ConstantNameValue)
    def constant_tuples(self):
        """
        Returns
        -------
        constant_tuples: [(str, float)]
            The set of all constants associated with this mapper
        """
        return {
            constant_tuple.constant: constant_tuple
            for name, prior_model in self.prior_model_tuples
            for constant_tuple in prior_model.constant_tuples
        }.values()

    @property
    @cast_collection(PriorNameValue)
    def prior_tuples_ordered_by_id(self):
        """
        Returns
        -------
        priors: [Prior]
            An ordered list of unique priors associated with this mapper
        """
        return sorted(list(self.prior_tuples),
                      key=lambda prior_tuple: prior_tuple.prior.id)

    @property
    def prior_class_dict(self):
        """
        Returns
        -------
        prior_class_dict: {Prior: class}
            A dictionary mapping Priors to associated classes. Each prior will only have
            one class; if a prior is shared by two classes then only one of those
            classes will be in this dictionary.
        """
        return {prior: cls
                for prior_model_tuple in self.prior_model_tuples
                for prior, cls in
                prior_model_tuple.prior_model.prior_class_dict.items()}

    @property
    def prior_prior_model_dict(self):
        """
        Returns
        -------
        prior_prior_model_dict: {Prior: PriorModel}
            A dictionary mapping priors to associated prior models. Each prior will only
            have one prior model; if a prior is shared by two prior models then one of
            those prior models will be in this dictionary.
        """
        return {prior: prior_model[1] for prior_model in self.prior_model_tuples for
                _, prior in
                prior_model[1].prior_tuples}

    @property
    def prior_prior_model_name_dict(self):
        """
        Returns
        -------
        prior_prior_model_name_dict: {Prior: str}
            A dictionary mapping priors to the names of associated prior models. Each
            prior will only have one prior model name; if a prior is shared by two prior
            models then one of those prior model's names will be in this dictionary.
        """
        prior_prior_model_name_dict = {prior_tuple.prior: prior_model_tuple.name
                                       for prior_model_tuple in
                                       self.flat_prior_model_tuples
                                       for prior_tuple in
                                       prior_model_tuple.prior_model.prior_tuples}
        prior_list_prior_model_name_dict = {
            prior_tuple.value: "{}_{}".format(list_prior_model_tuple.name,
                                              label_prior_model_tuple.name) for
            list_prior_model_tuple in self.list_prior_model_tuples for
            label_prior_model_tuple in
            list_prior_model_tuple.value.label_prior_model_tuples for prior_tuple in
            label_prior_model_tuple.value.prior_tuples}
        prior_prior_model_name_dict.update(prior_list_prior_model_name_dict)
        return prior_prior_model_name_dict

    @property
    @cast_collection(PriorModelNameValue)
    def list_prior_model_tuples(self):
        return [tup for tup in self.prior_model_tuples if
                isinstance(tup.value, CollectionPriorModel)]

    @property
    def constant_prior_model_name_dict(self):
        """
        Returns
        -------
        prior_prior_model_name_dict: {Prior: str}
            A dictionary mapping priors to the names of associated prior models. Each
            prior will only have one prior model name; if a prior is shared by two prior
            models then one of those prior model's names will be in this dictionary.
        """
        return {constant_tuple.constant: prior_model_tuple.name
                for prior_model_tuple in self.prior_model_tuples
                for constant_tuple in prior_model_tuple.prior_model.constant_tuples}

    @property
    def prior_model_name_prior_tuples_dict(self):
        """
        Returns
        -------
        class_priors_dict: {String: [Prior]}
            A dictionary mapping_matrix the names of priors to lists of associated
            priors
        """
        return {name: list(prior_model.prior_tuples) for name, prior_model in
                self.prior_model_tuples}

    @property
    def prior_model_name_constant_tuples_dict(self):
        """
        Returns
        -------
        class_constants_dict: {String: [Constant]}
            A dictionary mapping_matrix the names of priors to lists of associated
            constants
        """
        return {name: list(prior_model.constant_tuples) for name, prior_model in
                self.prior_model_tuples}

    def physical_vector_from_hypercube_vector(self, hypercube_vector):
        """
        Parameters
        ----------
        hypercube_vector: [float]
            A unit hypercube vector

        Returns
        -------
        values: [float]
            A vector with values output by priors
        """
        return list(
            map(lambda prior_tuple, unit: prior_tuple.prior.value_for(unit),
                self.prior_tuples_ordered_by_id,
                hypercube_vector))

    def physical_values_ordered_by_class(self, hypercube_vector):
        """
        Parameters
        ----------
        hypercube_vector: [float]
            A unit vector

        Returns
        -------
        physical_values: [float]
            A list of physical values constructed by passing the values in the hypercube
            vector through associated priors.
        """
        model_instance = self.instance_from_unit_vector(hypercube_vector)
        result = []
        for instance_key in sorted(model_instance.__dict__.keys()):
            instance = model_instance.__dict__[instance_key]
            try:
                for attribute_key in sorted(instance.__dict__.keys()):

                    value = instance.__dict__[attribute_key]

                    if isinstance(value, tuple):
                        result.extend(list(value))
                    else:
                        result.append(value)
            except AttributeError:
                pass
        return result

    @property
    def physical_values_from_prior_medians(self):
        """
        Returns
        -------
        physical_values: [float]
            A list of physical values constructed by taking the mean possible value from
            each prior.
        """
        return self.physical_vector_from_hypercube_vector(
            [0.5] * len(self.prior_tuples))

    def instance_from_prior_medians(self):
        """
        Creates a list of physical values from the median values of the priors.

        Returns
        -------
        physical_values : [float]
            A list of physical values

        """
        return self.instance_from_unit_vector(
            unit_vector=[0.5] * len(self.prior_tuples))

    def instance_from_unit_vector(self, unit_vector):
        """
        Creates a ModelInstance, which has an attribute and class instance corresponding
        to every PriorModel attributed to this instance.

        This method takes as input a unit vector of parameter values, converting each to
        physical values via their priors.

        Parameters
        ----------
        unit_vector: [float]
            A vector of physical parameter values.

        Returns
        -------
        model_instance : autofit.mapper.model.ModelInstance
            An object containing reconstructed model_mapper instances

        """
        arguments = dict(
            map(
                lambda prior_tuple, unit: (
                    prior_tuple.prior,
                    prior_tuple.prior.value_for(unit)
                ),
                self.prior_tuples_ordered_by_id,
                unit_vector
            )
        )

        return self.instance_for_arguments(arguments)

    def instance_from_physical_vector(self, physical_vector):
        """
        Creates a ModelInstance, which has an attribute and class instance corresponding
        to every PriorModel attributed to this instance.

        This method takes as input a physical vector of parameter values, thus omitting
        the use of priors.

        Parameters
        ----------
        physical_vector: [float]
            A unit hypercube vector

        Returns
        -------
        model_instance : autofit.mapper.model.ModelInstance
            An object containing reconstructed model_mapper instances

        """
        arguments = dict(
            map(
                lambda prior_tuple, physical_unit: (prior_tuple.prior, physical_unit),
                self.prior_tuples_ordered_by_id,
                physical_vector)
        )

        return self.instance_for_arguments(arguments)

    @property
    def instance_tuples(self):
        return [
            (key, value) for key, value in self.__dict__.items() if
            isinstance(value, object)
            and not isinstance(value, AbstractPriorModel)
            and not key == "id"
        ]

    def instance_for_arguments(self, arguments):
        """
        Creates a ModelInstance, which has an attribute and class instance corresponding
        to every PriorModel attributed to this instance.

        Parameters
        ----------
        arguments : dict
            The dictionary representation of prior and parameter values. This is created
            in the model_instance_from_* routines.

        Returns
        -------
        model_instance : autofit.mapper.model.ModelInstance
            An object containing reconstructed model_mapper instances

        """

        model_instance = ModelInstance()

        for prior_model_tuple in self.prior_model_tuples:
            setattr(model_instance, prior_model_tuple.name,
                    prior_model_tuple.prior_model.instance_for_arguments(arguments))

        for name, value in self.instance_tuples:
            setattr(model_instance, name, value)

        return model_instance

    def mapper_from_partial_prior_arguments(self, arguments):
        """
        Creates a new model mapper from a dictionary mapping_matrix existing priors to
        new priors, keeping existing priors where no mapping is provided.

        Parameters
        ----------
        arguments: {Prior: Prior}
            A dictionary mapping_matrix priors to priors

        Returns
        -------
        model_mapper: ModelMapper
            A new model mapper with updated priors.
        """
        original_prior_dict = {prior: prior for prior in self.priors}
        return self.mapper_from_prior_arguments({**original_prior_dict, **arguments})

    def mapper_from_prior_arguments(self, arguments):
        """
        Creates a new model mapper from a dictionary mapping_matrix existing priors to
        new priors.

        Parameters
        ----------
        arguments: {Prior: Prior}
            A dictionary mapping_matrix priors to priors

        Returns
        -------
        model_mapper: ModelMapper
            A new model mapper with updated priors.
        """
        mapper = copy.deepcopy(self)

        for prior_model_tuple in self.prior_model_tuples:
            setattr(mapper, prior_model_tuple.name,
                    prior_model_tuple.prior_model.gaussian_prior_model_for_arguments(
                        arguments))

        return mapper

    def mapper_from_gaussian_tuples(self, tuples, a=None, r=None):
        """
        Creates a new model mapper from a list of floats describing the mean values
        of gaussian priors. The widths of the new priors are taken from the
        width_config. The new gaussian priors must be provided in the same order as
        the priors associated with model.

        If a is not None then all priors are created with an absolute width of a.

        If r is not None then all priors are created with a relative width of r.

        Parameters
        ----------
        r
            The relative width to be assigned to gaussian priors
        a
            The absolute width to be assigned to gaussian priors
        tuples
            A list of tuples each containing the mean and width of a prior

        Returns
        -------
        mapper: ModelMapper
            A new model mapper with all priors replaced by gaussian priors.
        """

        prior_tuples = self.prior_tuples_ordered_by_id
        prior_class_dict = self.prior_class_dict
        arguments = {}

        for i, prior_tuple in enumerate(prior_tuples):
            prior = prior_tuple.prior
            cls = prior_class_dict[prior]
            mean = tuples[i][0]
            if a is not None and r is not None:
                raise exc.PriorException(
                    "Width of new priors cannot be both relative and absolute.")
            if a is not None:
                width_type = "a"
                value = a
            elif r is not None:
                width_type = "r"
                value = r
            else:
                width_type, value = conf.instance.prior_width.get_for_nearest_ancestor(
                    cls, prior_tuple.name)
            if width_type == "r":
                width = value * mean
            elif width_type == "a":
                width = value
            else:
                raise exc.PriorException(
                    "Prior widths must be relative 'r' or absolute 'a' e.g. a, 1.0")
            if isinstance(prior, GaussianPrior):
                limits = (prior.lower_limit, prior.upper_limit)
            else:
                limits = conf.instance.prior_limit.get_for_nearest_ancestor(
                    cls,
                    prior_tuple.name
                )
            arguments[prior] = GaussianPrior(mean, max(tuples[i][1], width), *limits)

        return self.mapper_from_prior_arguments(arguments)

    def mapper_from_gaussian_means(self, means):
        """
        Creates a new model mapper from a list of floats describing the mean values \
        of gaussian priors. The widths of the new priors are taken from the \
        width_config. The new gaussian priors must be provided in the same order as \
        the priors associated with model.

        Parameters
        ----------
        means: [float]
            A list containing the means of the gaussian priors.

        Returns
        -------
        mapper: ModelMapper
            A new model mapper with all priors replaced by gaussian priors.
        """
        return self.mapper_from_gaussian_tuples([(mean, 0) for mean in means])

    @property
    def info(self):
        """
        Use the priors that make up the model_mapper to generate information on each
        parameter of the overall model.

        This information is extracted from each priors *model_info* property.
        """

        path_priors_tuples = self.path_instance_tuples_for_class(
            Prior
        )

        path_priors_tuples = [(t[0][:-1], t[1])
                              if t[0][-1] == "value"
                              else t
                              for t in path_priors_tuples]

        path_float_tuples = self.path_instance_tuples_for_class(
            float,
            ignore_class=Prior
        )

        info_dict = dict()

        for t in path_priors_tuples + path_float_tuples:
            add_to_info_dict(t, info_dict)

        return '\n'.join(
            info_dict_to_list(
                info_dict,
                line_length=100,
                indent=4
            )
        )

    def name_for_prior(self, prior):
        for prior_model_name, prior_model in self.prior_model_tuples:
            prior_name = prior_model.name_for_prior(prior)
            if prior_name is not None:
                return "{}_{}".format(prior_model_name, prior_name)

    @property
    def param_names(self):
        """The param_names vector is a list each parameter's analysis_path, and is used
        for *GetDist* visualization.

        The parameter names are determined from the class instance names of the
        model_mapper. Latex tags are properties of each model class."""

        return [self.name_for_prior(prior) for prior in
                sorted(self.priors, key=lambda prior: prior.id)]

    @property
    def constant_names(self):
        constant_names = []

        constant_prior_model_name_dict = self.constant_prior_model_name_dict

        for constant_name, constant in self.constant_tuples:
            constant_names.append(
                constant_prior_model_name_dict[constant] + '_' + constant_name)

        return constant_names

    def __eq__(self, other):
        return isinstance(other, ModelMapper) \
               and self.priors == other.priors \
               and self.prior_model_tuples == other.prior_model_tuples


def add_to_info_dict(path_item_tuple, info_dict):
    path_tuple = path_item_tuple[0]
    key = path_tuple[0]
    if len(path_tuple) == 1:
        info_dict[key] = path_item_tuple[1]
    else:
        if key not in info_dict:
            info_dict[key] = dict()
        add_to_info_dict(
            (path_item_tuple[0][1:], path_item_tuple[1]),
            info_dict=info_dict[key]
        )


def info_dict_to_list(
        info_dict,
        line_length=130,
        indent=4
):
    lines = []
    for key, value in info_dict.items():
        indent_string = indent * " "
        if isinstance(value, dict):
            sub_lines = info_dict_to_list(
                value,
                line_length=line_length - indent,
                indent=indent
            )
            lines.append(key)
            for line in sub_lines:
                lines.append(f"{indent_string}{line}")
        else:
            value_string = str(value)
            space_string = max((line_length - len(value_string) - len(key)),
                               1) * " "
            lines.append(
                f"{key}{space_string}{value_string}"
            )
    return lines
