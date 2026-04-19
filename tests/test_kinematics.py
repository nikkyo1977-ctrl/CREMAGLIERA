import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pignone_cremagliera import compute_kinematics, KinResult


def make_params(m=1.0, z=10, alpha_sx_deg=20.0, alpha_dx_deg=20.0,
                x=0.0, ha_cr_coeff=1.0, c_coeff=0.25, delta_s=0.0):
    return dict(m=m, z=z, alpha_sx_deg=alpha_sx_deg, alpha_dx_deg=alpha_dx_deg,
                x=x, ha_cr_coeff=ha_cr_coeff, c_coeff=c_coeff, delta_s=delta_s)


def test_import():
    params = make_params()
    result = compute_kinematics(params)
    assert isinstance(result, KinResult)
