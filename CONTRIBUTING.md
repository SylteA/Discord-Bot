

# Contributing

## Setup Discord application
Create a new Discord application [here](https://discord.com/developers/applications) by clicking the `New application` button and name it whatever you want.

![New application](https://cdn.discordapp.com/attachments/721750194797936823/794646477505822730/unknown.png)

Go to the Bot section on the right-hand side and click on Add Bot.

![Add Bot](https://cdn.discordapp.com/attachments/852867509765799956/853984486970359838/unknown.png)

Copy the bot token (to be used in .env file when setting up project)

![Token](https://cdn.discordapp.com/attachments/852867509765799956/853985222127124500/unknown.png)


To Invite the bot to your server go to Oauth2 select bot then select administrator and go to the link
![Invite Bot](https://cdn.discordapp.com/attachments/852867509765799956/853985694183850004/unknown.png)


## Project Setup & Installation

1. Fork the repository to your own profile.
2. Setup postgresql DB
```postgresql://username:password@localhost/db_name```
Replace username, password, db_name with appropriate values
3. Run migrations  
```python cli.py migrate up```
4. To install packages run:-

    ```pip install poetry```  
    ```poetry install```
5. Create a .env file and copy the contents of example.env, setup the env vars.

6. Once above steps are done, run the bot using command  
   ```python cli.py```
7. Feel free to join the server in case of any issues.

## Guidelines

Please keep the following guidelines in mind when contributing:

- Follow the coding style and conventions used in the project.
- Write clear and concise commit messages.
- Test your changes thoroughly before submitting a pull request.
- Be respectful and constructive in all interactions with other contributors.
