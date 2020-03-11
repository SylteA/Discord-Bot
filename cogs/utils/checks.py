from discord import Member
from discord.ext.commands import check


def is_admin(member: Member):
    for role in member.roles:
        if role.id in (511334601977888798, 580911082290282506, 537990081156481025):
            return True
    return False


def is_mod(member: Member):
    for role in member.roles:
        if role.id in (511332506780434438, 541272748161499147):
            return True
    return is_admin(member)

def is_mod_check():
    def predicate(ctx):
        return is_mod(ctx.author)
    return check(predicate)

def in_twt():
    def predicate(ctx):
        return ctx.guild.id == 501090983539245061
    return check(predicate)
