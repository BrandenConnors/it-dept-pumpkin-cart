# Editable design sources

CadQuery 2.7 generators are retained by subsystem, with STEP outputs where available. Core-only reference assembly predates the R2/HF2/SR1 replacements and is not the complete current cart. Use the root assembly image and master guide for the current configuration.

Create a virtual environment, install `requirements.txt`, then run the desired `CAD/build_*.py` file. Each script writes STL/CAD/Guides alongside its own CAD directory, leaving the curated top-level Parts tree unchanged. Scripts may take several minutes. Parent subsystem directories already exist.

Core generation also exports the original bed, roof, hood carrier and 20 mm spacers. These are historical module outputs, NOT current release parts. Select current replacements according to the root README. Never copy all regenerated core STL files over the curated release.

Core individual STEP files were not originally exported; the source and Core_Only_Reference_Assembly.step preserve their geometry. Other current component STEP files accompany the corresponding STL folders under Parts. Historical check JSON describes CAD checks at generation time; the October 19 assembly report is separately recorded in release notes.

No dependency on the original workspace is required by these generators. Geometry was not changed during packaging. Documentation sources are not required to print or assemble the kit.
