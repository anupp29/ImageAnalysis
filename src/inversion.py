import numpy as np
import time
from qiskit import QuantumCircuit, transpile
from qiskit_aer import StatevectorSimulator
from encoding import NEQREncoder, normalise

_SIM = StatevectorSimulator()


def run(image: np.ndarray) -> dict:
    enc = NEQREncoder(image)
    t0 = time.perf_counter()
    base = enc.build_circuit()
    inv = QuantumCircuit(base.num_qubits)
    inv.compose(base, inplace=True)
    for q in range(enc.n_val):
        inv.x(q)
    sv = np.array(_SIM.run(transpile(inv, _SIM)).result().get_statevector())
    elapsed = time.perf_counter() - t0
    q_inv = enc.decode_statevector(sv)
    c_inv = 255.0 - normalise(enc.raw) * 255.0
    mse = float(np.mean((q_inv - c_inv) ** 2))
    psnr = float(10 * np.log10(255 ** 2 / mse)) if mse > 0 else float("inf")
    ssim = float(_ssim(q_inv, c_inv))
    return {
        "original": enc.raw,
        "quantum": q_inv,
        "classical": c_inv,
        "mse": mse,
        "psnr": psnr,
        "ssim": ssim,
        "qubits": inv.num_qubits,
        "depth": inv.depth(),
        "gate_count": inv.size(),
        "elapsed": elapsed,
        "image_size": (enc.H, enc.W),
    }


def _ssim(a: np.ndarray, b: np.ndarray, c1=6.5025, c2=58.5225) -> float:
    a = a / 255.0
    b = b / 255.0
    mu_a, mu_b = a.mean(), b.mean()
    sig_a = a.std() ** 2
    sig_b = b.std() ** 2
    sig_ab = float(np.mean((a - mu_a) * (b - mu_b)))
    num = (2 * mu_a * mu_b + c1) * (2 * sig_ab + c2)
    den = (mu_a**2 + mu_b**2 + c1) * (sig_a + sig_b + c2)
    return num / den if den != 0 else 1.0