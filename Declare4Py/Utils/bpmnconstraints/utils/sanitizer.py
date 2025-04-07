"""
All code in module is based upon Adrian Rebmann's codebase.
"""

import re

NON_ALPHANUM = re.compile("[^a-zA-Z]")
CAMEL_PATTERN_1 = re.compile("(.)([A-Z][a-z]+)")
CAMEL_PATTERN_2 = re.compile("([a-z0-9])([A-Z])")


class Sanitizer:
    def __init__(self) -> None:
        pass

    def sanitize_label(self, label):
        label = str(label)
        if " - " in label:
            label = label.split(" - ")[-1]
        if "&" in label:
            label = label.replace("&", "and")
        label = label.replace("\n", " ").replace("\r", "")
        label = label.replace("(s)", "s")
        label = label.replace("'", "")
        label = re.sub(" +", " ", label)

        label = NON_ALPHANUM.sub(" ", label)
        label = label.strip()

        label = self.__camel_to_white(label)

        label = re.sub(r"\s{1,}", " ", label)
        return label

    def __camel_to_white(self, label):
        label = CAMEL_PATTERN_1.sub(r"\1 \2", label)
        return CAMEL_PATTERN_2.sub(r"\1 \2", label)
