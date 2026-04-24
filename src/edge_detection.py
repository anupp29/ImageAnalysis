import numpy as np
import time
from qiskit import transpile
from qiskit_aer import StatevectorSimulator
from encoding import NEQREncoder, normalise
from scipy import ndimage

_SIM = StatevectorSimulator()


def _cyclic_increment(qc, reg):
    n = len(reg)
    for i in range(n - 1, -1, -1):
        if i == 0:
            qc.x(reg[0])
        else:
            qc.mcx(reg[:i], reg[i])


def _run_shifted(enc: NEQREncoder, axis: str) -> np.ndarray:
    qc = enc.build_circuit()
    n_val, n_row, n_col = enc.n_val, enc.n_row, enc.n_col
    if axis == "col":
        start = n_val + n_row
        reg = list(range(start, start + n_col))
    else:
        start = n_val
        reg = list(range(start, start + n_row))
    _cyclic_increment(qc, reg)
    sv = np.array(_SIM.run(transpile(qc, _SIM)).result().get_statevector())
    return enc.decode_statevector(sv)


def run(image: np.ndarray) -> dict:
    enc = NEQREncoder(image)
    t0 = time.perf_counter()

    qc_orig = enc.build_circuit()
    sv_orig = np.array(_SIM.run(transpile(qc_orig, _SIM)).result().get_statevector())
    decoded = enc.decode_statevector(sv_orig)

    h_shifted = _run_shifted(enc, axis="col")
    v_shifted = _run_shifted(enc, axis="row")

    h_edge = np.abs(decoded.astype(float) - h_shifted.astype(float))
    v_edge = np.abs(decoded.astype(float) - v_shifted.astype(float))
    combined = np.hypot(h_edge, v_edge)
    combined = normalise(combined) * 255.0

    elapsed = time.perf_counter() - t0

    img_n = normalise(enc.raw) * 255.0
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)
    ky = kx.T
    sobel = normalise(np.hypot(ndimage.convolve(img_n, kx), ndimage.convolve(img_n, ky))) * 255.0
    laplacian = normalise(np.abs(ndimage.convolve(img_n, np.array([[0,1,0],[1,-4,1],[0,1,0]], dtype=float))
    )) * 255.0

    corr_sobel = float(np.corrcoef(combined.flatten(), sobel.flatten())[0, 1])
    corr_lap   = float(np.corrcoef(combined.flatten(), laplacian.flatten())[0, 1])
    mse_sobel  = float(np.mean((combined - sobel) ** 2))

    return {
        "original": enc.raw,
        "quantum_h": h_edge,
        "quantum_v": v_edge,
        "quantum": combined,
        "sobel": sobel,
        "laplacian": laplacian,
        "corr_sobel": corr_sobel,
        "corr_laplacian": corr_lap,
        "mse_vs_sobel": mse_sobel,
        "qubits": qc_orig.num_qubits,
        "depth": qc_orig.depth(),
        "gate_count": qc_orig.size(),
        "elapsed": elapsed,
        "image_size": (enc.H, enc.W),
    }