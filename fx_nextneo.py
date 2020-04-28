import time
import datetime
from collections import deque

import numpy as np

from fx_api import FX


def main(sample=100, dim=30, interval=10):
    if sample < 2 * dim:
        sample = 2 * dim
        print('sample is changed to', 2 * dim)
    with FX() as api:
        mean_rate = 0.
        queue = deque([], maxlen=dim)
        # The first row of the data matrix
        for i in range(dim):
            queue.append(api.get_ask_rate())
            mean_rate = (i * mean_rate + queue[-1]) / (i + 1)
            time.sleep(interval)
        x = []
        y = []
        # The following rows of the data matrix
        for i in range(sample):
            y.append(api.get_ask_rate())
            x.append(queue)
            queue.popleft()
            queue.append(y[-1])
            mean_rate = ((dim - 1) * mean_rate + queue[-1]) / dim
            time.sleep(interval)
        start = time.time()
        # Drop and Fetch data and Predict
        while time.time() - start < 1e4:
            y.append(api.get_ask_rate())
            x.append(queue)
            queue.popleft()
            queue.append(y[-1])
            mean_rate = ((dim - 1) * mean_rate + queue[-1]) / dim
            X = np.array(x) - mean_rate
            Y = np.array(y) - mean_rate
            beta = np.linalg.pinv(X.T @ X) @ X.T @ Y
            y_hat = np.zeros(2 * dim)
            y_hat[:dim] = Y[-dim:]
            for t in range(dim):
                y_hat[dim + t] = beta @ y_hat[t : dim + t]
            argmin = int(np.argmin(y_hat[dim:])) + 1
            argmax = int(np.argmax(y_hat[dim:])) + 1
            now = datetime.datetime.now()
            print(
                'min:',
                now + datetime.timedelta(seconds=interval*argmin),
                round(y_hat[dim + argmin] - Y[-1]))
            print(
                'max:',
                now + datetime.timedelta(seconds=interval*argmax),
                round(y_hat[dim + argmax] - Y[-1]))
            time.sleep(interval)


if __name__ == '__main__':
    main()
