import collections
import typing
from collections import defaultdict


class Subdomains:
    plain_domains: set[str]
    domains_by_levels: tuple[tuple[int, list[tuple[str, ...]]], ...]

    def __init__(self, domains: typing.Sequence[str]):
        self.plain_domains = set()

        tmp_level_with_dom: defaultdict[int, list[tuple[str, ...]]] = collections.defaultdict(list)
        for d in map(self.normalize_domain, domains):
            if d.startswith("."):
                level, parts = self.get_level(d)
                tmp_level_with_dom[level].append(parts)
            else:
                self.plain_domains.add(d)
        # Ensure sorted by level
        self.domains_by_levels = tuple((key, tmp_level_with_dom[key]) for key in sorted(tmp_level_with_dom.keys()))

    def exists(self, domain_name: str) -> bool:
        domain_name = self.normalize_domain(domain_name)
        if domain_name in self.plain_domains:
            return True

        level: int
        parts: tuple[str, ...]
        level, parts = self.get_level(domain_name)

        domains: list[tuple[str, ...]]
        for known_level, domains in self.domains_by_levels:
            if known_level > level:
                # Do not search in upper domains
                # This means nothing could be found since search is from lower to upper
                return False

            dom: tuple[str, ...]
            for dom in domains:
                if parts[:known_level] == tuple(dom):
                    return True

        return False

    @staticmethod
    def get_level(domain_name: str) -> tuple[int, tuple[str, ...]]:
        parts = domain_name.strip(".").split(".")
        return len(parts), tuple(reversed(parts))

    @staticmethod
    def normalize_domain(domain_name: str) -> str:
        return domain_name.lower()


def test() -> None:
    sd = Subdomains([".very.long.domain.name", "android.com", ".google.com", "editorconfig.org"])
    assert sd.exists("test.google.com")
    assert not sd.exists("test.android.com")
    assert sd.exists("EditorConfig.org")


if __name__ == "__main__":
    test()
