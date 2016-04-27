APP_BUILD_DIRS = $(sort $(dir $(wildcard build/*/)))

all:
	(cd build && "$(MAKE)") || exit $$?
	(cd build && "$(MAKE)" PROFILER_ENABLED=1) || exit $$?

clean: $(APP_BUILD_DIRS)
	for d in $(APP_BUILD_DIRS); do (cd $$d; "$(MAKE)" clean) || exit $$?; done
	for d in $(APP_BUILD_DIRS); do (cd $$d; "$(MAKE)" clean PROFILER_ENABLED=1) || exit $$?; done
