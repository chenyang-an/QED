from pathlib import Path


def fib_one_based(n: int) -> int:
    if n == 1 or n == 2:
        return 1
    a, b = 1, 1
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


def fib_zero_based(n: int) -> int:
    if n == 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


results = {
    "one_based_F3": fib_one_based(3),
    "one_based_F4": fib_one_based(4),
    "one_based_F5": fib_one_based(5),
    "zero_based_F2": fib_zero_based(2),
    "zero_based_F3": fib_zero_based(3),
    "zero_based_F4": fib_zero_based(4),
    "zero_based_F5": fib_zero_based(5),
    "one_based_5th_term": fib_one_based(5),
    "zero_based_5th_term": [fib_zero_based(i) for i in range(6)][4],
}

lines = [
    f"one_based_F3={results['one_based_F3']}",
    f"one_based_F4={results['one_based_F4']}",
    f"one_based_F5={results['one_based_F5']}",
    f"zero_based_F2={results['zero_based_F2']}",
    f"zero_based_F3={results['zero_based_F3']}",
    f"zero_based_F4={results['zero_based_F4']}",
    f"zero_based_F5={results['zero_based_F5']}",
    f"one_based_5th_term={results['one_based_5th_term']}",
    f"zero_based_5th_term={results['zero_based_5th_term']}",
]

out_path = Path("/Users/an/Desktop/cm/QED/proof_output/tmp/check_fibonacci_claims_output.txt")
out_path.write_text("\n".join(lines) + "\n", encoding="ascii")
print("Wrote", out_path)
