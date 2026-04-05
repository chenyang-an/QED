def fib_f1_f2(n: int) -> int:
    if n == 1 or n == 2:
        return 1
    a, b = 1, 1
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


def fib_f0_f1(n: int) -> int:
    if n == 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def main() -> None:
    seq_f1 = [fib_f1_f2(i) for i in range(1, 6)]
    seq_f0 = [fib_f0_f1(i) for i in range(0, 6)]
    with open("/Users/an/Desktop/cm/QED/proof_output/tmp/verify_fib_output.txt", "w", encoding="ascii") as f:
        f.write(f"F1/F2 convention sequence through n=5: {seq_f1}\n")
        f.write(f"F0/F1 convention sequence through n=5: {seq_f0}\n")
        f.write(f"F1/F2 recurrence check n=3: {fib_f1_f2(3)} == {fib_f1_f2(2)} + {fib_f1_f2(1)}\n")
        f.write(f"F1/F2 recurrence check n=4: {fib_f1_f2(4)} == {fib_f1_f2(3)} + {fib_f1_f2(2)}\n")
        f.write(f"F1/F2 recurrence check n=5: {fib_f1_f2(5)} == {fib_f1_f2(4)} + {fib_f1_f2(3)}\n")
        f.write(f"F0/F1 recurrence check n=2: {fib_f0_f1(2)} == {fib_f0_f1(1)} + {fib_f0_f1(0)}\n")
        f.write(f"F0/F1 recurrence check n=3: {fib_f0_f1(3)} == {fib_f0_f1(2)} + {fib_f0_f1(1)}\n")
        f.write(f"F0/F1 recurrence check n=4: {fib_f0_f1(4)} == {fib_f0_f1(3)} + {fib_f0_f1(2)}\n")
        f.write(f"F0/F1 recurrence check n=5: {fib_f0_f1(5)} == {fib_f0_f1(4)} + {fib_f0_f1(3)}\n")
        f.write(f"F_5 under F1/F2 convention: {fib_f1_f2(5)}\n")
        f.write(f"F_5 under F0/F1 convention: {fib_f0_f1(5)}\n")
        f.write(f"5th listed term if sequence is written from F_0: {seq_f0[4]}\n")


if __name__ == "__main__":
    main()
