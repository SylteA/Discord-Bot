
---

# Contributing

## Setup Discord Application

Refer to the official discord.py [documentation](https://discordpy.readthedocs.io/en/stable/discord.html) to create a bot.

## Project Setup & Installation

1. Fork the repository to your own profile.
2. Set up a local PostgreSQL database or use [Docker](#Docker-Setup).

   ```postgresql://username:password@localhost/db_name```

   Replace username, password, db_name with appropriate values.

3. Run migrations.

   ```python cli.py migrate up```

4. To install packages, run:

   ```bash
   pip install poetry
   poetry install
   ```

5. Create a .env file and copy the contents of example.env, setting up the environment variables.

6. Once the above steps are done, run the bot using the command:

   ```bash
   python cli.py
   ```

7. Feel free to join the server in case of any issues.

## Docker-Setup

1. Ensure you have Docker installed and set up on your system. Refer to the [Docker's official guide](https://docs.docker.com/get-started/overview/) if needed.
2. To run a PostgreSQL instance, execute:

   ```bash
   docker compose up -d postgres
   ```
   The `-d` flag runs the instance in detached mode.

3. Run migrations.

   ```python cli.py migrate up```
# Guidelines

Please adhere to the following guidelines when contributing:

- Follow the coding style and conventions used in the project.
- Write clear and concise commit messages.
- Test your changes thoroughly before submitting a pull request.
- Be respectful and constructive in all interactions with other contributors.

## Code Quality and Testing

- Ensure your code follows best practices and is well-documented.
- Write unit tests for new features and ensure existing tests pass.
- Perform code reviews and address feedback from other contributors.
