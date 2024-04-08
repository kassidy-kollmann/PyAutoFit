import logging
from abc import ABC
import os
from typing import Optional, Dict

from autoconf import conf

from autofit.mapper.prior_model.abstract import AbstractPriorModel
from autofit.non_linear.analysis.latent_variables import LatentVariables
from autofit.non_linear.paths.abstract import AbstractPaths
from autofit.non_linear.paths.database import DatabasePaths
from autofit.non_linear.paths.null import NullPaths
from autofit.non_linear.samples.summary import SamplesSummary
from autofit.non_linear.samples.pdf import SamplesPDF
from autofit.non_linear.result import Result
from autofit.non_linear.samples.samples import Samples
from .visualise import Visualiser

logger = logging.getLogger(__name__)


class Analysis(ABC):
    """
    Protocol for an analysis. Defines methods that can or
    must be implemented to define a class that compute the
    likelihood that some instance fits some data.
    """

    Result = Result
    Visualiser = Visualiser

    def compute_all_latent_variables(
        self, samples: Samples
    ) -> Optional[LatentVariables]:
        """
        Internal method that manages computation of latent variables from samples.

        Parameters
        ----------
        samples
            The samples from the non-linear search.

        Returns
        -------
        The computed latent variables or None if compute_latent_variable is not implemented.
        """
        try:
            latent_variables = LatentVariables()
            model = samples.model
            for sample in samples.sample_list:
                latent_variables.add(
                    **self.compute_latent_variable(sample.instance_for_model(model))
                )
            return latent_variables
        except NotImplementedError:
            return None

    def compute_latent_variable(self, instance) -> Dict[str, float]:
        """
        Override to compute latent variables from the instance.

        Parameters
        ----------
        instance
            An instance of the model.

        Returns
        -------
        The computed latent variables.
        """
        raise NotImplementedError()

    def with_model(self, model):
        """
        Associate an explicit model with this analysis. Instances of the model
        will be used to compute log likelihood in place of the model passed
        from the search.

        Parameters
        ----------
        model
            A model to associate with this analysis

        Returns
        -------
        An analysis for that model
        """
        from .model_analysis import ModelAnalysis

        return ModelAnalysis(analysis=self, model=model)

    def should_visualize(
        self, paths: AbstractPaths, during_analysis: bool = True
    ) -> bool:
        """
        Whether a visualize method should be called perform visualization, which depends on the following:

        1) If a model-fit has already completed, the default behaviour is for visualization to be bypassed in order
        to make model-fits run faster.

        2) If a model-fit has completed, but it is the final visualization output where `during_analysis` is False,
        it should be performed.

        3) Visualization can be forced to run via the `force_visualization_overwrite`, for example if a user
        wants to plot additional images that were not output on the original run.

        4) If the analysis is running a database session visualization is switched off.

        5) If PyAutoFit test mode is on visualization is disabled, irrespective of the `force_visualization_overwite`
        config input.

        Parameters
        ----------
        paths
            The PyAutoFit paths object which manages all paths, e.g. where the non-linear search outputs are stored,
            visualization and the pickled objects used by the aggregator output by this function.


        Returns
        -------
        A bool determining whether visualization should be performed or not.
        """

        if os.environ.get("PYAUTOFIT_TEST_MODE") == "1":
            return False

        if isinstance(paths, DatabasePaths) or isinstance(paths, NullPaths):
            return False

        if conf.instance["general"]["output"]["force_visualize_overwrite"]:
            return True

        if not during_analysis:
            return True

        return not paths.is_complete

    def log_likelihood_function(self, instance):
        raise NotImplementedError()

    def save_attributes(self, paths: AbstractPaths):
        pass

    def save_results(self, paths: AbstractPaths, result: Result):
        pass

    def save_results_combined(self, paths: AbstractPaths, result: Result):
        pass

    def modify_before_fit(self, paths: AbstractPaths, model: AbstractPriorModel):
        """
        Overwrite this method to modify the attributes of the `Analysis` class before the non-linear search begins.

        An example use-case is using properties of the model to alter the `Analysis` class in ways that can speed up
        the fitting performed in the `log_likelihood_function`.
        """
        return self

    def modify_model(self, model):
        return model

    def modify_after_fit(
        self, paths: AbstractPaths, model: AbstractPriorModel, result: Result
    ):
        """
        Overwrite this method to modify the attributes of the `Analysis` class before the non-linear search begins.

        An example use-case is using properties of the model to alter the `Analysis` class in ways that can speed up
        the fitting performed in the `log_likelihood_function`.
        """
        return self

    def make_result(
        self,
        samples_summary: SamplesSummary,
        paths: AbstractPaths,
        samples: Optional[SamplesPDF] = None,
        search_internal: Optional[object] = None,
        analysis: Optional[object] = None,
    ) -> Result:
        """
        Returns the `Result` of the non-linear search after it is completed.

        The result type is defined as a class variable in the `Analysis` class. It can be manually overwritten
        by a user to return a user-defined result object, which can be extended with additional methods and attributes
        specific to the model-fit.

        The standard `Result` object may include:

        - The samples summary, which contains the maximum log likelihood instance and median PDF model.

        - The paths of the search, which are used for loading the samples and search internal below when a search
        is resumed.

        - The samples of the non-linear search (e.g. MCMC chains) also stored in `samples.csv`.

        - The non-linear search used for the fit in its internal representation, which is used for resuming a search
        and making bespoke visualization using the search's internal results.

        - The analysis used to fit the model (default disabled to save memory, but option may be useful for certain
        projects).

        Parameters
        ----------
        samples_summary
            The summary of the samples of the non-linear search, which include the maximum log likelihood instance and
            median PDF model.
        paths
            An object describing the paths for saving data (e.g. hard-disk directories or entries in sqlite database).
        samples
            The samples of the non-linear search, for example the chains of an MCMC run.
        search_internal
            The internal representation of the non-linear search used to perform the model-fit.
        analysis
            The analysis used to fit the model.

        Returns
        -------
        Result
            The result of the non-linear search, which is defined as a class variable in the `Analysis` class.
        """
        return self.Result(
            samples_summary=samples_summary,
            paths=paths,
            samples=samples,
            search_internal=search_internal,
            analysis=None,
        )

    def profile_log_likelihood_function(self, paths: AbstractPaths, instance):
        """
        Overwrite this function for profiling of the log likelihood function to be performed every update of a
        non-linear search.

        This behaves analogously to overwriting the `visualize` function of the `Analysis` class, whereby the user
        fills in the project-specific behaviour of the profiling.

        Parameters
        ----------
        paths
            An object describing the paths for saving data (e.g. hard-disk directories or entries in sqlite database).
        instance
            The maximum likliehood instance of the model so far in the non-linear search.
        """
        pass

    def __add__(self, other: "Analysis"):
        """
        Analyses can be added together. The resultant
        log likelihood function returns the sum of the
        underlying log likelihood functions.

        Parameters
        ----------
        other
            Another analysis class

        Returns
        -------
        A class that computes log likelihood based on both analyses
        """
        from .combined import CombinedAnalysis

        if isinstance(other, CombinedAnalysis):
            return other + self
        return CombinedAnalysis(self, other)

    def __radd__(self, other):
        """
        Allows analysis to be used in sum
        """
        if other == 0:
            return self
        return self + other
