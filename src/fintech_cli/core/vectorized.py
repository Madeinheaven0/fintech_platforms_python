from math import sqrt
from decimal import Decimal
import numpy as np
from numpy.typing import NDArray
from numpy.random import default_rng as rng


class MonteCarloBlackScholes:
    def __init__(self, S0: float, r: float, vol: float, T: float, step: int, paths: int, seed: int = None):
        self.S0 = float(S0)
        self.mean_return = float(r)  # ou r
        self.vol = float(vol)
        self.T = float(T)
        self.step = int(step)
        self.paths = int(paths)
        self.dt = self.T / self.step

        self.rng = np.random.default_rng(seed)
        self.price_table: NDArray[np.float64] = None
        self._price: Decimal = None

    def _initialization(self):
        self.price_table = np.zeros((self.step + 1, self.paths))
        self.price_table[0] = self.S0

    def compute_price(self) -> Decimal:
        self._initialization()
        z = self.rng.standard_normal((self.step, self.paths))

        drift = self.mean_return - (self.vol ** 2) / 2
        increments = drift * self.dt + self.vol * np.sqrt(self.dt) * z

        log_paths = np.vstack([
            np.log(self.price_table[0]),
            np.log(self.price_table[0]) + np.cumsum(increments, axis=0)
        ])

        self.price_table = np.exp(log_paths)

        self._price = Decimal(str(self.price_table[-1].mean()))
        return self._price

    @property
    def price(self) -> Decimal:
        if self._price is None:
            self.calculate_price()
            return self._price
        return self._price


class CovarianceMatrix:
    @staticmethod
    def compute_covariance_table(multi_assets_table: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.cov(multi_assets_table, rowvar=False)


class MonteCarloHeston:
    def __init__(self, S0: float, r: float, v0: float, kappa: float, theta: float, xi: float, rho: float, T: float,
                 step: int, paths: int, seed: int = None):
        self.S0 = S0
        self.r = r
        self.v0 = v0
        self.kappa = kappa
        self.theta = theta
        self.xi = xi
        self.rho = rho
        self.T = T
        self.step = step
        self.paths = paths
        self.dt = T / step

        self.rng = np.random.default_rng(seed)
        self.rng_var = np.random.default_rng(seed + 1 if seed is not None else None)

        self.price_table: NDArray[np.float64] = None
        self.variance_table: NDArray[np.float64] = None
        self._price: Decimal = None

    def _initialization(self):
        self.price_table = np.zeros((self.step + 1, self.paths))
        self.variance_table = np.zeros((self.step + 1, self.paths))

        self.price_table[0] = self.S0
        self.variance_table[0] = self.v0

    def _compute_var_table(self):
        dt = self.dt
        kappa = self.kappa
        theta = self.theta
        xi = self.xi
        z_var = self.rng_var.standard_normal((self.step, self.paths))

        for i in range(1, self.step + 1):
            non_neg_variance = np.maximum(self.variance_table[i - 1], 0)
            self.variance_table[i] = (
                    non_neg_variance
                    + kappa * (theta - non_neg_variance) * dt
                    + xi * np.sqrt(non_neg_variance) * z_var[i - 1] * np.sqrt(dt)
            )
        return z_var

    def compute_price(self) -> Decimal:
        self._initialization()
        dt = self.dt
        rho = self.rho

        z_var = self._compute_var_table()
        z = self.rng.standard_normal((self.step, self.paths))

        # raw correlation fo cholesky
        z_price = rho * z_var + np.sqrt(1 - rho ** 2) * z

        variance = np.maximum(self.variance_table, 0)
        var_interval = variance[:-1]

        drift = (self.r - var_interval / 2) * dt
        increments = drift + np.sqrt(var_interval * dt) * z_price

        log_paths = np.vstack([
            np.log(self.price_table[0]),
            np.log(self.price_table[0]) + np.cumsum(increments, axis=0)
        ])

        self.price_table = np.exp(log_paths)
        self._price = Decimal(str(self.price_table[-1].mean()))
        return self._price