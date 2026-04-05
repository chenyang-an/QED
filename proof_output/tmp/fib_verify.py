def fib1(n):
    if n == 1 or n == 2: return 1
    return fib1(n-1) + fib1(n-2)

def fib2(n):
    if n == 0: return 0
    if n == 1: return 1
    return fib2(n-1) + fib2(n-2)

print("fib1(5) =", fib1(5))
print("fib2(5) =", fib2(5))
