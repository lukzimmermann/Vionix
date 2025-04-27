from celery import Celery
from time import sleep
app = Celery("tasks", broker="redis://localhost:6379")

@app.task
def process(x,y):
    for i in range(100):
        sleep(1)
        print("Processing...")
    return x+y

def main():
    print("Hello, world!")



if __name__ == "__main__":
    main()
