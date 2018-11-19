try:  # Python 2
    import startup
except ImportError:  # Python 3
    from . import startup


def main():
    startup.run()


if __name__ == '__main__':
    startup.run()
