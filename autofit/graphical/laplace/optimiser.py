from typing import Optional, Dict, Tuple, Any, Union

from autofit.mapper.variable_operator import VariableData
from autofit.graphical.factor_graphs.factor import Factor
from autofit.graphical.mean_field import MeanField, FactorApproximation
from autofit.graphical.utils import Status, StatusFlag
from autofit.graphical.expectation_propagation.ep_mean_field import EPMeanField
from autofit.graphical.expectation_propagation.optimiser import AbstractFactorOptimiser
from autofit.graphical.laplace import newton

FactorApprox = Union[EPMeanField, FactorApproximation, Factor]


def make_posdef_hessian(mean_field, variables):
    return MeanField.precision(mean_field, variables)


class LaplaceOptimiser(AbstractFactorOptimiser):
    def __init__(
        self,
        make_hessian=make_posdef_hessian,
        search_direction=newton.newton_direction,
        calc_line_search=newton.line_search,
        quasi_newton_update=newton.full_diag_update,
        stop_conditions=newton.stop_conditions,
        make_det_hessian=None,
        max_iter: int = 100,
        n_refine: int = 1,
        hessian_kws: Optional[Dict[str, Any]] = None,
        det_hessian_kws: Optional[Dict[str, Any]] = None,
        search_direction_kws: Optional[Dict[str, Any]] = None,
        line_search_kws: Optional[Dict[str, Any]] = None,
        quasi_newton_kws: Optional[Dict[str, Any]] = None,
        stop_kws: Optional[Dict[str, Any]] = None,
        deltas: Optional[Dict[str, int]] = None,
    ):
        super().__init__(deltas=deltas)

        self.make_hessian = make_hessian
        self.make_det_hessian = make_det_hessian or make_hessian
        self.search_direction = search_direction
        self.calc_line_search = calc_line_search
        self.quasi_newton_update = quasi_newton_update
        self.stop_conditions = stop_conditions

        self.max_iter = max_iter
        self.n_refine = n_refine

        self.hessian_kws = hessian_kws or {}
        self.det_hessian_kws = det_hessian_kws or hessian_kws or {}
        self.search_direction_kws = search_direction_kws or {}
        self.line_search_kws = line_search_kws or {}
        self.quasi_newton_kws = quasi_newton_kws or {}
        self.stop_kws = stop_kws or {}

    @property
    def default_kws(self):
        return dict(
            max_iter=self.max_iter,
            n_refine=self.n_refine,
            search_direction=self.search_direction,
            calc_line_search=self.calc_line_search,
            quasi_newton_update=self.quasi_newton_update,
            stop_conditions=self.stop_conditions,
            search_direction_kws=self.search_direction_kws,
            line_search_kws=self.line_search_kws,
            quasi_newton_kws=self.quasi_newton_kws,
            stop_kws=self.stop_kws,
        )

    def prepare_state(
        self,
        factor_approx: FactorApprox,
        mean_field: MeanField = None,
        params: VariableData = None,
    ) -> newton.OptimisationState:
        mean_field = mean_field or factor_approx.model_dist

        free_variables = factor_approx.free_variables
        det_variables = factor_approx.deterministic_variables

        parameters = (params or MeanField.mean.fget(mean_field)).subset(free_variables)
        hessian = self.make_hessian(mean_field, free_variables, **self.hessian_kws)
        if det_variables:
            det_hessian = self.make_hessian(mean_field, det_variables)
        else:
            det_hessian = None

        state = newton.OptimisationState(
            factor_approx,
            factor_approx.func_gradient,
            parameters,
            hessian,
            det_hessian,
        )

        return state

    def optimise_state(
        self,
        state: newton.OptimisationState,
        old_state: Optional[newton.OptimisationState] = None,
        **kwargs
    ) -> Tuple[bool, newton.OptimisationState, str]:
        kws = {**self.default_kws, **kwargs}
        return newton.optimise_quasi_newton(state, old_state, **kws)

    def optimise_approx(
        self,
        factor_approx: FactorApprox,
        mean_field: MeanField = None,
        params: VariableData = None,
        **kwargs
    ) -> Tuple[MeanField, Status]:

        mean_field = mean_field or factor_approx.model_dist
        state = self.prepare_state(factor_approx, mean_field, params)
        next_state, status = self.optimise_state(state, **kwargs)
        if status.flag != StatusFlag.SUCCESS:
            next_state = self.refine(
                state, mean_field.sample, n_refine=kwargs.get("n_refine")
            )

        projection = mean_field.from_opt_state(next_state)
        return projection, status

    def refine(self, state, new_param, n_refine=None):
        next_state = state
        for i in range(n_refine or self.n_refine):
            new_state = state.update(parameters=new_param())
            next_state = self.quasi_newton_update(
                next_state, new_state, **self.quasi_newton_kws
            )

        return next_state

    def optimise(
        self,
        factor: Factor,
        model_approx: EPMeanField,
        status: Optional[Status] = Status(),
        **kwargs
    ) -> Tuple[EPMeanField, Status]:

        factor_approx = model_approx.factor_approximation(factor)
        new_model_dist, status = self.optimise_approx(factor_approx, **kwargs)
        return self.update_model_approx(
            new_model_dist, factor_approx, model_approx, status
        )
