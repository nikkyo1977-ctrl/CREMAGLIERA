import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from pignone_cremagliera import compute_kinematics, KinResult


def make_params(m=1.0, z=10, alpha_sx_deg=20.0, alpha_dx_deg=20.0,
                x=0.0, ha_cr_coeff=1.0, c_coeff=0.25, delta_s=0.0):
    return dict(m=m, z=z, alpha_sx_deg=alpha_sx_deg, alpha_dx_deg=alpha_dx_deg,
                x=x, ha_cr_coeff=ha_cr_coeff, c_coeff=c_coeff, delta_s=delta_s)


def test_import():
    params = make_params()
    result = compute_kinematics(params)
    assert isinstance(result, KinResult)


def test_base_geometry_standard():
    """z=10, m=1, alpha=20°, x=0: valori standard ISO."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, alpha_dx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    assert abs(k.r - 5.0) < 1e-9
    assert abs(k.ra - 6.0) < 1e-9        # r + (1+0)*m
    assert abs(k.H - 5.0) < 1e-9         # r + 0*m
    assert abs(k.da - 12.0) < 1e-9
    assert abs(k.rb_sx - 5.0 * np.cos(np.radians(20.0))) < 1e-9
    assert abs(k.rb_dx - 5.0 * np.cos(np.radians(20.0))) < 1e-9


def test_profile_shift_geometry():
    """x=0.5: ra, H, rf cambiano correttamente."""
    params = make_params(m=1.0, z=10, x=0.5)
    k = compute_kinematics(params)
    assert abs(k.ra - (5.0 + 1.5)) < 1e-9    # r + (1+0.5)*m
    assert abs(k.H - 5.5) < 1e-9             # r + 0.5*m
    assert abs(k.rf - (5.0 - (1.0 + 0.25 - 0.5))) < 1e-9  # r - (ha_cr + c - x*m)


def test_ga_bug_fix_zero_x():
    """Con x=0, ga deve coincidere con ha_cr/sin(alpha)."""
    params = make_params(m=1.0, z=12, alpha_sx_deg=20.0, x=0.0, ha_cr_coeff=1.0)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    expected = 1.0 / np.sin(alpha)   # ha_cr=1.0*m=1.0
    assert abs(k.ga_sx - expected) < 1e-9


def test_ga_bug_fix_positive_x():
    """Con x=0.5, ga deve essere (ha_cr - x*m)/sin(alpha)."""
    params = make_params(m=1.0, z=12, alpha_sx_deg=20.0, x=0.5, ha_cr_coeff=1.0)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    ha_cr = 1.0 * 1.0  # ha_cr_coeff * m
    expected = (ha_cr - 0.5 * 1.0) / np.sin(alpha)
    assert abs(k.ga_sx - expected) < 1e-9


def test_ga_bug_fix_negative_x():
    """Con x=-0.3, ga deve essere (ha_cr - x*m)/sin(alpha) > ha_cr/sin(alpha)."""
    params = make_params(m=1.0, z=12, alpha_sx_deg=20.0, x=-0.3, ha_cr_coeff=1.0)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    ha_cr = 1.0
    expected = (ha_cr - (-0.3) * 1.0) / np.sin(alpha)
    assert abs(k.ga_sx - expected) < 1e-9


def test_gf_formula():
    """gf = sqrt(ra^2 - rb^2) - r*sin(alpha)."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.5)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    ra = 5.0 + 1.5  # r + (1+x)*m
    rb = 5.0 * np.cos(alpha)
    r = 5.0
    expected = np.sqrt(ra**2 - rb**2) - r * np.sin(alpha)
    assert abs(k.gf_sx - expected) < 1e-9


def test_contact_ratio():
    """eps = (ga + gf) / pb."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.5, ha_cr_coeff=1.0)
    k = compute_kinematics(params)
    expected = (k.ga_sx + k.gf_sx) / k.pb_sx
    assert abs(k.eps_sx - expected) < 1e-9


def test_linear_displacement():
    """L = pi * m * z."""
    params = make_params(m=2.0, z=15)
    k = compute_kinematics(params)
    assert abs(k.L - np.pi * 2.0 * 15) < 1e-9


def test_tooth_thickness_symmetric():
    """sp = m*(pi/2 + x*(tan_sx + tan_dx)) - delta_s."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, alpha_dx_deg=20.0,
                         x=0.5, delta_s=0.05)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    expected = 1.0 * (np.pi / 2 + 0.5 * (np.tan(alpha) + np.tan(alpha))) - 0.05
    assert abs(k.sp - expected) < 1e-9
