# Import nessary libraries
import math

import numpy as np
import gymnasium as gym
from gymnasium.envs.toy_text.cliffwalking import CliffWalkingEnv
from gymnasium.error import DependencyNotInstalled
from os import path


# Do not change this class
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3
image_path = path.join(path.dirname(gym.__file__), "envs", "toy_text")


class CliffWalking(CliffWalkingEnv):
    def __init__(self, is_hardmode=True, num_cliffs=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_hardmode = is_hardmode

        # Generate random cliff positions
        if self.is_hardmode:
            self.num_cliffs = num_cliffs
            self._cliff = np.zeros(self.shape, dtype=bool)
            self.start_state = (3, 0)
            self.terminal_state = (self.shape[0] - 1, self.shape[1] - 1)
            self.cliff_positions = []
            while len(self.cliff_positions) < self.num_cliffs:
                new_row = np.random.randint(0, 4)
                new_col = np.random.randint(0, 11)
                state = (new_row, new_col)
                if (
                    (state not in self.cliff_positions)
                    and (state != self.start_state)
                    and (state != self.terminal_state)
                ):
                    self._cliff[new_row, new_col] = True
                    if not self.is_valid():
                        self._cliff[new_row, new_col] = False
                        continue
                    self.cliff_positions.append(state)

        # Calculate transition probabilities and rewards
        self.P = {}
        for s in range(self.nS):
            position = np.unravel_index(s, self.shape)
            self.P[s] = {a: [] for a in range(self.nA)}
            self.P[s][UP] = self._calculate_transition_prob(position, [-1, 0])
            self.P[s][RIGHT] = self._calculate_transition_prob(position, [0, 1])
            self.P[s][DOWN] = self._calculate_transition_prob(position, [1, 0])
            self.P[s][LEFT] = self._calculate_transition_prob(position, [0, -1])

    def _calculate_transition_prob(self, current, delta):
        new_position = np.array(current) + np.array(delta)
        new_position = self._limit_coordinates(new_position).astype(int)
        new_state = np.ravel_multi_index(tuple(new_position), self.shape)
        if self._cliff[tuple(new_position)]:
            return [(1.0, self.start_state_index, -100, False)]

        terminal_state = (self.shape[0] - 1, self.shape[1] - 1)
        is_terminated = tuple(new_position) == terminal_state

        return [(1 / 3, new_state, -0.2, is_terminated)]

    # DFS to check that it's a valid path.
    def is_valid(self):
        frontier, discovered = [], set()
        frontier.append((3, 0))
        while frontier:
            r, c = frontier.pop()
            if not (r, c) in discovered:
                discovered.add((r, c))
                directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
                for x, y in directions:
                    r_new = r + x
                    c_new = c + y
                    if r_new < 0 or r_new >= self.shape[0] or c_new < 0 or c_new >= self.shape[1]:
                        continue
                    if (r_new, c_new) == self.terminal_state:
                        return True
                    if not self._cliff[r_new][c_new]:
                        frontier.append((r_new, c_new))
        return False

    def step(self, action):
        if action not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid action {action}   must be in [0, 1, 2, 3]")

        if self.is_hardmode:
            match action:
                case 0:
                    action = np.random.choice([0, 1, 3], p=[1, 0, 0])
                case 1:
                    action = np.random.choice([0, 1, 2], p=[0, 1, 0])
                case 2:
                    action = np.random.choice([1, 2, 3], p=[0, 1, 0])
                case 3:
                    action = np.random.choice([0, 2, 3], p=[0, 0, 1])

        return super().step(action)

    def _render_gui(self, mode):
        try:
            import pygame
        except ImportError as e:
            raise DependencyNotInstalled(
                "pygame is not installed, run `pip install gymnasium[toy-text]`"
            ) from e
        if self.window_surface is None:
            pygame.init()

            if mode == "human":
                pygame.display.init()
                pygame.display.set_caption("CliffWalking - Edited by Audrina & Kian")
                self.window_surface = pygame.display.set_mode(self.window_size)
            else:  # rgb_array
                self.window_surface = pygame.Surface(self.window_size)
        if self.clock is None:
            self.clock = pygame.time.Clock()
        if self.elf_images is None:
            hikers = [
                path.join(image_path, "img/elf_up.png"),
                path.join(image_path, "img/elf_right.png"),
                path.join(image_path, "img/elf_down.png"),
                path.join(image_path, "img/elf_left.png"),
            ]
            self.elf_images = [
                pygame.transform.scale(pygame.image.load(f_name), self.cell_size)
                for f_name in hikers
            ]
        if self.start_img is None:
            file_name = path.join(image_path, "img/stool.png")
            self.start_img = pygame.transform.scale(
                pygame.image.load(file_name), self.cell_size
            )
        if self.goal_img is None:
            file_name = path.join(image_path, "img/cookie.png")
            self.goal_img = pygame.transform.scale(
                pygame.image.load(file_name), self.cell_size
            )
        if self.mountain_bg_img is None:
            bg_imgs = [
                path.join(image_path, "img/mountain_bg1.png"),
                path.join(image_path, "img/mountain_bg2.png"),
            ]
            self.mountain_bg_img = [
                pygame.transform.scale(pygame.image.load(f_name), self.cell_size)
                for f_name in bg_imgs
            ]
        if self.near_cliff_img is None:
            near_cliff_imgs = [
                path.join(image_path, "img/mountain_near-cliff1.png"),
                path.join(image_path, "img/mountain_near-cliff2.png"),
            ]
            self.near_cliff_img = [
                pygame.transform.scale(pygame.image.load(f_name), self.cell_size)
                for f_name in near_cliff_imgs
            ]
        if self.cliff_img is None:
            file_name = path.join(image_path, "img/mountain_cliff.png")
            self.cliff_img = pygame.transform.scale(
                pygame.image.load(file_name), self.cell_size
            )

        for s in range(self.nS):
            row, col = np.unravel_index(s, self.shape)
            pos = (col * self.cell_size[0], row * self.cell_size[1])
            check_board_mask = row % 2 ^ col % 2
            self.window_surface.blit(self.mountain_bg_img[check_board_mask], pos)

            if self._cliff[row, col]:
                self.window_surface.blit(self.cliff_img, pos)
            if s == self.start_state_index:
                self.window_surface.blit(self.start_img, pos)
            if s == self.nS - 1:
                self.window_surface.blit(self.goal_img, pos)
            if s == self.s:
                elf_pos = (pos[0], pos[1] - 0.1 * self.cell_size[1])
                last_action = self.lastaction if self.lastaction is not None else 2
                self.window_surface.blit(self.elf_images[last_action], elf_pos)

        if mode == "human":
            pygame.event.pump()
            pygame.display.update()
            self.clock.tick(self.metadata["render_fps"])
        else:  # rgb_array
            return np.transpose(
                np.array(pygame.surfarray.pixels3d(self.window_surface)), axes=(1, 0, 2)
            )


def policy_iteration(env, gamma, theta):
    # Initialize the value function
    v = np.zeros(env.nS)

    # Initialize the policy
    policy = np.ones((env.nS, env.nA)) / env.nA

    for state in range (env.nS):
        check = False
        for i in range(10):
            x, y = env.cliff_positions[i]
            s = 12 * x + y
            if s == state:
                check = True
                break
        if not check:
            for action in range(env.nA):
                x = env.P[state][action]
                new_reward = -math.sqrt(math.pow(int(state / 12) - 3, 2) + math.pow(state % 12 - 11, 2))
                y = list(x[0])
                y[2] = new_reward
                x[0] = tuple(y)
                env.P[state][action] = x

    # Repeat until convergence
    while True:
        # Evaluate the current policy
        v_prime = np.zeros(env.nS)

        for state in range(env.nS):
            # Calculate the maximum expected value
            max_v = -np.inf

            for action in range(env.nA):
                # Calculate the expected value given action
                v_action = 0

                for probability, next_state, reward, done in env.P[state][action]:
                    v_action += probability * (reward + gamma * v[next_state])

                # Update the maximum expected value
                if v_action > max_v:
                    max_v = v_action

            # Set the value of state
            v_prime[state] = max_v

        # Calculate the optimal policy
        policy_prime = np.zeros((env.nS, env.nA))

        for state in range(env.nS):
            # Find the action that maximizes the expected value
            max_v = -np.inf
            best_action = -1

            for action in range(env.nA):
                # Calculate the expected value given action
                v_action = 0

                for probability, next_state, reward, done in env.P[state][action]:
                    v_action += probability * (reward + gamma * v_prime[next_state])

                # Update the maximum expected value
                if v_action > max_v:
                    if not (state >= 0) & (state < 12) & (action == 0):
                        if not (state > 35) & (state < 48) & (action == 2):
                            if not (state % 12 == 11) & (action == 1):
                                if not (state % 12 == 0) & (action == 3):
                                    max_v = v_action
                                    best_action = action

            # Set the policy
            policy_prime[state] = best_action

        # Policy improvement step
        delta = np.max(np.abs(policy - policy_prime))

        if delta < theta:
            break

        # Update the policy
        policy = policy_prime

    return policy, v


# Create an environment
env = CliffWalking(render_mode="human")
observation, info = env.reset(seed=30)

gamma = 0.99
theta = 1e-4

policy, v = policy_iteration(env, gamma, theta)

print("Optimal policy:")
print(policy)

# Define the maximum number of iterations
max_iter_number = 1000
done = False
truncated = False
reward = 0
d = 0
Action = policy[observation][0]
for i in range(max_iter_number):
    print("----------------"f'{i}'"----------------")

    while True:
        # Perform the action and receive feedback from the environment
        next_state, reward, done, truncated, info = env.step(Action)
        print(f'{next_state,reward, done, truncated, info}')
        Action = policy[next_state][0]
        if info['prob']== 1.0:
            break
        if done:
            d = d + 1
            env.reset()
            break


print(d)
# Close the environment
env.close()
