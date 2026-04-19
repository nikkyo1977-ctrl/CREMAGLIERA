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


def test_kinematic_arrays_shape():
    """Gli array hanno 200 punti, theta da 0 a un passo."""
    params = make_params(m=1.0, z=10, x=0.0)
    k = compute_kinematics(params)
    pitch_angle = 2 * np.pi / 10
    assert len(k.theta_arr) == 200
    assert abs(k.theta_arr[0]) < 1e-9
    assert abs(k.theta_arr[-1] - pitch_angle) < 1e-9
    assert len(k.u_sx_arr) == 200
    assert len(k.vs_arr) == 200
    assert len(k.n_pairs_sx_arr) == 200


def test_u_sx_range():
    """u_sx va da -ga_sx a -ga_sx + pb_sx in un passo."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    assert abs(k.u_sx_arr[0] - (-k.ga_sx)) < 1e-9
    assert abs(k.u_sx_arr[-1] - (-k.ga_sx + k.pb_sx)) < 1e-6


def test_vs_zero_at_pitch_point():
    """vs = 0 quando u = 0 (punto primitivo)."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    # Trovare l'indice dove u_sx è più vicino a zero
    idx = np.argmin(np.abs(k.u_sx_arr))
    assert abs(k.vs_arr[idx]) < 0.01  # tolleranza per la discretizzazione


def test_n_pairs_double_contact_zone():
    """La zona di doppio contatto ha lunghezza (eps-1)*pitch_angle."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.5)
    k = compute_kinematics(params)
    pitch_angle = 2 * np.pi / 10
    double_len_expected = (k.eps_sx - 1) * pitch_angle
    double_theta = k.theta_arr[k.n_pairs_sx_arr == 2]
    if len(double_theta) > 0:
        measured = double_theta[-1] - double_theta[0]
        assert abs(measured - double_len_expected) < 0.05 * pitch_angle


def test_n_pairs_minimum_one():
    """n_pairs è sempre >= 1 quando eps >= 1."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.5)
    k = compute_kinematics(params)
    if k.eps_sx >= 1.0:
        assert np.all(k.n_pairs_sx_arr >= 1)


def test_undercut_detection():
    """z=4, x=0, alpha=20°: deve rilevare sottosquadro (z < z_min)."""
    params = make_params(m=1.0, z=4, alpha_sx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    z_min_expected = 2.0 * (1.0 - 0.0) / np.sin(alpha)**2
    assert abs(k.z_min_sx - z_min_expected) < 1e-6
    assert k.undercut_sx is True


def test_no_undercut_with_positive_shift():
    """x=0.5 su z=10 deve eliminare il rischio di undercut.

    Con alpha=20° e x=0.5: z_min = 2*(1-0.5)/sin²(20°) ≈ 8.55.
    z=10 > z_min, quindi nessun undercut.
    """
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.5)
    k = compute_kinematics(params)
    assert k.undercut_sx is False


def test_interference_rack_tip():
    """ga > r*sin(alpha): interferenza della testa cremagliera.

    Con alpha=10°, z=6, x=-0.5, ha_cr=1.5: ga >> r*sin(alpha), interferenza garantita.
    """
    params = make_params(m=1.0, z=6, alpha_sx_deg=10.0, x=-0.5, ha_cr_coeff=1.5)
    k = compute_kinematics(params)
    assert k.interference_rack_tip_sx is True  # ga >> r*sin(alpha) for these params


def test_no_interference_standard():
    """Setup standard z=20, m=1, alpha=20°, x=0: nessuna interferenza."""
    params = make_params(m=1.0, z=20, alpha_sx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    assert k.interference_rack_tip_sx is False
    assert k.undercut_sx is False
