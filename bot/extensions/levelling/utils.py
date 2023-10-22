from bisect import bisect

required_xp = [0]

for lvl in range(1001):
    xp = 5 * (lvl**2) + (50 * lvl) + 100
    required_xp.append(xp + required_xp[-1])


def get_level_for_xp(user_xp: int) -> int:
    return bisect(required_xp, user_xp) - 1


def get_xp_for_level(level: int) -> int:
    return required_xp[level]
