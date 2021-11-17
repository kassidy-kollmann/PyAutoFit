import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Dict, Tuple, Optional, List
)

import matplotlib.pyplot as plt

from autofit import conf
from autofit.graphical.factor_graphs import (
    Factor, FactorGraph
)
from autofit.graphical.utils import Status
from .ep_mean_field import EPMeanField
from .history import EPHistory, EPCallBack, FactorHistory
from ...tools.util import IntervalCounter

logger = logging.getLogger(
    __name__
)


class AbstractFactorOptimiser(ABC):
    @abstractmethod
    def optimise(
            self,
            factor: Factor,
            model_approx: EPMeanField,
            name: str = None,
            status: Status = Status()
    ) -> Tuple[EPMeanField, Status]:
        pass


class EPOptimiser:
    def __init__(
            self,
            factor_graph: FactorGraph,
            name="ep_optimiser",
            default_optimiser: Optional[AbstractFactorOptimiser] = None,
            factor_optimisers: Optional[Dict[Factor, AbstractFactorOptimiser]] = None,
            ep_history: Optional[EPHistory] = None,
            factor_order: Optional[List[Factor]] = None,
            log_interval=10,
            visualise_interval=10
    ):
        factor_optimisers = factor_optimisers or {}
        self.factor_graph = factor_graph
        self.factors = factor_order or self.factor_graph.factors

        self.should_log = IntervalCounter(
            log_interval
        )
        self.should_visualise = IntervalCounter(
            visualise_interval
        )

        if default_optimiser is None:
            self.factor_optimisers = factor_optimisers
            missing = set(self.factors) - self.factor_optimisers.keys()
            if missing:
                raise (ValueError(
                    f"missing optimisers for {missing}, "
                    "pass a default_optimiser or add missing optimsers"
                ))
        else:
            self.factor_optimisers = {
                factor: factor_optimisers.get(
                    factor,
                    default_optimiser
                )
                for factor in self.factors
            }

        self.ep_history = ep_history or EPHistory()
        self.name = name

        with open(self.output_path / "graph.info", "w+") as f:
            f.write(self.factor_graph.info)

    @property
    def output_path(self):
        path = Path(conf.instance.output_path) / self.name
        os.makedirs(path, exist_ok=True)
        return path

    def _log_factor(self, factor):
        factor_history = self.ep_history[factor]
        log_evidence = factor_history.latest_successful.log_evidence
        divergence = factor_history.kl_divergence()

        factor_logger = logging.getLogger(
            factor.name
        )
        factor_logger.info(
            f"Log Evidence = {log_evidence}"
        )
        factor_logger.info(
            f"KL Divergence = {divergence}"
        )

    def _visualise_factor(self, factor):
        factor_history = self.ep_history[factor]
        fig, (evidence_plot, kl_plot) = plt.subplots(2)
        fig.suptitle('Evidence and KL Divergence')
        evidence_plot.plot(
            factor_history.evidences,
            label=f"{factor.name} evidence"
        )
        kl_plot.plot(
            factor_history.kl_divergences,
            label=f"{factor.name} divergence"
        )
        evidence_plot.legend()
        kl_plot.legend()

    def run(
            self,
            model_approx: EPMeanField,
            max_steps=100,
    ) -> EPMeanField:
        for _ in range(max_steps):
            should_log = self.should_log()
            should_visualise = self.should_visualise()

            for factor, optimiser in self.factor_optimisers.items():
                factor_logger = logging.getLogger(
                    factor.name
                )
                factor_logger.debug("Optimising...")
                try:
                    model_approx, status = optimiser.optimise(
                        factor,
                        model_approx,
                        name=self.name
                    )
                except (ValueError, ArithmeticError, RuntimeError) as e:
                    logger.exception(e)
                    status = Status(
                        False,
                        (f"Factor: {factor} experienced error {e}",)
                    )

                factor_logger.debug(status)

                if self.ep_history(factor, model_approx, status):
                    logger.info("Terminating optimisation")
                    break  # callback controls convergence

                if status:
                    if should_log:
                        self._log_factor(factor)
                    if should_visualise:
                        self._visualise_factor(factor)

            else:  # If no break do next iteration
                if should_visualise:
                    plt.savefig(
                        str(self.output_path / "graph.png")
                    )
                continue
            break  # stop iterations

        return model_approx
