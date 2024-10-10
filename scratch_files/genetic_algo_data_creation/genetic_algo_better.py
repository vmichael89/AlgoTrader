import random
import numpy as np
import pandas as pd
import os
import json

# Genetic algorithm parameters
POPULATION_SIZE = 200
ELITISM_COPIES = 1
NUM_GENERATIONS = 10


class Strategy:
    FILTERS = [
        'RSI3070', 'RSI4060', 'PAB15MA', 'PAB50MA', 'PAB100MA', 'ATRTA', 'ATRTB', 'INDEC',
        'ENGULF', 'HAMMER', 'BIGCAND', 'ADXTA', 'ADXTB', 'HH0', 'HH1', 'LH0', 'LH1',
        'HL0', 'HL1', 'LL0', 'LL1', 'RELVOL'
    ]
    ENTRY_EVENTS = ['TRNDLN72', 'INDEC', 'ENGULF', 'HAMMER', 'MACRS1550', 'MACRS50100', 'PLBCK', 'BLBND']
    EXIT_EVENTS = ['BLBND', 'MACRS1550', 'MACRS50100', 'EX2', 'EX3', 'EX4']

    def __init__(self):
        # self.filter_string = ''.join(random.choices(['0', '1'], weights=[0.8, 0.2], k=len(self.FILTERS)))
        self.filter_string = ''.join(random.choices(['0'], k=len(self.FILTERS)))
        self.entry_event = random.choice(self.ENTRY_EVENTS)
        self.exit_event = random.choice(self.EXIT_EVENTS)
        self.trades = pd.DataFrame()
        self.time_for_200 = 0
        self.took_too_long = False
        self.MUTATION_RATE = 0.05

    def find_fitness(self):
        if self.took_too_long or self.trades.empty:
            self.fitness = 0
            print("Took too long...")
            return

        self.trades['return'] = self.trades.apply(
            lambda row: row['exit_p'] - row['entry_p'] if row['type'] == 1 else row['entry_p'] - row['exit_p'], axis=1
        )

        win_count = (self.trades['return'] > 0).sum()
        total_trades = len(self.trades)
        self.win_rate = win_count / total_trades if total_trades else 0

        pos_return = self.trades[self.trades['return'] > 0]['return'].mean()
        neg_return = self.trades[self.trades['return'] < 0]['return'].mean()
        self.reward_risk = abs(pos_return / neg_return) if neg_return != 0 else 0

        self.expectancy = self.win_rate * self.reward_risk - (1 - self.win_rate)
        self.fitness = max(0, self.expectancy / self.time_for_200)

    def data_feed_strategy(self, feed_type='training'):
        self.trades = pd.DataFrame()
        self.time_for_200 = 0
        date_ranges = {
            'training': ("2014-10-08", "2023-10-08"),
            'validation': ("2023-10-08", "2024-04-08"),
            'test': ("2024-04-08", "2024-10-08")
        }
        start_date, end_date = map(pd.to_datetime, date_ranges[feed_type])
        data_folder = '../../data/data_features'

        while len(self.trades) < 200:
            ticker_file = random.choice(os.listdir(data_folder))
            ohlcv = pd.read_csv(os.path.join(data_folder, ticker_file), parse_dates=['date'], index_col='date')
            ohlcv = ohlcv[(ohlcv.index >= start_date) & (ohlcv.index <= end_date)]

            if len(ohlcv) < 1440:
                continue

            ohlcv_section = ohlcv.iloc[random.randint(0, len(ohlcv) - 1440):].reset_index(drop=True)
            self.run_strategy(ohlcv_section)

            if self.took_too_long:
                break

    def run_strategy(self, ohlcv):
        selected_filters = [self.FILTERS[i] for i in range(len(self.filter_string)) if self.filter_string[i] == '1']
        in_trade, trade_i, close = False, len(self.trades), ohlcv['close'].to_numpy()

        for i, row in ohlcv.iterrows():
            self.time_for_200 += 1

            if len(self.trades) >= 200 or self.time_for_200 >= 100000:
                self.took_too_long = self.time_for_200 >= 100000
                return

            conditions = not selected_filters or all(row[flt] in (1, 2) for flt in selected_filters)
            long_entry = conditions and row[self.entry_event] in (1, 2)
            short_entry = conditions and row[self.entry_event] in (-1, 2)

            if not in_trade and (long_entry or short_entry):
                in_trade = True
                trade_type = 1 if long_entry else -1
                self.trades.loc[trade_i, ['entry_p', 'type']] = [close[i], trade_type]

                if self.exit_event in ["EX2", "EX3", "EX4"]:
                    target_levels = json.loads(row[self.exit_event].replace('nan', 'null'))
                    if target_levels[0] is None:
                        in_trade = False
                        trade_i += 1
                        continue

                    sl, tp = target_levels if trade_type == 1 else target_levels[::-1]
                    self.trades.loc[trade_i, ['sl', 'tp']] = [sl, tp]

            if in_trade:
                trade_type = self.trades.loc[trade_i, 'type']
                exit_condition_met = False

                if self.exit_event in ["EX2", "EX3", "EX4"]:
                    exit_condition_met = (trade_type == 1 and (close[i] >= self.trades.loc[trade_i, 'tp'] or close[i] <= self.trades.loc[trade_i, 'sl'])) or \
                                         (trade_type == -1 and (close[i] <= self.trades.loc[trade_i, 'tp'] or close[i] >=self.trades.loc[trade_i, 'sl']))
                else:
                    exit_condition_met = (trade_type == 1 and ohlcv.loc[i, self.exit_event] == -1) or \
                                         (trade_type == -1 and ohlcv.loc[i, self.exit_event] == 1)

                if exit_condition_met:
                    self.trades.loc[trade_i, 'exit_p'] = close[i]
                    in_trade = False
                    trade_i += 1

    def mutate(self):
        self.filter_string = ''.join(
            '1' if c == '0' else '0' if random.random() < self.MUTATION_RATE else c for c in self.filter_string
        )
        if random.random() < self.MUTATION_RATE:
            self.entry_event = random.choice(self.ENTRY_EVENTS)
        if random.random() < self.MUTATION_RATE:
            self.exit_event = random.choice(self.EXIT_EVENTS)


def select_parent(fitness_values):
    random_value = random.uniform(0, sum(fitness_values))
    cumulative_sum = 0
    for i, fitness in enumerate(fitness_values):
        cumulative_sum += fitness
        if cumulative_sum >= random_value:
            return i


def crossover(parent1, parent2):
    split_point = random.randint(1, len(parent1.filter_string) - 1)
    #
    # print(parent1.filter_string, parent2.filter_string)
    #
    child1, child2 = Strategy(), Strategy()
    child1.filter_string = parent1.filter_string[:split_point] + parent2.filter_string[split_point:]
    child2.filter_string = parent2.filter_string[:split_point] + parent1.filter_string[split_point:]
    #
    # print(child1.filter_string, child2.filter_string)

    return child1, child2


def run_genetic_algorithm(population_size, generations):
    population = [Strategy() for _ in range(population_size)]

    print(population[0].filter_string)

    for gen in range(generations):
        print(f'Generation {gen + 1}')

        for i, strategy in enumerate(population):
            print(f"Strategy {i+1}/{len(population)}")

            strategy.data_feed_strategy()
            strategy.find_fitness()

        fitness_values = [s.fitness for s in population]
        print(fitness_values)

        population = sorted(population, key=lambda s: s.fitness, reverse=True)



        new_population = population[:ELITISM_COPIES]
        while len(new_population) < population_size:
            print(population[0].filter_string)

            parent1, parent2 = population[select_parent(fitness_values)], population[select_parent(fitness_values)]
            child1, child2 = crossover(parent1, parent2)
            child1.mutate()
            child2.mutate()
            new_population.extend([child1, child2])

        population = new_population[:population_size]

    print("Validating Strategies")
    for i, strategy in enumerate(population):
        print(f"Strategy {i + 1}/{len(population)}")
        strategy.data_feed_strategy('validation')
        strategy.find_fitness()

    top_strategies = sorted(population, key=lambda s: s.fitness, reverse=True)[:10]
    print('Testing strategies')
    for i, strategy in enumerate(top_strategies):
        print(f"Strategy {i + 1}/{len(top_strategies)}")

        strategy.data_feed_strategy('test')
        strategy.find_fitness()

        if strategy.took_too_long:
            print("Strategy took too long...")
        else:
            print(f"Win Rate: {strategy.win_rate}")
            print(f"Reward to Risk: {strategy.reward_risk}")
            print(f"Time for 200 Trades: {strategy.time_for_200}")
            print(f"Fitness: {strategy.fitness}")