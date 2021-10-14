# --- Global vars ---
BASE_DIR := `pwd`

DOC_DIR := doc
ASSETS_DIR := $(DOC_DIR)/assets
ASSETS := $(shell find $(ASSETS_DIR) -type f -not -path '*/\.*')
DOCUMENT := $(DOC_DIR)/presentation.adoc

BUILD_DIR := build
PDF := $(BUILD_DIR)/presentation.pdf
HTML := $(BUILD_DIR)/presentation.html

CP := cp -r
RM := rm -r
CHROME_EXEC := "/Applications/Internet/Browsers/Google Chrome.app/Contents/MacOS/Google Chrome"


# --- Targets ---
.PHONY: build
build: $(HTML)

$(HTML): $(DOCUMENT) $(ASSETS)
	@asciidoctor-revealjs -r asciidoctor-diagram $(DOCUMENT) -o $(HTML)
	@$(CP) $(ASSETS_DIR) $(BUILD_DIR)

.PHONY: clean
clean:
	@$(RM) $(BUILD_DIR)

.PHONY: rebuild
rebuild: clean build


.PHONY: slideshow
slideshow: $(HTML)
	@open -a $(CHROME_EXEC) $(HTML)



# -- PDF export --
# Manual way: Open presentation in browser + append `?print-pdf` to URL -> Print
.PHONY: pdf
pdf: $(PDF)

$(PDF): $(HTML)
	@decktape -s 3200x1800 --chrome-path=$(CHROME_EXEC) \
		reveal "file:///$(BASE_DIR)/$(HTML)?fragments=true" $(PDF)
