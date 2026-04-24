import numpy as np
import math
from qiskit import QuantumCircuit, QuantumRegister


def to_power2(n):
    return 2 ** math.ceil(math.log2(max(n, 2)))


def preprocess(image: np.ndarray, max_dim: int = 32) -> np.ndarray:
    from PIL import Image as PILImage
    arr = image.astype(np.float64)
    h, w = arr.shape
    nh = to_power2(min(h, max_dim))
    nw = to_power2(min(w, max_dim))
    pil = PILImage.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    pil = pil.resize((nw, nh), PILImage.LANCZOS)
    return np.array(pil, dtype=np.float64)


def normalise(arr: np.ndarray) -> np.ndarray:
    mn, mx = arr.min(), arr.max()
    if mx == mn:
        return np.zeros_like(arr, dtype=np.float64)
    return (arr - mn) / (mx - mn)


class NEQREncoder:
    def __init__(self, image: np.ndarray, value_bits: int = 8):
        img = preprocess(image)
        self.raw = img
        scaled = normalise(img) * (2 ** value_bits - 1)
        self.image = np.round(scaled).astype(int)
        self.H, self.W = self.image.shape
        self.n_row = int(math.log2(self.H))
        self.n_col = int(math.log2(self.W))
        self.n_val = value_bits
        self.n_total = self.n_val + self.n_row + self.n_col

    def build_circuit(self) -> QuantumCircuit:
        val_qr = QuantumRegister(self.n_val, "val")
        row_qr = QuantumRegister(self.n_row, "row")
        col_qr = QuantumRegister(self.n_col, "col")
        qc = QuantumCircuit(val_qr, row_qr, col_qr)
        for q in row_qr:
            qc.h(q)
        for q in col_qr:
            qc.h(q)
        for i in range(self.H):
            for j in range(self.W):
                pv = int(self.image[i, j])
                if pv == 0:
                    continue
                row_bits = [(i >> b) & 1 for b in range(self.n_row)]
                col_bits = [(j >> b) & 1 for b in range(self.n_col)]
                for b, bit in enumerate(row_bits):
                    if bit == 0:
                        qc.x(row_qr[b])
                for b, bit in enumerate(col_bits):
                    if bit == 0:
                        qc.x(col_qr[b])
                ctrl = list(row_qr) + list(col_qr)
                for bp in range(self.n_val):
                    if (pv >> bp) & 1:
                        qc.mcx(ctrl, val_qr[bp])
                for b, bit in enumerate(row_bits):
                    if bit == 0:
                        qc.x(row_qr[b])
                for b, bit in enumerate(col_bits):
                    if bit == 0:
                        qc.x(col_qr[b])
        return qc

    def decode_statevector(self, sv: np.ndarray) -> np.ndarray:
        probs = np.abs(sv) ** 2
        img_out = np.zeros((self.H, self.W), dtype=np.float64)
        n_val, n_row, n_col = self.n_val, self.n_row, self.n_col
        n_total = n_val + n_row + n_col
        for idx in range(len(sv)):
            bits = [(idx >> b) & 1 for b in range(n_total)]
            val = sum(bits[b] << b for b in range(n_val))
            row = sum(bits[n_val + b] << b for b in range(n_row))
            col = sum(bits[n_val + n_row + b] << b for b in range(n_col))
            if row < self.H and col < self.W:
                img_out[row, col] += val * probs[idx]
        total = probs.sum()
        if total > 0:
            img_out /= (total / (self.H * self.W))
        return np.clip(img_out, 0, 255)