from discord import Member
from discord.ext.commands import check
from ...discordIds import *


def is_admin(member: Member):
    for role in member.roles:
        if role.id in (TIM, adminRole, 537990081156481025):
            return True
    return False


def is_mod(member: Member):
    for role in member.roles:
        if role.id in (modRole, helperRole):
            return True
    return is_admin(member)


def is_engineer(member: Member):
    for role in member.roles:
        if role.id == engineerRole:
            return True
    return is_mod(member)


def is_mod_check():
    def predicate(ctx):
        return is_mod(ctx.author)
    return check(predicate)


def is_engineer_check():
    def predicate(ctx):
        return is_engineer(ctx.author)
    return check(predicate)


def in_twt():
    def predicate(ctx):
        return ctx.guild.id == 501090983539245061
    return check(predicate)
