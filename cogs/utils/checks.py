from discord import Member
from discord.ext.commands import check

from config import ADMIN_ROLES_ID, ENGINEER_ROLE_ID, GUILD_ID, STAFF_ROLE_ID


def is_admin(member: Member):
    for role in member.roles:
        if role.id in ADMIN_ROLES_ID:
            return True

    return False


def is_staff(member: Member):
    for role in member.roles:
        if role.id == STAFF_ROLE_ID:
            return True

    return False


def is_engineer(member: Member):
    for role in member.roles:
        if role.id == ENGINEER_ROLE_ID:
            return True

    return is_staff(member)


def is_staff_check():
    def predicate(ctx):
        return is_staff(ctx.author)

    return check(predicate)


def is_engineer_check():
    def predicate(ctx):
        return is_engineer(ctx.author)

    return check(predicate)


def in_twt():
    def predicate(ctx):
        return ctx.guild.id == GUILD_ID

    return check(predicate)
