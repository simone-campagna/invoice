#!/usr/bin/env python

### From:
### https://gist.github.com/sontek/1508912

__all__ = [
    'set_printer',
    'set_symbols',
    'set_flake_symbols',
    'set_currency_symbols',
    'set_animation',
    'make_it_snow',
]

import os
import random
import time
import platform
 
snowflakes = {}
 
_PRINTER = print
_SYMBOLS = None
_DELAY = 0.1
_DURATION = None

def set_printer(printer):
    global _PRINTER
    _PRINTER = printer

def set_symbols(symbols):
    global _SYMBOLS
    _SYMBOLS = tuple(symbols)

def set_flake_symbols():
    set_symbols(range(0x2740, 0x2749))

def set_currency_symbols():
    set_symbols((0x20A4, 0x20AC, ord('$')))

def set_animation(*, delay, duration):
    global _DELAY_SECONDS
    _DELAY = delay
    global _DURATION
    _DURATION = duration

set_currency_symbols()

try: # pragma: no cover
    # Windows Support
    from colorama import init
    init()
except ImportError: # pragma: no cover
    pass
 
def get_terminal_size(): # pragma: no cover
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            import struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return None
        return cr
 
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
 
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            cr = (25, 80)
    return int(cr[1]), int(cr[0])
 
columns, rows = get_terminal_size()
 
def clear_screen(numlines=100):
    """Clear the console.

    numlines is an optional argument used only as a fall-back.
    """
    if os.name == "posix":
        # Unix/Linux/MacOS/BSD/etc
        os.system('clear')
    elif os.name in ("nt", "dos", "ce"): # pragma: no cover
        # DOS/Windows
        os.system('cls')
    else: # pragma: no cover
        # Fallback for other operating systems.
        _PRINTER('\n' * rows)
 
def get_random_flake():
    if not platform.system() == 'Windows':
        try:
            # python3 support
            try:
                cmd = unichr
            except NameError:
                cmd = chr
 
            flake = cmd(random.choice(_SYMBOLS))
 
            return flake
        except: # pragma: no cover
            pass
 
    return " *"
 
def move_flake(col):
    if snowflakes[col][0]+1 == rows: # pragma: no cover
        snowflakes[col] = [1, get_random_flake()]
    else:
        _PRINTER("\033[%s;%sH  " % (snowflakes[col][0], col))
 
        snowflakes[col][0] += 1
 
        _PRINTER("\033[%s;%sH%s" % (snowflakes[col][0], col, snowflakes[col][1]))
 
        _PRINTER("\033[1;1H")
 
def make_it_snow():
 
    clear_screen()
 
    start_time = time.time()
    try:
        while _DURATION is None or time.time() - start_time < _DURATION:
            col = random.choice(range(1, int(columns)))
     
            # its already on the screen, move it
            if col in snowflakes.keys():
                move_flake(col)
            else:
            # otherwise put it on the screen
                flake = get_random_flake()
                snowflakes[col] = [1, flake]
     
                _PRINTER("\033[%s;%sH%s" % (snowflakes[col][0], col,
                        snowflakes[col][1]))
     
            # key any flakes on the screen moving
            for flake in snowflakes.keys():
                move_flake(flake)
     
            time.sleep(_DELAY)
    except KeyboardInterrupt: # pragma: no cover
        pass
    finally:
        clear_screen()

if __name__ == "__main__":
    main()
