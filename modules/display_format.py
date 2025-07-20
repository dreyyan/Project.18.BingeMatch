import time
# UTILITY: Display formatted line
def display_format(character, length):
    for i in range(1, length + 1):
        print(character, end='')
    print() # Print newline
    time.sleep(0.1)