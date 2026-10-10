import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import deque

# Параметри моделі
TOTAL_HOURS = 24
STEP_MIN = 20
TOTAL_STEPS = (TOTAL_HOURS * 60) // STEP_MIN

T_SCAN = 0.1
T_FIX = 0.5

N_BINOM = 30
P_BINOM = 0.4

C = 5

# інтенсивність Пуассона (мат. сподівання покупців за крок 20 хв)
LAMBDAS = {
    "night": 2,
    "morning": 14,
    "day": 9,
    "evening": 36,
    "late": 8,
}

# статичний розклад
SCHEDULE = {
    "night":     1,
    "morning":   2,
    "day":       1,
    "evening":   4,
    "late":      1,
}

# Визначення періоду часу
def get_period(step_index):
    minute = step_index * STEP_MIN
    hour = (minute // 60) % 24
    
    if 0 <= hour < 7:
        return "night"
    elif 7 <= hour < 10:
        return "morning"
    elif 10 <= hour < 17:
        return "day"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "late"

# Інтенсивність потоку для кроку
def get_lambda(step_index):
    return LAMBDAS[get_period(step_index)]

# Скільки кас працює наразі
def get_open_cashiers(step_index):
    return max(1, min(C, SCHEDULE[get_period(step_index)]))

class Customer:
    def __init__(self, arrival_time, n_items):
        self.arrival_time = arrival_time
        self.n_items = n_items
        # Час обслуговування: T_cl = T_scan * N_items + T_fix
        self.t_cl = T_SCAN * n_items + T_FIX
        self.service_start_time = None

# Моделювання
queue = deque() # єдина черга
channel_free_time = [0.0] * C # момент, коли кожна каса звільниться

serviced_count = 0

history_queue_length = []
history_avg_wait_time = []
history_serviced_count = []
history_all_items = []
history_rho = []
time_labels = []

avg_items = N_BINOM * P_BINOM
avg_service_time = T_SCAN * avg_items + T_FIX
step_capacity_per_cashier = STEP_MIN / avg_service_time

current_time = 0.0

for step in range(TOTAL_STEPS):
    current_time = step * STEP_MIN
    step_end = current_time + STEP_MIN
    lam = get_lambda(step)
    
    num_new_customers = np.random.poisson(lam)
    
    for _ in range(num_new_customers):
        n_items = max(1, np.random.binomial(N_BINOM, P_BINOM))
        history_all_items.append(n_items)
        customer = Customer(arrival_time=current_time, n_items=n_items)
        queue.append(customer)

    c_open = get_open_cashiers(step)

    for i in range(c_open):
        channel_free_time[i] = max(channel_free_time[i], current_time)
        
    step_wait_times = []
    
    while len(queue) > 0:
        earliest_cash = min(range(c_open), key=lambda i: channel_free_time[i])
        curr_cust = queue[0]
        start_time = max(channel_free_time[earliest_cash], curr_cust.arrival_time)

        if start_time >= step_end:
            break

        queue.popleft()
        
        curr_cust.service_start_time = start_time
        wait_time = max(0.0, curr_cust.service_start_time - curr_cust.arrival_time)
        step_wait_times.append(wait_time)

        channel_free_time[earliest_cash] = start_time + curr_cust.t_cl
        serviced_count += 1
            
    # Збір статистики за крок
    history_queue_length.append(len(queue))
    
    avg_wait = np.mean(step_wait_times) if step_wait_times else 0.0
    history_avg_wait_time.append(avg_wait)

    history_serviced_count.append(serviced_count)

    total_capacity = c_open * step_capacity_per_cashier
    rho = lam / total_capacity if total_capacity > 0 else 0.0
    history_rho.append(rho)
    
    hour = (step * STEP_MIN) // 60
    minute = (step * STEP_MIN) % 60
    time_labels.append(f"{hour:02d}:{minute:02d}")

df_results = pd.DataFrame({
    'Час': time_labels,
    'W (Час очікування, хв)': history_avg_wait_time,
    'L (Довжина черги, осіб)': history_queue_length,
    'P (Обслужено покупців)': history_serviced_count,
    'ρ (Інтенсивність потоку)': history_rho
})

print("=== Таблиця вихідних параметрів моделі ===")
print(df_results.head(TOTAL_STEPS).to_string(index=False))

plt.figure(figsize=(14, 6))
plt.plot(range(TOTAL_STEPS), history_queue_length, color='crimson', linewidth=2)
plt.title("Динаміка довжини черги (L) при роботі кількох кас")
plt.ylabel("Довжина черги (осіб)")
plt.xlabel("Кроки моделювання (20 хв)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

plt.figure(figsize=(14, 6))
plt.plot(range(TOTAL_STEPS), history_avg_wait_time, color='navy', linewidth=2)
plt.axhline(y=10, color='r', linestyle=':', label='Макс. допустимий час очікування (10 хв)')
plt.title("Середній час очікування в черзі (W)")
plt.xlabel("Час доби")
plt.ylabel("Час (хв)")
plt.xticks(range(0, TOTAL_STEPS, 3), time_labels[::3], rotation=45)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

plt.figure(figsize=(14, 5))
plt.hist(history_all_items, bins=range(1, N_BINOM + 2), color='purple', edgecolor='black', alpha=0.7, align='left')
plt.title("Розподіл кількості товарів у кошиках покупців")
plt.xlabel("Кількість товарів у чеку (шт.)")
plt.ylabel("Кількість покупців")
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

plt.figure(figsize=(14, 5))
plt.plot(range(TOTAL_STEPS), history_rho, color='darkorange', linewidth=2, label='Коефіцієнт завантаження системи (ρ)')
plt.axhline(y=1.0, color='red', linestyle='--', linewidth=1.5, label='Критичний рівень перевантаження (ρ = 1.0)')
plt.title("Динаміка коефіцієнта завантаження системи (ρ) протягом доби")
plt.xlabel("Час доби")
plt.ylabel("Коефіцієнт завантаження (ρ)")
plt.xticks(range(0, TOTAL_STEPS, 3), time_labels[::3], rotation=45)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

print(f"Всього обслужено покупців за добу (P): {serviced_count}")
print(f"Залишок у черзі на кінець доби: {len(queue)}")