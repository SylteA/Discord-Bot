from discord import Member


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
