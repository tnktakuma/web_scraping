from fx_api import FX


def main():
    api = FX(False)
    api.ask()
    api.quit()


if __name__ == '__main__':
    main()
