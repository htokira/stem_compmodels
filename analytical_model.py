import math

# навантаження на канал r та приведена завантаженість rho
def calculate_load(lambd, mu, c):
    r = lambd / mu  # навантаження на один канал
    rho = r / c  # приведена завантаженість системи
    return r, rho

# чи виконується умова існування стаціонарного режиму
def is_stationary(rho):
    return rho < 1

# гранична ймовірність простою системи q0
def calculate_q0(r, c, rho):
    if not is_stationary(rho):
        raise ValueError("Немає стаціонарного режиму")
    
    total = 0.0
    for i in range(c):
        total += r ** i / math.factorial(i)
    total += r ** c / math.factorial(c) * (1 / (1 - rho))
    return 1 / total

# гранична ймовірність станів до утворення черги та у черзі
def calculate_q(i, r, c, rho, q0):
    if i <= c: 
        return r ** i / math.factorial(i) * q0 # до утв. черги
    k = i - c
    return r ** c / math.factorial(c) * rho ** k * q0  # після

# ймовірність того, що вимога потрапить у чергу
def calculate_pq(r, c, rho, q0): 
    if not is_stationary(rho):
        raise ValueError("Немає стаціонарного режиму")
    return r ** c / math.factorial(c) * (1 / (1 - rho)) * q0
