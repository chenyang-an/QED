from decimal import Decimal, getcontext

import sympy as sp


def recurrence_one_indexed():
    values = {1: 1, 2: 1}
    for n in range(3, 6):
        values[n] = values[n - 1] + values[n - 2]
    return values


def recurrence_zero_indexed():
    values = {0: 0, 1: 1}
    for n in range(2, 6):
        values[n] = values[n - 1] + values[n - 2]
    return values


def main():
    out_lines = []

    one_indexed = recurrence_one_indexed()
    out_lines.append(f"1-indexed recurrence values: {one_indexed}")

    phi = (1 + sp.sqrt(5)) / 2
    psi = (1 - sp.sqrt(5)) / 2
    binet_exact = sp.simplify((phi**5 - psi**5) / sp.sqrt(5))
    out_lines.append(f"Binet exact value at n=5: {binet_exact}")

    getcontext().prec = 30
    sqrt5 = Decimal(5).sqrt()
    phi_dec = (Decimal(1) + sqrt5) / Decimal(2)
    psi_dec = (Decimal(1) - sqrt5) / Decimal(2)
    phi5_dec = phi_dec**5
    psi5_dec = psi_dec**5
    diff_dec = phi5_dec - psi5_dec
    quotient_dec = diff_dec / sqrt5

    out_lines.append(f"phi approx: {phi_dec}")
    out_lines.append(f"psi approx: {psi_dec}")
    out_lines.append(f"phi^5 approx: {phi5_dec}")
    out_lines.append(f"psi^5 approx: {psi5_dec}")
    out_lines.append(f"phi^5 - psi^5 approx: {diff_dec}")
    out_lines.append(f"(phi^5 - psi^5)/sqrt(5) approx: {quotient_dec}")
    out_lines.append(f"phi formatted to 10 decimals: {phi_dec:.10f}")
    out_lines.append(f"psi formatted to 10 decimals: {psi_dec:.10f}")
    out_lines.append(f"phi^5 formatted to 10 decimals: {phi5_dec:.10f}")
    out_lines.append(f"psi^5 formatted to 10 decimals: {psi5_dec:.10f}")
    out_lines.append(f"phi^5 - psi^5 formatted to 10 decimals: {diff_dec:.10f}")
    out_lines.append(f"sqrt(5) formatted to 10 decimals: {sqrt5:.10f}")
    out_lines.append(
        f"(phi^5 - psi^5)/sqrt(5) formatted to 10 decimals: {quotient_dec:.10f}"
    )

    zero_indexed = recurrence_zero_indexed()
    out_lines.append(f"0-indexed recurrence values: {zero_indexed}")

    checks = {
        "F1_equals_1": one_indexed[1] == 1,
        "F2_equals_1": one_indexed[2] == 1,
        "F3_equals_2": one_indexed[3] == 2,
        "F4_equals_3": one_indexed[4] == 3,
        "F5_equals_5": one_indexed[5] == 5,
        "Binet_exact_equals_5": binet_exact == 5,
        "Zero_indexed_F5_equals_5": zero_indexed[5] == 5,
    }
    out_lines.append(f"Boolean checks: {checks}")

    output_path = (
        "/Users/an/Desktop/cm/QED/proof_output/tmp/"
        "verify_fib_proof_output.txt"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")

    print("wrote", output_path)
    for key, value in checks.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
