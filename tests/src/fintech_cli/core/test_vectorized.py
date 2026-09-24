import pytest

from  src.fintech_cli.core.vectorized import MonteCarloHeston, MonteCarloBlackScholes, CovarianceMatrix

S0 = 100.0
r = 0.05
T = 1.0
step = 252
paths = 100000
seed = 42
v0 = 0.20 ** 2
kappa = 2.0
theta = 0.20 ** 2
xi = 0.3
rho = -0.7

def test_monte_carlo_black_scholes():
    vol_bs = 0.20
    bs_model = MonteCarloBlackScholes(S0=S0, r=r, T=T, step=step, paths=paths, vol=vol_bs)
    price_bs = bs_model.compute_price()
    assert float(price_bs) == pytest.approx(105.13, abs=0.2)

def test_monte_carlo_heston():
    heston_model = MonteCarloHeston(
        S0=S0, r=r, v0=v0, kappa=kappa, theta=theta,
        xi=xi, rho=rho, T=T, step=step, paths=paths, seed=seed
    )
    price = heston_model.compute_price()

    assert float(price) == pytest.approx(105.13, abs=0.5)