import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Параметри моделі
TOTAL_HOURS = 24
STEP_MIN = 20
TOTAL_STEPS = (TOTAL_HOURS * 60) // STEP_MIN

T_SCAN = 0.1
T_FIX = 0.5

N_BINOM = 30
P_BINOM = 0.4

# Визначення інтенсивності Пуассона (мат. сподівання покупців за крок 20 хв)
def get_lambda(step_index):
    minute = step_index * STEP_MIN
    hour = (minute // 60) % 24
    
    if 0 <= hour < 7:
        return 2
    elif 7 <= hour < 10:
        return 14
    elif 10 <= hour < 17:
        return 9
    elif 17 <= hour < 22:
        return 36
    else:
        return 8

class Customer:
    def __init__(self, arrival_time, n_items):
        self.arrival_time = arrival_time
        self.n_items = n_items
        # Час обслуговування: T_cl = T_scan * N_items + T_fix
        self.t_cl = T_SCAN * n_items + T_FIX
        self.service_start_time = None

# Моделювання
queue = []
serviced_count = 0

history_queue_length = []
history_avg_wait_time = []
history_serviced_count = []
time_labels = []

current_time = 0.0

for step in range(TOTAL_STEPS):
    current_time = step * STEP_MIN
    lam = get_lambda(step)
    
    num_new_customers = np.random.poisson(lam)
    
    for _ in range(num_new_customers):
        n_items = max(1, np.random.binomial(N_BINOM, P_BINOM))
        customer = Customer(arrival_time=current_time, n_items=n_items)
        queue.append(customer)
        
    time_remaining_in_step = float(STEP_MIN)
    step_wait_times = []
    
    while time_remaining_in_step > 0 and len(queue) > 0:
        curr_cust = queue[0]
        curr_sim_time = current_time + (STEP_MIN - time_remaining_in_step)
        
        if curr_cust.arrival_time > curr_sim_time:
            time_remaining_in_step = STEP_MIN - (curr_cust.arrival_time - current_time)
            curr_sim_time = curr_cust.arrival_time

        if curr_cust.service_start_time is None:
            curr_cust.service_start_time = curr_sim_time
            wait_time = max(0.0, curr_cust.service_start_time - curr_cust.arrival_time)
            step_wait_times.append(wait_time)   
            
        if curr_cust.t_cl <= time_remaining_in_step:
            time_remaining_in_step -= curr_cust.t_cl
            queue.pop(0)
            serviced_count += 1
        else:
            curr_cust.t_cl -= time_remaining_in_step
            time_remaining_in_step = 0
            
    # Збір статистики за крок
    history_queue_length.append(len(queue))
    
    avg_wait = np.mean(step_wait_times) if step_wait_times else 0.0
    history_avg_wait_time.append(avg_wait)

    history_serviced_count.append(serviced_count)
    
    hour = (step * STEP_MIN) // 60
    minute = (step * STEP_MIN) % 60
    time_labels.append(f"{hour:02d}:{minute:02d}")

df_results = pd.DataFrame({
    'Час': time_labels,
    'W (Час очікування, хв)': history_avg_wait_time,
    'L (Довжина черги, осіб)': history_queue_length,
    'P (Обслужено покупців)': history_serviced_count
})

print("=== Таблиця вихідних параметрів моделі ===")
print(df_results.head(TOTAL_STEPS).to_string(index=False))

plt.figure(figsize=(14, 6))

plt.subplot(2, 1, 1)
plt.plot(range(TOTAL_STEPS), history_queue_length, color='crimson', linewidth=2)
plt.title("Динаміка довжини черги (L) при роботі 1 каси")
plt.ylabel("Довжина черги (осіб)")
plt.xlabel("Кроки моделювання (20 хв)")
plt.grid(True, linestyle='--', alpha=0.6)

plt.subplot(2, 1, 2)
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

print(f"Всього обслужено покупців за добу (P): {serviced_count}")
print(f"Залишок у черзі на кінець доби: {len(queue)}")