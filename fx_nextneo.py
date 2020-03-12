from fx_api import FX


def main():
    with FX() as api:
        print(api.get_ask_rate())
        print(api.get_bid_rate())
        api.order_ask()


if __name__ == '__main__':
    main()
