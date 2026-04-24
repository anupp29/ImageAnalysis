import numpy as np
import math
import time
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from encoding import normalise

_SIM = AerSimulator()


def _amplitude_state(vec: np.ndarray) -> np.ndarray:
    n = len(vec)
    n2 = 2 ** math.ceil(math.log2(max(n, 2)))
    padded = np.pad(vec.astype(np.float64), (0, n2 - n))
    nrm = np.linalg.norm(padded)
    return padded / nrm if nrm > 0 else padded


def _build_swap_test(vec_a: np.ndarray, vec_b: np.ndarray) -> QuantumCircuit:
    n = int(math.log2(len(vec_a)))
    qc = QuantumCircuit(1 + 2 * n, 1)
    sub_a = QuantumCircuit(n)
    sub_a.initialize(vec_a.tolist(), list(range(n)))
    sub_b = QuantumCircuit(n)
    sub_b.initialize(vec_b.tolist(), list(range(n)))
    qc.compose(sub_a, qubits=list(range(1, 1 + n)), inplace=True)
    qc.compose(sub_b, qubits=list(range(1 + n, 1 + 2 * n)), inplace=True)
    qc.h(0)
    for i in range(n):
        qc.cswap(0, 1 + i, 1 + n + i)
    qc.h(0)
    qc.measure(0, 0)
    return qc


def run(image_a: np.ndarray, image_b: np.ndarray, shots: int = 8192) -> dict:
    flat_a = _amplitude_state(normalise(image_a).flatten())
    flat_b = _amplitude_state(normalise(image_b).flatten())
    if len(flat_a) != len(flat_b):
        target = max(len(flat_a), len(flat_b))
        target = 2 ** math.ceil(math.log2(target))
        flat_a = np.pad(flat_a, (0, target - len(flat_a)))
        flat_b = np.pad(flat_b, (0, target - len(flat_b)))
        nrm_a = np.linalg.norm(flat_a)
        nrm_b = np.linalg.norm(flat_b)
        if nrm_a > 0: flat_a /= nrm_a
        if nrm_b > 0: flat_b /= nrm_b
    t0 = time.perf_counter()
    qc = _build_swap_test(flat_a, flat_b)
    counts = _SIM.run(transpile(qc, _SIM), shots=shots).result().get_counts()
    elapsed = time.perf_counter() - t0
    p0 = counts.get("0", 0) / shots
    q_sim = max(0.0, 2 * p0 - 1.0)
    c_sim = float(np.dot(flat_a, flat_b))
    c_mse = float(np.mean((normalise(image_a) - normalise(image_b)) ** 2))
    c_hist = float(np.sum(np.minimum(
        np.histogram(normalise(image_a), bins=64)[0],
        np.histogram(normalise(image_b), bins=64)[0]
    )) / min(image_a.size, image_b.size))
    return {
        "quantum_similarity": q_sim,
        "classical_cosine": c_sim,
        "classical_mse": c_mse,
        "histogram_intersection": c_hist,
        "counts": counts,
        "shots": shots,
        "qubits": qc.num_qubits,
        "depth": qc.depth(),
        "gate_count": qc.size(),
        "elapsed": elapsed,
    }


def batch(query: np.ndarray, gallery: list, shots: int = 4096) -> list:
    results = []
    for idx, ref in enumerate(gallery):
        r = run(query, ref, shots=shots)
        results.append({"index": idx, **r})
    return sorted(results, key=lambda x: -x["quantum_similarity"])