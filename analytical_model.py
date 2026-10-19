import math
import pandas as pd
import matplotlib.pyplot as plt

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

# Допоміжна функція для повного розрахунку всіх параметрів за один період
def calculate_system_metrics(lambd, mu, c):
    r, rho = calculate_load(lambd, mu, c)
    
    if not is_stationary(rho):
        return {
            'r': r, 'rho': rho, 'q0': 0.0, 'pq': 1.0,
            'Lq': float('inf'), 'Ls': float('inf'),
            'Wq_min': float('inf'), 'Ws_min': float('inf'),
            'throughput': c * mu, 'stationary': False
        }
    
    q0 = calculate_q0(r, c, rho)
    pq = calculate_pq(r, c, rho, q0)
    
    Lq = pq * (r / (c - r))
    Ls = Lq + r
    
    Wq_min = (Lq / lambd) * 60.0 if lambd > 0 else 0.0
    Ws_min = (Ls / lambd) * 60.0 if lambd > 0 else 0.0

    throughput = lambd if rho < 1 else c * mu
    
    return {
        'r': r, 'rho': rho, 'q0': q0, 'pq': pq,
        'Lq': Lq, 'Ls': Ls,
        'Wq_min': Wq_min, 'Ws_min': Ws_min,
        'throughput': throughput, 'stationary': True
    }

T_SCAN = 0.1
T_FIX = 0.5
N_BINOM = 30
P_BINOM = 0.4

avg_service_time_min = T_SCAN * (N_BINOM * P_BINOM) + T_FIX
mu = 60.0 / avg_service_time_min

PERIODS_DATA = {
    "Ніч (00:00-07:00)":        {"lam_step": 2,  "c": 1},
    "Ранок (07:00-10:00)":      {"lam_step": 14, "c": 2},
    "День (10:00-17:00)":       {"lam_step": 9,  "c": 2},
    "Вечір (17:00-22:00)":      {"lam_step": 36, "c": 4},
    "Пізній вечір (22:00-00:00)": {"lam_step": 8,  "c": 2}
}

results = []

for period_name, data in PERIODS_DATA.items():
    lambd_hourly = data["lam_step"] * 3
    c = data["c"]
    metrics = calculate_system_metrics(lambd_hourly, mu, c)
    
    results.append({
        "Період доби": period_name,
        "λ (люд/год)": lambd_hourly,
        "Кас (c)": c,
        "r (Навантаження)": round(metrics['r'], 2),
        "ρ (Завантаженість)": round(metrics['rho'], 3),
        "q0 (Простій)": round(metrics['q0'], 3),
        "pq (Ймов. черги)": round(metrics['pq'], 3),
        "Lq (Черга, осіб)": round(metrics['Lq'], 2),
        "Wq (Очікування, хв)": round(metrics['Wq_min'], 2),
        "Пропускна здатність A": round(metrics['throughput'], 2)
    })

df_analytical_summary = pd.DataFrame(results)
print("\n=== Результати аналітичної моделі ===")
print(df_analytical_summary.to_string(index=False))

periods_list = df_analytical_summary["Період доби"]
lambda_list = df_analytical_summary["λ (люд/год)"]
throughput_list = df_analytical_summary["Пропускна здатність A"]
wq_list = df_analytical_summary["Wq (Очікування, хв)"]

x = range(len(periods_list))
width = 0.35

plt.figure(figsize=(14, 5))
plt.bar([i - width/2 for i in x], lambda_list, width, label='Вхідний потік (λ)', color='#ff7f0e')
plt.bar([i + width/2 for i in x], throughput_list, width, label='Пропускна здатність (A)', color='#1f77b4')
plt.title("Порівняння вхідного потоку та реальної пропускної здатності", fontsize=12, pad=10)
plt.xticks(x, periods_list)
plt.xlabel("Період доби", fontsize=11)
plt.ylabel("осіб / год", fontsize=11)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

plt.figure(figsize=(14, 5))
bars = plt.bar(periods_list, wq_list, color='#2ca02c', width=0.4)
plt.axhline(y=10, color='r', linestyle='--', linewidth=2, label='Макс. допустима норма (10 хв)')
plt.title("Середній час очікування в черзі (Wq)", fontsize=12, pad=10)
plt.xlabel("Період доби", fontsize=11)
plt.ylabel("хвилини", fontsize=11)
plt.ylim(0, 12)
plt.legend(loc='upper left')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
