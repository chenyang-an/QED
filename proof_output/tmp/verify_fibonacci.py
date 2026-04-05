#!/usr/bin/env python3
"""
Verification script for Fibonacci proof
"""

# Convention 1: F_1 = 1, F_2 = 1 (1-indexed)
def fib_convention1(n):
    """Fibonacci with F_1 = 1, F_2 = 1"""
    if n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        a, b = 1, 1
        for _ in range(3, n + 1):
            a, b = b, a + b
        return b

# Convention 2: F_0 = 0, F_1 = 1 (0-indexed)
def fib_convention2(n):
    """Fibonacci with F_0 = 0, F_1 = 1"""
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

print("=== Verification of Fibonacci Proof ===")
print()

# Verify Convention 1 (F_1 = 1, F_2 = 1)
print("Convention 1: F_1 = 1, F_2 = 1")
for i in range(1, 6):
    print(f"  F_{i} = {fib_convention1(i)}")

f5_conv1 = fib_convention1(5)
print(f"  The 5th Fibonacci number (conv1): F_5 = {f5_conv1}")
print(f"  Proof claims F_5 = 5: {'CONFIRMED' if f5_conv1 == 5 else 'CONTRADICTED'}")
print()

# Verify Convention 2 (F_0 = 0, F_1 = 1)
print("Convention 2: F_0 = 0, F_1 = 1")
for i in range(0, 6):
    print(f"  F_{i} = {fib_convention2(i)}")

f5_conv2 = fib_convention2(5)
print(f"  The 5th Fibonacci number (conv2): F_5 = {f5_conv2}")
print(f"  Proof claims F_5 = 5: {'CONFIRMED' if f5_conv2 == 5 else 'CONTRADICTED'}")
print()

# Verify each computational step in the proof
print("=== Step-by-step verification (Convention 1) ===")
steps = [
    ("F_1 = 1", 1, 1),
    ("F_2 = 1", 2, 1),
    ("F_3 = F_2 + F_1 = 1 + 1 = 2", 3, 2),
    ("F_4 = F_3 + F_2 = 2 + 1 = 3", 4, 3),
    ("F_5 = F_4 + F_3 = 3 + 2 = 5", 5, 5),
]

all_correct = True
for desc, n, claimed in steps:
    actual = fib_convention1(n)
    status = "CONFIRMED" if actual == claimed else "CONTRADICTED"
    if actual != claimed:
        all_correct = False
    print(f"  {desc} -> Actual: {actual}, Claimed: {claimed} -> {status}")

print()
print("=== Step-by-step verification (Convention 2) ===")
steps2 = [
    ("F_0 = 0", 0, 0),
    ("F_1 = 1", 1, 1),
    ("F_2 = F_1 + F_0 = 1 + 0 = 1", 2, 1),
    ("F_3 = F_2 + F_1 = 1 + 1 = 2", 3, 2),
    ("F_4 = F_3 + F_2 = 2 + 1 = 3", 4, 3),
    ("F_5 = F_4 + F_3 = 3 + 2 = 5", 5, 5),
]

for desc, n, claimed in steps2:
    actual = fib_convention2(n)
    status = "CONFIRMED" if actual == claimed else "CONTRADICTED"
    if actual != claimed:
        all_correct = False
    print(f"  {desc} -> Actual: {actual}, Claimed: {claimed} -> {status}")

print()
print(f"=== OVERALL: {'ALL COMPUTATIONS CONFIRMED' if all_correct else 'SOME COMPUTATIONS FAILED'} ===")
