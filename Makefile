.PHONY: all
all:


.PHONY: format
format: format-black

.PHONY: format-black
format-black:
	python -m black --line-length=120 .
