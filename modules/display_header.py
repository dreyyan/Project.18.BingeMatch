import time
# UTILITY: Display header for the interface /w appropriate formatting
def display_header(title_name, interface_name, symbol, space, is_odd):
    print(f"[ {title_name} ]")
    time.sleep(0.1)
    if is_odd:
        print(((space - 1) * symbol), end='') # Output spacing
    else:
        print((space * symbol), end='')  # Output spacing
    print(f" {interface_name} {(space * symbol)}")
    time.sleep(0.1)