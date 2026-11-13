import time
import threading
from collections import defaultdict


class RateLimiter:

    def __init__(self, limit=5, window=60):
        self.limit = limit
        self.window = window

        self.user_req = defaultdict(
            lambda: {
                "prev": 0,
                "cur": 0,
                "window": None
            }
        )

        self.user_locks = defaultdict(threading.Lock)
        self.global_lock = threading.Lock()

    def allow_request(self, user_id):

        # Get or create a lock for this user
        with self.global_lock:
            lock = self.user_locks[user_id]

        # Protect this user's counters
        with lock:

            now = time.time()

            cur_w = int(now // self.window)
            elapsed = now % self.window

            data = self.user_req[user_id]

            # First request
            if data["window"] is None:
                data["window"] = cur_w

            # New time window
            elif cur_w != data["window"]:

                if cur_w == data["window"] + 1:
                    data["prev"] = data["cur"]
                else:
                    data["prev"] = 0

                data["cur"] = 0
                data["window"] = cur_w

            # Calculate weighted request count
            prev_weight = (
                self.window - elapsed
            ) / self.window

            estimated_count = (
                data["prev"] * prev_weight
                + data["cur"]
            )

            # Reject if limit reached
            if estimated_count >= self.limit:
                return False

            # Allow request
            data["cur"] += 1

            return True


# Example usage

limiter = RateLimiter(limit=5, window=60)

for i in range(7):

    allowed = limiter.allow_request("user1")

    if allowed:
        print(f"Request {i+1}: ALLOWED")
    else:
        print(f"Request {i+1}: REJECTED")


print(limiter.allow_request("user2"))  # Independent user
