import numpy as np
from tensorflow.keras.layers import Input, Dense, Activation
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
import gym
import random


class DQNAgent:
    def __init__(self, env, policy):

        self.alpha = 0.001  # Learning rate
        self.gamma = 0.99  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.001  # Minimum exploration rate
        self.policy = policy # Policy
        self.replay_buffer = [] # Initialize replay buffer
        self.replay_buffer_max_length = 500 # Maximum length of replay buffer
        self.n_actions = env.action_space.n  # Size of action space
        self.states_size = env.observation_space.shape[0]  # Size of observation space
        self.batch_size = 64  # Batch size


        ### Construct Deep Neural Network
    def _construct_dnn(self, input_size, output_nodes):
        model = Sequential(
            [
                Input(shape=(input_size,)),
                Dense(64, activation='relu'),
                Dense(32, activation='relu'),
                Dense(output_nodes, activation='linear')
            ]
        )
        model.compile(optimizer=Adam(learning_rate=0.1), loss='mse')
        return model

    def select_action(self, model, s, epsilon=0.05):
        if self.policy == 'egreedy':
            # explore action space with probability of epsilon
            if np.random.uniform(0, 1) < epsilon:
                a = np.random.randint(0, self.n_actions)
            # greedy policy with probability 1-epsilon
            else:
                q_predictions = model.predict(s.reshape((1, 4)))[0]  # given a state compute q-values for each action (output of Q_network)
                a = np.argmax(q_predictions)  # choose action that correspond to highest estimated q-value
            return a
        #### Add other behaviour policies

    def epsilon_decay(self, max_episode_length):  # when episode ends, update exploration rate
        epsilon_delta = (self.epsilon - self.epsilon_min) / max_episode_length
        self.epsilon = self.epsilon - epsilon_delta

    def collect_episode(self, s, a, r, s_next, done):
        self.replay_buffer.append({
            'state': s,
            'action': a,
            'reward': r,
            'state_next': s_next,
            'done': done
        })
        # If replay buffer is larger then pre-defined maximum buffer length, remove oldest experience
        if len(self.replay_buffer) > self.replay_buffer_max_length:
            self.replay_buffer.pop(0)

    def train_Qnetwork(self, model):
        batch = random.sample(self.replay_buffer, self.batch_size)
        states = np.zeros((self.batch_size, self.states_size))  # Dim: batch_size x 4
        states_next = np.zeros((self.batch_size, self.states_size))  # Dim: batch_size x 4
        actions, rewards, dones = [], [], []

        for cnt, experience in enumerate(batch):
            states[cnt, :] = experience['state'] # Collect states of all experiences from batch
            states_next[cnt, :] = experience['state_next'] # Collect new states of all experiences from batch
            actions.append(experience['action']) # Collect actions of all experiences from batch
            rewards.append(experience['reward']) # Collect rewards of all experiences from batch
            dones.append(experience['done'])

        output = model.predict(states)  # Dim: batch_size x 2(actions) --> Primary network
        target = model.predict(states_next)  # Dim: batch_size x 2(actions)

        for i in range(self.batch_size):
            if not dones[i]:
                output[i, :][actions[i]] = rewards[i] + self.gamma * np.max(target[i])
            else:
                output[i, :][actions[i]] = rewards[i]

        model.fit(states, output, verbose=0)


def DQN(n_episodes, max_episode_length, policy):
    env_cart = gym.make('CartPole-v1')
    agent = DQNAgent(env_cart, policy)
    q_net = agent._construct_dnn(input_size=agent.states_size, output_nodes=agent.n_actions)
    t_step_total = 0
    rewards = []

    for episode in range(n_episodes):
        s = env_cart.reset()
        rewards_episode = 0
        # Collect episode
        for t in range(max_episode_length):
            a = agent.select_action(q_net, s)
            s_next, r, done, _ = env_cart.step(a)  # State: Box(4), Reward: float, done: Boolean
            rewards_episode += r # Compute reward of the episode
            agent.collect_episode(s, a, r, s_next,done)  # Collect episode: Store experience of each time step within an episode
            t_step_total += 1  # count total number of time steps
            s = s_next

            if done:  # If cart drops, break out of episode
                break

        print(f'Episode: {episode + 1} with exploration rate {agent.epsilon} had reward of {rewards_episode}')
        rewards.append(rewards_episode)  # collect rewards of each episodes
        if agent.epsilon > agent.epsilon_min:
            agent.epsilon_decay(max_episode_length) # Decaying Exploration Rate

        # After finishing an episode, train the Q-network (Q-value function approx.)
        if t_step_total >= agent.batch_size:
            agent.train_Qnetwork(q_net)

    return (rewards)


def test():
    n_episodes = 1000
    max_episode_length = 500

    # Exploration
    policy = 'egreedy'  # 'egreedy' or 'softmax'

    results = DQN(n_episodes, max_episode_length, policy)
    return results


print(test())