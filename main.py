import pygame
import sys
import random

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)       # Snake body
DARK_GREEN = (0, 100, 0)  # Snake head
RED = (255, 0, 0)         # Food
GREY = (100, 100, 100)    # Game Over background
BLUE = (0, 0, 200)        # Main Menu background
GRID_COLOR = (40, 40, 40)

# Difficulty Progression
BASE_FPS = 10
FPS_INCREASE_INTERVAL = 5
FPS_INCREASE_AMOUNT = 1
MAX_FPS = 30

# Pygame Key Constants for Directions (used for input and state)
DIR_UP = pygame.K_UP
DIR_DOWN = pygame.K_DOWN
DIR_LEFT = pygame.K_LEFT
DIR_RIGHT = pygame.K_RIGHT

# Game States
MAIN_MENU = "MAIN_MENU"
PLAYING = "PLAYING"
GAME_OVER = "GAME_OVER"

# File for High Score
HIGH_SCORE_FILE = "highscore.txt"

# --- Global Game Variables ---
snake = None
food = None
score = 0
high_score = 0
game_state = MAIN_MENU
current_fps = BASE_FPS

# --- Pygame Initialization ---
pygame.init()
try:
    pygame.mixer.init() # For sound effects
except pygame.error as e:
    print(f"Warning: pygame.mixer.init() failed: {e}. Sound effects will be disabled.")
    # You could set a global flag here if other parts of your code depend on mixer being available
    # For example: MIXER_INITIALIZED = False (and True in the try block)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Yılan Oyunu") # "Snake Game" in Turkish
clock = pygame.time.Clock()

# --- Fonts ---
title_font = pygame.font.Font(None, 90)
score_font = pygame.font.Font(None, 36)
game_over_font = pygame.font.Font(None, 72)
instruction_font = pygame.font.Font(None, 48)
menu_font = pygame.font.Font(None, 52)
high_score_font = pygame.font.Font(None, 40)

# --- Sound Effects Loading ---
EAT_SOUND_PATH = "assets/sounds/eat.wav"
GAME_OVER_SOUND_PATH = "assets/sounds/game_over.wav"
eat_sound = None
game_over_sound = None

# Only attempt to load sounds if mixer was initialized (or check a flag)
# However, pygame.mixer.Sound() will fail gracefully if mixer is not init,
# but it's cleaner to check. For now, the existing try-except for Sound() is okay.
if pygame.mixer.get_init(): # Check if mixer was successfully initialized
    try:
        eat_sound = pygame.mixer.Sound(EAT_SOUND_PATH)
    except pygame.error as e:
        print(f"Warning: Could not load sound: {EAT_SOUND_PATH} ({e})")
    try:
        game_over_sound = pygame.mixer.Sound(GAME_OVER_SOUND_PATH)
    except pygame.error as e:
        print(f"Warning: Could not load sound: {GAME_OVER_SOUND_PATH} ({e})")
else:
    print("Info: Sound effect loading skipped as pygame.mixer was not initialized.")

# --- High Score Functions ---
def load_high_score():
    global high_score
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            content = f.read().strip()
            if content: # Ensure content is not empty string
                 high_score = int(content)
            else: # If file is empty, treat as 0
                high_score = 0
    except FileNotFoundError: # If file doesn't exist, high score is 0
        high_score = 0
    except ValueError: # If file content is not a valid integer
        high_score = 0
        print(f"Warning: High score file '{HIGH_SCORE_FILE}' contains invalid data. Resetting high score to 0.")

def save_high_score():
    global high_score
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(high_score))
    except IOError: # If file cannot be written to
        print(f"Warning: Could not save high score to '{HIGH_SCORE_FILE}'.")

# --- Game Object Classes ---
class Snake:
    def __init__(self, screen_width, screen_height, grid_size):
        self.grid_size = grid_size
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Initial position: center of the screen
        start_x = (screen_width // 2 // grid_size) * grid_size
        start_y = (screen_height // 2 // grid_size) * grid_size
        self.body = [(start_x, start_y)] # List of (x,y) tuples

        # Direction handling:
        # current_direction_key: The direction intended by the latest valid user input.
        # actual_move_direction_key: The direction the snake actually moved in the last frame. Used for anti-U-turn logic.
        self.current_direction_key = DIR_RIGHT
        self.actual_move_direction_key = DIR_RIGHT

        self.grow_pending = False # Flag to indicate if snake should grow in the next move

        # Movement deltas (dx, dy) are determined by actual_move_direction_key in move()
        self.dx = grid_size
        self.dy = 0

    def move(self):
        # Update actual_move_direction_key to the current intended direction.
        # This is the direction the snake will attempt to move in THIS frame.
        self.actual_move_direction_key = self.current_direction_key

        # Update dx, dy based on the actual direction of movement for this frame
        if self.actual_move_direction_key == DIR_UP: self.dx, self.dy = 0, -self.grid_size
        elif self.actual_move_direction_key == DIR_DOWN: self.dx, self.dy = 0, self.grid_size
        elif self.actual_move_direction_key == DIR_LEFT: self.dx, self.dy = -self.grid_size, 0
        elif self.actual_move_direction_key == DIR_RIGHT: self.dx, self.dy = self.grid_size, 0

        head_x, head_y = self.body[0]
        new_head_x = head_x + self.dx
        new_head_y = head_y + self.dy

        self.body.insert(0, (new_head_x, new_head_y)) # Add new head

        if self.grow_pending:
            self.grow_pending = False # Reset flag
        else:
            self.body.pop() # Remove tail if not growing

    def grow(self):
        self.grow_pending = True

    def draw(self, surface):
        for i, (segment_x, segment_y) in enumerate(self.body):
            rect = pygame.Rect(segment_x, segment_y, self.grid_size, self.grid_size)
            if i == 0: # Head
                pygame.draw.rect(surface, DARK_GREEN, rect)
                pygame.draw.rect(surface, BLACK, rect, 1)

                # Draw eyes based on actual_move_direction_key for consistency
                eye_radius = max(1, self.grid_size // 8)
                eye_offset_x = self.grid_size // 4
                eye_offset_y = self.grid_size // 4

                head_center_x = rect.centerx
                head_center_y = rect.centery

                # Determine eye positions based on the direction the snake last moved
                if self.actual_move_direction_key == DIR_UP:
                    eye1_pos = (head_center_x - eye_offset_x, head_center_y - eye_offset_y)
                    eye2_pos = (head_center_x + eye_offset_x, head_center_y - eye_offset_y)
                elif self.actual_move_direction_key == DIR_DOWN:
                    eye1_pos = (head_center_x - eye_offset_x, head_center_y + eye_offset_y)
                    eye2_pos = (head_center_x + eye_offset_x, head_center_y + eye_offset_y)
                elif self.actual_move_direction_key == DIR_LEFT:
                    eye1_pos = (head_center_x - eye_offset_x, head_center_y - eye_offset_y)
                    eye2_pos = (head_center_x - eye_offset_x, head_center_y + eye_offset_y)
                elif self.actual_move_direction_key == DIR_RIGHT: # Default to right if no direction yet
                    eye1_pos = (head_center_x + eye_offset_x, head_center_y - eye_offset_y)
                    eye2_pos = (head_center_x + eye_offset_x, head_center_y + eye_offset_y)

                pygame.draw.circle(surface, BLACK, eye1_pos, eye_radius)
                pygame.draw.circle(surface, BLACK, eye2_pos, eye_radius)
            else: # Body segments
                pygame.draw.rect(surface, GREEN, rect)
                pygame.draw.rect(surface, BLACK, rect, 1)

    def check_collision_wall(self):
        head_x, head_y = self.body[0]
        return not (0 <= head_x < self.screen_width and 0 <= head_y < self.screen_height)

    def check_collision_self(self):
        head = self.body[0]
        return head in self.body[1:] # Check if head collides with any part of the tail

    def change_direction(self, new_key):
        # Prevent changing to the opposite of the *last actual move direction*
        if new_key == DIR_UP and self.actual_move_direction_key == DIR_DOWN: return
        if new_key == DIR_DOWN and self.actual_move_direction_key == DIR_UP: return
        if new_key == DIR_LEFT and self.actual_move_direction_key == DIR_RIGHT: return
        if new_key == DIR_RIGHT and self.actual_move_direction_key == DIR_LEFT: return

        # If not a direct reversal, update the intended direction
        self.current_direction_key = new_key

class Food:
    def __init__(self, screen_width, screen_height, grid_size, snake_body):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.grid_size = grid_size
        self.position = (0,0) # (x,y) tuple for top-left of the food's grid cell
        self.randomize_position(snake_body) # Initial placement

    def randomize_position(self, snake_body):
        # Loop until a valid position (not on the snake) is found
        while True:
            x = random.randint(0, (self.screen_width // self.grid_size) - 1) * self.grid_size
            y = random.randint(0, (self.screen_height // self.grid_size) - 1) * self.grid_size
            if (x, y) not in snake_body:
                self.position = (x, y)
                return

    def draw(self, surface):
        center_x = self.position[0] + self.grid_size // 2
        center_y = self.position[1] + self.grid_size // 2
        radius = self.grid_size // 2 - 2 # Small padding
        pygame.draw.circle(surface, RED, (center_x, center_y), radius)

# --- UI and Game Flow Helper Functions ---
def display_message(surface, message, font, color, y_offset=0, center_x=True, x_pos=None):
    text_surface = font.render(message, True, color)
    rect = text_surface.get_rect()
    if center_x:
        rect.centerx = SCREEN_WIDTH // 2
    else:
        rect.x = x_pos if x_pos is not None else 10 # Default x if not centered
    rect.centery = (SCREEN_HEIGHT // 2) + y_offset
    surface.blit(text_surface, rect)

def draw_grid(surface, s_width, s_height, g_size, color):
    # Vertical lines
    for x in range(0, s_width, g_size):
        pygame.draw.line(surface, color, (x, 0), (x, s_height))
    # Horizontal lines
    for y in range(0, s_height, g_size):
        pygame.draw.line(surface, color, (0, y), (s_width, y))

def initialize_game_session():
    """Called once at the start of the application."""
    global game_state
    load_high_score()
    game_state = MAIN_MENU

def reset_game():
    """Resets game variables for a new round."""
    global snake, food, score, game_state, current_fps
    snake = Snake(SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE)
    food = Food(SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, snake.body)
    score = 0
    game_state = PLAYING
    # Reset FPS to base, adjusted by score (which is 0 here)
    current_fps = BASE_FPS + (score // FPS_INCREASE_INTERVAL) * FPS_INCREASE_AMOUNT
    current_fps = min(current_fps, MAX_FPS)

# --- Main Game Function ---
def main():
    global snake, food, score, game_state, current_fps, high_score

    initialize_game_session()
    running = True

    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle input based on current game state
            if game_state == MAIN_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s or event.key == pygame.K_RETURN:
                        reset_game()
                    elif event.key == pygame.K_q:
                        running = False
            elif game_state == PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key in [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]:
                        snake.change_direction(event.key)
            elif game_state == GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: # Play Again
                        reset_game()
                    elif event.key == pygame.K_q: # Quit
                        running = False

        # --- Game State Logic & Rendering ---
        if game_state == MAIN_MENU:
            screen.fill(BLUE)
            draw_grid(screen, SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, GRID_COLOR)
            display_message(screen, "Yılan Oyunu", title_font, WHITE, y_offset=-150)
            display_message(screen, f"High Score: {high_score}", high_score_font, WHITE, y_offset=-80)
            display_message(screen, "Press 'S' or Enter to Start", menu_font, WHITE, y_offset=50)
            display_message(screen, "Press 'Q' to Quit", menu_font, WHITE, y_offset=120)

        elif game_state == PLAYING:
            snake.move()

            # Food collision
            if snake.body[0] == food.position:
                snake.grow()
                score += 1
                if eat_sound: eat_sound.play()
                food.randomize_position(snake.body)
                # Update FPS based on new score
                current_fps = BASE_FPS + (score // FPS_INCREASE_INTERVAL) * FPS_INCREASE_AMOUNT
                current_fps = min(current_fps, MAX_FPS)

            # Wall or self collision
            if snake.check_collision_wall() or snake.check_collision_self():
                if game_over_sound: game_over_sound.play()

                if score > high_score: # Check and save new high score
                    high_score = score
                    save_high_score()

                game_state = GAME_OVER
                # print(f"Game Over! Final Score: {score}, High Score: {high_score}") # Debugging

            # Rendering for PLAYING state
            screen.fill(BLACK)
            draw_grid(screen, SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, GRID_COLOR)
            snake.draw(screen)
            food.draw(screen)
            # Score display
            score_text_surface = score_font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text_surface, (10,10))
            # High score display (in-game)
            high_score_ingame_text = score_font.render(f"High: {high_score}", True, WHITE)
            screen.blit(high_score_ingame_text, (SCREEN_WIDTH - high_score_ingame_text.get_width() - 10, 10))

        elif game_state == GAME_OVER:
            screen.fill(GREY)
            draw_grid(screen, SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, GRID_COLOR)
            display_message(screen, "GAME OVER", game_over_font, RED, y_offset=-120)
            display_message(screen, f"Final Score: {score}", instruction_font, WHITE, y_offset=-40)
            display_message(screen, f"High Score: {high_score}", high_score_font, WHITE, y_offset=20)
            display_message(screen, "Press 'R' to Play Again", instruction_font, WHITE, y_offset=100)
            display_message(screen, "Press 'Q' to Quit", instruction_font, WHITE, y_offset=150)

        pygame.display.flip() # Update the full display
        # Control game speed; use BASE_FPS for menus, current_fps for gameplay
        clock.tick(current_fps if game_state == PLAYING else BASE_FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
