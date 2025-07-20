import time, sys
# UTILITY: Display formatted error message to the user
def error_message(message, delay_seconds):
    print(f"ERROR: {message}.", end="", flush=True)
    time.sleep(delay_seconds)
    sys.stdout.write('\033[1A') # Move cursor up 1 line
    sys.stdout.write('\r\033[K\n\r\033[K\033[1A') # Clear error input and error message
    sys.stdout.flush()
    