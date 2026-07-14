.PHONY: test validate-examples wheel

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

validate-examples:
	@for file in examples/*.json; do \
		PYTHONPATH=src python -m mesbg_probability validate $$file >/dev/null || exit 1; \
	done

wheel:
	python -m pip wheel . --no-deps --no-build-isolation -w dist
