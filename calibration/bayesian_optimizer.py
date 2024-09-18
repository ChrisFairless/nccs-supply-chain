# NCCS calibration module

# Replacing a couple of classes from CLIMADA's calibration module with ones designed for our own modelling pipeline
# The module has the same name as the ones it is replacing, and the classes have the same names with 'NCCS' prepended.

from dataclasses import dataclass
from calibration.base import NCCSOptimizer
from climada.util.calibrate import BayesianOptimizerOutput, BayesianOptimizer, BayesianOptimizerController

class NCCSBayesianOptimizerOutput(BayesianOptimizerOutput):
    pass


class NCCSBayesianOptimizerController(BayesianOptimizerController):
    pass


@dataclass
class NCCSBayesianOptimizer(NCCSOptimizer, BayesianOptimizer):
    # Mutliple inheritance here: we want the custom methods we defined in 
    # `NCCSOptimizer`, falling back on the methods defined in CLIMADA's
    # `BayesianOptimizer`
    def run(self, controller: NCCSBayesianOptimizerController) -> NCCSBayesianOptimizerOutput:
        output = BayesianOptimizer.run(self, controller)
        return NCCSBayesianOptimizerOutput(p_space = output.p_space)


class NCCSBayesianOptimizerOutputEvaluator():
    # TODO this doesn't work with the current outputs. If we need it we could adapt it.
    pass
