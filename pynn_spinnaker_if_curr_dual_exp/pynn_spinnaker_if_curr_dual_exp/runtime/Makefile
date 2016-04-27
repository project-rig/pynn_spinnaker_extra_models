APP_BUILD_DIRS = $(sort $(dir $(wildcard build/*/)))

all:
	(cd build && "$(MAKE)") || exit $$?
	(cd build && "$(MAKE)" PROFILER_ENABLED=1) || exit $$?

clean:
	(cd build && "$(MAKE)" clean) || exit $$?
	(cd build && "$(MAKE)" clean PROFILER_ENABLED=1) || exit $$?