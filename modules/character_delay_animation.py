import time
# UTILITY: Display text with a typing effect
def character_delay_animation(string_input, seconds):
    for char in string_input:
        print(char, end="", flush=True)
        time.sleep(seconds)
    print()