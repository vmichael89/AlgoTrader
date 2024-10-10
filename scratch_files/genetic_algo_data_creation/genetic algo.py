import random
import numpy as np
import pandas as pd
import os
import json

# Genetic algorithm parameters
POPULATION_SIZE = 200
ELITISM_COPIES = 1
NUM_GENERATIONS = 10


# Define the Strategy class to represent an individual in the population
class Strategy:
    def __init__(self):
        self.filters = filters = [
            'RSI3070', 'RSI4060', 'PAB15MA', 'PAB50MA', 'PAB100MA', 'ATRTA', 'ATRTB',
            'INDEC', 'ENGULF', 'HAMMER', 'BIGCAND', 'ADXTA', 'ADXTB', 'HH0', 'HH1',
            'LH0', 'LH1', 'HL0', 'HL1', 'LL0', 'LL1', 'RELVOL'
        ]

        self.entry_events = entry_events = ['TRNDLN72', 'INDEC', 'ENGULF', 'HAMMER', 'MACRS1550', 'MACRS50100', 'PLBCK', 'BLBND']

        self.exit_events = exit_events = ['BLBND', 'MACRS1550', 'MACRS50100', 'EX2', 'EX3', 'EX4']

        # Randomly initialize filters as a string of 0s and 1s
        # self.filter_string = ''.join(random.choice(['0', '1']) for _ in range(len(filters)))
        # self.filter_string = ''.join(random.choice(['0']) for _ in range(len(filters)))
        self.filter_string = ''.join(random.choices(['0', '1'], weights=[0.8, 0.2], k=len(self.filters)))
        # Randomly select entry and exit events
        self.entry_event = random.choice(entry_events)
        self.exit_event = random.choice(exit_events)
        self.trades = pd.DataFrame()
        self.time_for_200 = 0
        self.took_too_long = False
        self.MUTATION_RATE = 0.05

    def find_fitness(self):
        if self.took_too_long:
            self.fitness = 0
            print('Took too long...')
            return

        if len(self.trades) > 0:
            self.trades['return'] = self.trades.apply(
                lambda row: row['exit_p'] - row['entry_p'] if row['type'] == 1
                else row['entry_p'] - row['exit_p'],
                axis=1
            )

        win_count = (self.trades['return'] > 0).sum() if len(self.trades) > 0 else 0
        total_trades = len(self.trades)
        self.win_rate = (win_count / total_trades) if total_trades > 0 else 0

        self.reward_risk = abs((self.trades[self.trades['return'] > 0]['return'].mean()) / \
                      self.trades[self.trades['return'] < 0]['return'].mean())

        self.expectancy = self.win_rate * self.reward_risk - (1-self.win_rate) * 1

        self.fitness = max(0, self.expectancy/self.time_for_200)

    def data_feed_strategy(self, type='training'):
        self.trades = pd.DataFrame()
        self.time_for_200 = 0

        # Define the folder path containing the ticker data
        data_folder = '../../data/data_features'

        # Define the start and end date for filtering the ticker data

        if type=='training':
            start_date = pd.to_datetime("2014-10-08")
            end_date = pd.to_datetime("2023-10-08")
        elif type == 'validation':
            start_date = pd.to_datetime("2023-10-08")
            end_date = pd.to_datetime("2024-04-08")
        elif type=='test':
            start_date = pd.to_datetime("2024-04-08")
            end_date = pd.to_datetime("2024-10-08")

        while len(self.trades) < 200:
            # Randomly select a ticker file from the data folder
            ticker_file = random.choice(os.listdir(data_folder))
            ticker_path = os.path.join(data_folder, ticker_file)

            # Load the OHLCV data for the selected ticker
            ohlcv = pd.read_csv(ticker_path, parse_dates=['date'], index_col='date')

            # Filter the DataFrame to include only the desired date range
            ohlcv = ohlcv[(ohlcv.index >= start_date) & (ohlcv.index <= end_date)]

            # Ensure there are enough candles in the filtered DataFrame
            if len(ohlcv) < 1440:
                continue  # Not enough data, skip this ticker

            # Randomly select a start index for a 2-week (1440 candles) period
            random_start = random.randint(0, len(ohlcv) - 1440)
            ohlcv_section = ohlcv.iloc[random_start:random_start + 1440]

            # Reset index of the selected section (optional, depending on your usage)
            ohlcv_section = ohlcv_section.reset_index(drop=True)

            # Feed the 2-week section of OHLCV data to the strategy
            self.run_strategy(ohlcv_section)

            # If the strategy has taken too long, exit the loop early
            if self.took_too_long:
                # print("Strategy took too long. Exiting.")
                break

        # Print total trades after finishing feeding data
        # print(f"Finished feeding data. Total trades: {len(self.trades)}")
    def get_parameters(self):
        selected_filters = [self.filters[i] for i in range(len(self.filter_string)) if self.filter_string[i] == '1']

        return selected_filters, self.entry_event, self.exit_event

    def run_strategy(self, ohlcv):
        selected_filters = [self.filters[i] for i in range(len(self.filter_string)) if self.filter_string[i] == '1']

        in_trade = False

        trade_i = len(self.trades)

        close = ohlcv['close'].to_numpy()

        for i in range(len(ohlcv)):
            self.time_for_200 += 1

            if len(self.trades)>=200:
                return

            if self.time_for_200>=100000:
                self.took_too_long = True
                return

            if not in_trade:
                if (not selected_filters or all(ohlcv.loc[i, filter_] in (1, 2) for filter_ in selected_filters)) and ohlcv.loc[i, self.entry_event] in (1, 2):
                    in_trade = True

                    self.trades.loc[trade_i, 'entry_p'] = close[i]
                    self.trades.loc[trade_i, 'type'] = 1

                    if self.exit_event in ["EX2", "EX3", "EX4"]:
                        target_levels = json.loads(ohlcv.loc[i, self.exit_event].replace('nan', 'null'))

                        if target_levels[0] == None:
                            in_trade = False
                            trade_i+=1

                            continue

                        self.trades.loc[trade_i, 'sl'] = target_levels[0]
                        self.trades.loc[trade_i, 'tp'] = target_levels[1]

                if (not selected_filters or all(ohlcv.loc[i, filter_] in (-1, 2) for filter_ in selected_filters)) and ohlcv.loc[i, self.entry_event] in (-1, 2):
                    in_trade = True

                    self.trades.loc[trade_i, 'entry_p'] = close[i]
                    self.trades.loc[trade_i, 'type'] = -1

                    if self.exit_event in ["EX2", "EX3", "EX4"]:
                        target_levels = json.loads(ohlcv.loc[i, self.exit_event].replace('nan', 'null'))

                        if target_levels[0] == None:
                            in_trade = False
                            trade_i+=1

                            continue

                        self.trades.loc[trade_i, 'sl'] = target_levels[1]
                        self.trades.loc[trade_i, 'tp'] = target_levels[0]

            if in_trade:
                if self.exit_event in ["EX2", "EX3", "EX4"]:
                    if (self.trades.loc[trade_i, 'type'] == 1 and (close[i] >= self.trades.loc[trade_i, 'tp'] or close[i] <= self.trades.loc[trade_i, 'sl'])) or \
                            (self.trades.loc[trade_i, 'type'] == -1 and (close[i] <= self.trades.loc[trade_i, 'tp'] or close[i] >= self.trades.loc[trade_i, 'sl'])):
                        self.trades.loc[trade_i, 'exit_p'] = close[i]

                        in_trade = False
                        trade_i += 1
                else:
                    if (self.trades.loc[trade_i, 'type'] == 1 and ohlcv.loc[i, self.exit_event] == -1) or \
                            (self.trades.loc[trade_i, 'type'] == -1 and ohlcv.loc[i, self.exit_event] == 1):
                        self.trades.loc[trade_i, 'exit_p'] = close[i]

                        in_trade = False
                        trade_i += 1

    def mutate(self):
        # Mutate the filters string
        mutated_filter_string = list(self.filter_string)
        for i in range(len(mutated_filter_string)):
            if random.random() < self.MUTATION_RATE:
                mutated_filter_string[i] = '1' if mutated_filter_string[i] == '0' else '0'
        self.filter_string = ''.join(mutated_filter_string)

        # Randomly mutate the entry/exit events
        if random.random() < self.MUTATION_RATE:
            self.entry_event = random.choice(self.entry_events)
        if random.random() < self.MUTATION_RATE:
            self.exit_event = random.choice(self.exit_events)


def select_parent(fitness_values):
    # Step 1: Calculate the total fitness
    total_fitness = sum(fitness_values)

    # Step 2: Generate a random value between 0 and the total fitness
    random_value = random.uniform(0, total_fitness)

    # Step 3: Iterate through the fitness values to find the selected parent
    cumulative_sum = 0
    for i, fitness in enumerate(fitness_values):
        cumulative_sum += fitness
        if cumulative_sum >= random_value:
            return i


def crossover(parent1, parent2):
    # Select a random crossover point
    split_point = random.randint(1, len(parent1.filter_string) - 1)  # Avoid splitting at the start or end

    # Create children by combining the filter_strings of the parents
    child1_filter_string = parent1.filter_string[:split_point] + parent2.filter_string[split_point:]
    child2_filter_string = parent2.filter_string[:split_point] + parent1.filter_string[split_point:]

    # Create new Strategy instances for the children
    child1 = Strategy()
    child2 = Strategy()

    child1.filter_string = child1_filter_string
    child2.filter_string = child2_filter_string

    return child1, child2

def run_genetic_algorithm(population_size, generations):
    # Create initial population
    population = [Strategy() for _ in range(population_size)]

    for i in range(generations):
        print(f'Generation {i+1}')

        for j, strategy in enumerate(population):
            print(f'Strategy {j+1}/{len(population)}')

            strategy.data_feed_strategy()
            strategy.find_fitness()

        new_population = []

        fitness_values = [strategy.fitness for strategy in population]

        print(fitness_values)

        sorted_population = sorted(zip(population, fitness_values), key=lambda x: x[1], reverse=True)

        #elitism
        for j in range(ELITISM_COPIES):
            new_population.append(sorted_population[j][0])

        while len(new_population)<population_size:
            parent1 = population[select_parent(fitness_values)]
            parent2 = population[select_parent(fitness_values)]

            child1, child2 = crossover(parent1, parent2)

            child1.mutate()
            child2.mutate()

            new_population.append(child1)
            new_population.append(child2)

        population = new_population[:population_size]

    #Validation
    print("Validating Strategies")

    for i, strategy in enumerate(population):
        print(f'Strategy {i + 1}/{len(population)}')

        strategy.data_feed_strategy(type='validation')
        strategy.find_fitness()

    fitness_values = [strategy.fitness for strategy in population]
    sorted_population = sorted(zip(population, fitness_values), key=lambda x: x[1], reverse=True)

    top_10_strategies = [strategy for strategy, fitness in sorted_population[:10]]

    print('Testing strategies')

    for i, strategy in enumerate(top_10_strategies):
        print(f'Strategy {i + 1}/{len(top_10_strategies)}')

        strategy.data_feed_strategy(type='test')
        strategy.find_fitness()

        try:
            print(f"Win Rate: {strategy.win_rate}")
            print(f"Reward to Risk: {strategy.reward_risk}")
            print(f"Time for 200 Trades: {strategy.time_for_200}")
            print(f"Fitness: {strategy.fitness}")
        except:
            print("Strategy took too long...")