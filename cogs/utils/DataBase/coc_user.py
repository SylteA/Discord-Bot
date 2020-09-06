class CocUser:
    discord_id: int
    coc_id: str
    wins: int

    def __repr__(self):
        return (f"<CocUser discord_id={repr(self.discord_id)} "
                f"coc_id={repr(self.coc_id)} wins={repr(self.wins)}>")
