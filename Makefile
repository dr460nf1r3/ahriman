.PHONY: archive archive_directory archlinux check clean directory push tests version
.DEFAULT_GOAL := archlinux

PROJECT := ahriman

FILES := AUTHORS COPYING CONFIGURING.md README.md package src setup.py
TARGET_FILES := $(addprefix $(PROJECT)/, $(FILES))
IGNORE_FILES := package/archlinux src/.mypy_cache

$(TARGET_FILES) : $(addprefix $(PROJECT), %) : $(addprefix ., %) directory version
	@cp -rp $< $@

archive: archive_directory
	tar cJf "$(PROJECT)-$(VERSION)-src.tar.xz" "$(PROJECT)"
	rm -rf "$(PROJECT)"

archive_directory: $(TARGET_FILES)
	rm -fr $(addprefix $(PROJECT)/, $(IGNORE_FILES))
	find "$(PROJECT)" -type f -name "*.pyc" -delete
	find "$(PROJECT)" -depth -type d -name "__pycache__" -execdir rm -rf {} +
	find "$(PROJECT)" -depth -type d -name "*.egg-info" -execdir rm -rf {} +

archlinux: archive
	sed -i "/sha512sums=('[0-9A-Fa-f]*/s/[^'][^)]*/sha512sums=('$$(sha512sum $(PROJECT)-$(VERSION)-src.tar.xz | awk '{print $$1}')'/" package/archlinux/PKGBUILD
	sed -i "s/pkgver=[0-9.]*/pkgver=$(VERSION)/" package/archlinux/PKGBUILD

check:
	cd src && mypy --implicit-reexport --strict -p "$(PROJECT)"
	find "src/$(PROJECT)" tests -name "*.py" -execdir autopep8 --exit-code --max-line-length 120 -aa -i {} +
	cd src && pylint --rcfile=../.pylintrc "$(PROJECT)"

clean:
	find . -type f -name "$(PROJECT)-*-src.tar.xz" -delete
	rm -rf "$(PROJECT)"

directory: clean
	mkdir "$(PROJECT)"

push: archlinux
	git add package/archlinux/PKGBUILD src/ahriman/version.py
	git commit -m "Release $(VERSION)"
	git push
	git tag "$(VERSION)"
	git push --tags

tests:
	python setup.py test

version:
ifndef VERSION
	$(error VERSION is required, but not set)
endif
	sed -i '/__version__ = "[0-9.]*/s/[^"][^)]*/__version__ = "$(VERSION)"/' src/ahriman/version.py
