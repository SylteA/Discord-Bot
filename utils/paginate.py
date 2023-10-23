import typing as t


def by_lines(content: str, max_page_size: int) -> t.Generator[str, None, None]:
    current_page = ""

    for line in content.splitlines(keepends=True):
        if len(current_page) + len(line) > max_page_size:
            yield current_page
            current_page = ""

        current_page += line

    if current_page:
        yield current_page
