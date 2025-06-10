import unittest
import pygame
from main import Snake, Food, SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, GRID_WIDTH, GRID_HEIGHT, DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT

# Minimal Pygame setup if classes rely on it (e.g. for Rect, K_constants)
pygame.init()

class TestSnakeLogic(unittest.TestCase):

    def setUp(self):
        """Set up for each test method."""
        self.snake = Snake(SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE)
        # Default snake starts with 1 segment at center, moving right.
        # For tests needing a longer snake or specific setup, modify self.snake.body and directions here.
        # Example: Start with a 3-segment snake moving right for some tests
        start_x = (SCREEN_WIDTH // 2 // GRID_SIZE) * GRID_SIZE
        start_y = (SCREEN_HEIGHT // 2 // GRID_SIZE) * GRID_SIZE
        self.snake.body = [
            (start_x, start_y),
            (start_x - GRID_SIZE, start_y),
            (start_x - GRID_SIZE * 2, start_y),
        ]
        self.snake.current_direction_key = DIR_RIGHT
        self.snake.actual_move_direction_key = DIR_RIGHT
        # Ensure dx, dy match the direction for the first move if not calling change_direction first
        self.snake.dx = GRID_SIZE
        self.snake.dy = 0


    def test_snake_initialization(self):
        # Test with a freshly initialized snake (as per main.py's Snake.__init__)
        fresh_snake = Snake(SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE)
        self.assertEqual(len(fresh_snake.body), 1) # Default length is 1
        self.assertEqual(fresh_snake.current_direction_key, DIR_RIGHT)
        self.assertEqual(fresh_snake.actual_move_direction_key, DIR_RIGHT)

    def test_snake_move_right(self):
        # Uses the 3-segment snake from setUp
        initial_head_pos = self.snake.body[0] # tuple (x,y)
        self.snake.move()
        expected_head_pos = (initial_head_pos[0] + GRID_SIZE, initial_head_pos[1])
        self.assertEqual(self.snake.body[0], expected_head_pos)
        self.assertEqual(len(self.snake.body), 3)

    def test_snake_move_left(self):
        # Re-initialize for specific direction test
        self.snake.body = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]
        self.snake.current_direction_key = DIR_LEFT
        self.snake.actual_move_direction_key = DIR_LEFT
        # Manually set dx,dy for the first move as move() uses them before updating based on actual_move_direction_key
        self.snake.dx = -GRID_SIZE
        self.snake.dy = 0

        initial_head_pos = self.snake.body[0]
        self.snake.move() # This move will use the dx,dy set above
        expected_head_pos = (initial_head_pos[0] - GRID_SIZE, initial_head_pos[1])
        self.assertEqual(self.snake.body[0], expected_head_pos)

    def test_snake_move_up(self):
        # Uses 3-segment snake from setUp, initially moving RIGHT
        self.snake.change_direction(DIR_UP) # current_direction_key is UP
        self.snake.move() # actual_move_direction_key becomes UP, dx=0, dy=-GRID_SIZE

        initial_head_pos_after_turn = self.snake.body[0]
        self.snake.move() # Second move, should continue UP
        expected_head_pos = (initial_head_pos_after_turn[0], initial_head_pos_after_turn[1] - GRID_SIZE)
        self.assertEqual(self.snake.body[0], expected_head_pos)

    def test_snake_move_down(self):
        self.snake.change_direction(DIR_DOWN)
        self.snake.move()

        initial_head_pos_after_turn = self.snake.body[0]
        self.snake.move()
        expected_head_pos = (initial_head_pos_after_turn[0], initial_head_pos_after_turn[1] + GRID_SIZE)
        self.assertEqual(self.snake.body[0], expected_head_pos)

    def test_snake_grow(self):
        initial_len = len(self.snake.body)
        self.snake.grow()
        self.snake.move()
        self.assertEqual(len(self.snake.body), initial_len + 1)

    def test_wall_collision_right_wall(self):
        # Position snake head at the right wall, moving right
        self.snake.body = [(SCREEN_WIDTH - GRID_SIZE, SCREEN_HEIGHT // 2)]
        self.snake.current_direction_key = DIR_RIGHT
        self.snake.actual_move_direction_key = DIR_RIGHT
        self.snake.dx = GRID_SIZE; self.snake.dy = 0 # Ensure dx/dy are set for the move

        # The head is at SCREEN_WIDTH - GRID_SIZE. A move right will make head_x = SCREEN_WIDTH.
        # Collision is if head_x is NOT < self.screen_width. So head_x == SCREEN_WIDTH is a collision.
        self.snake.move()
        self.assertTrue(self.snake.check_collision_wall())

    def test_wall_collision_left_wall(self):
        self.snake.body = [(0, SCREEN_HEIGHT // 2)]
        self.snake.current_direction_key = DIR_LEFT
        self.snake.actual_move_direction_key = DIR_LEFT
        self.snake.dx = -GRID_SIZE; self.snake.dy = 0

        # Head at 0. Move left makes head_x = -GRID_SIZE.
        # Collision if head_x < 0.
        self.snake.move()
        self.assertTrue(self.snake.check_collision_wall())

    def test_no_wall_collision_center(self):
        # Uses snake from setUp, which is in the center
        self.snake.move()
        self.assertFalse(self.snake.check_collision_wall())

    def test_self_collision(self):
        # Head at (100,100), a tail segment also at (100,100)
        self.snake.body = [
            (100, 100), # Head
            (120, 100),
            (140, 100),
            (100, 100)  # Tail segment at head's current position (simulating a loop)
        ]
        self.assertTrue(self.snake.check_collision_self())

    def test_no_self_collision_straight_snake(self):
        # Uses snake from setUp (3 segments, straight line)
        self.assertFalse(self.snake.check_collision_self())

    def test_change_direction_valid(self):
        self.snake.actual_move_direction_key = DIR_RIGHT # Assume last move was right
        self.snake.change_direction(DIR_UP)
        self.assertEqual(self.snake.current_direction_key, DIR_UP)

    def test_prevent_reverse_direction_right_to_left(self):
        self.snake.actual_move_direction_key = DIR_RIGHT
        self.snake.current_direction_key = DIR_RIGHT # Current intention is also right

        self.snake.change_direction(DIR_LEFT) # Attempt to reverse
        self.assertEqual(self.snake.current_direction_key, DIR_RIGHT) # Should remain RIGHT

    def test_prevent_reverse_direction_up_to_down(self):
        self.snake.actual_move_direction_key = DIR_UP
        self.snake.current_direction_key = DIR_UP

        self.snake.change_direction(DIR_DOWN)
        self.assertEqual(self.snake.current_direction_key, DIR_UP)

class TestFoodLogic(unittest.TestCase):
    def setUp(self):
        # Need a snake for food initialization context
        self.snake_body_for_food = [(100,100), (80,100)]

    def test_food_creation_and_initial_position(self):
        food = Food(SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, self.snake_body_for_food)
        self.assertIsNotNone(food.position)
        self.assertTrue(0 <= food.position[0] < SCREEN_WIDTH)
        self.assertTrue(0 <= food.position[1] < SCREEN_HEIGHT)
        self.assertEqual(food.position[0] % GRID_SIZE, 0) # Check if aligned to grid
        self.assertEqual(food.position[1] % GRID_SIZE, 0)
        self.assertNotIn(food.position, self.snake_body_for_food) # Check it didn't spawn on snake

    def test_food_randomize_position(self):
        food = Food(SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, self.snake_body_for_food)
        initial_pos = food.position

        # Create a nearly full snake body to make it harder for food to spawn
        # but still leave one spot open.
        full_snake_body = []
        open_spot_x, open_spot_y = -1,-1

        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                if r == 0 and c == 0: # Leave one spot open at (0,0)
                    open_spot_x = c * GRID_SIZE
                    open_spot_y = r * GRID_SIZE
                else:
                    full_snake_body.append((c * GRID_SIZE, r * GRID_SIZE))

        food.randomize_position(full_snake_body)
        self.assertNotIn(food.position, full_snake_body)
        # If the only open spot was chosen, this will pass
        # This also implicitly tests that randomize_position can find a spot if one exists
        # (though it might be slow if only one spot is open on a large grid)
        self.assertEqual(food.position, (open_spot_x, open_spot_y))


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    pygame.quit() # Clean up Pygame after tests
