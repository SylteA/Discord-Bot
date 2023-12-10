import os


def update_health(name: str, value: bool):
    path = f"/tmp/.health.{name.lower()}"

    with open(path, "w") as f:
        f.write(str(value))
    # checking after to avoid making sure the file exists
    if not value:
        os.remove(path)
