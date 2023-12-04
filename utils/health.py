
def update_health(name: str, value):
    with open(f'/tmp/.health.{name.lower()}', 'w') as f:
        f.write(str(value))
