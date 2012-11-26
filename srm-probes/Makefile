SITE=org.sam
PKG1=gridmetrics
PKG2=${PKG1}/jobmonit

SPECFILE=grid-monitoring-probes-${SITE}.spec
PROBES=src/SRM-probe src/CE-probe src/CREAMCE-probe src/CREAMCEDJS-probe \
	src/WN-probe src/WMS-probe src/wnjob src/sam src/T-probe src/LFC-probe
WRAPPERS=src/nagtest-run src/samtest-run
CONFS=src/etc/org.sam.conf
FILES=CHANGES setup.py README
MODS1=src/$(PKG1)/__init__.py \
    src/$(PKG1)/cemetrics.py \
    src/$(PKG1)/wmsmetrics.py \
    src/$(PKG1)/srmmetrics.py \
    src/$(PKG1)/wnmetrics.py \
    src/$(PKG1)/creammetrics.py \
    src/$(PKG1)/lfcmetrics.py \
    src/$(PKG1)/threadpool.py \
    src/$(PKG1)/utils.py \
    src/$(PKG1)/scheduler.py
MODS2=src/$(PKG2)/__init__.py \
    src/$(PKG2)/jdl.py

rpmtopdir := $(shell rpm --eval %_topdir)
rpmbuild  := $(shell [ -x /usr/bin/rpmbuild ] && echo rpmbuild || echo rpm)

PKGNAME = $(shell grep -s '^Name:'    $(SPECFILE) | sed -e 's/Name: *//')
PKGVERS = $(shell grep -s '^Version:' $(SPECFILE) | sed -e 's/Version: *//')

distdir = dist/$(PKGNAME)-$(PKGVERS)


dist: $(SPECFILE) $(PROBES) $(WRAPPERS) $(CONFS) $(FILES) $(MODS1) $(MODS2) 
	mkdir -p $(distdir)/usr/libexec/grid-monitoring/probes/$(SITE)
	cp -rpf $(PROBES) $(distdir)/usr/libexec/grid-monitoring/probes/$(SITE)
	cp -rpf $(WRAPPERS) $(distdir)/usr/libexec/grid-monitoring/probes/$(SITE)
	mkdir -p $(distdir)/etc/gridmon
	cp -f $(CONFS) $(distdir)/etc/gridmon
	mkdir -p $(distdir)/$(PKG1) $(distdir)/$(PKG2)
	cp -f $(MODS1) $(distdir)/$(PKG1)
	cp -f $(MODS2) $(distdir)/$(PKG2)
	cp -f $(FILES) $(distdir)
	find $(distdir) -path '*svn*' -prune -exec rm -rf {} \;
	find $(distdir) -path '.*swp' -prune -exec rm -rf {} \;

bldprep: dist $(SPECFILE)
	@mkdir -p $(rpmtopdir)/{SOURCES,SPECS,BUILD,SRPMS,RPMS}
	@cd dist && tar cfz $(rpmtopdir)/SOURCES/$(PKGNAME)-$(PKGVERS).tgz \
	                                               $(PKGNAME)-$(PKGVERS)/*
	@cp -f $(SPECFILE) $(rpmtopdir)/SPECS/$(SPECFILE)

srpm: bldprep dist $(SPECFILE)
	$(rpmbuild) -bs $(SPECFILE)

srpmel4: bldprep dist $(SPECFILE)
	$(rpmbuild) -bs --define 'dist .el4' $(SPECFILE)

srpmel5: bldprep dist $(SPECFILE)
	$(rpmbuild) -bs --define 'dist .el5' $(SPECFILE)

srpms: srpmel4 srpmel5

rpmel4: bldprep dist $(SPECFILE)
	$(rpmbuild) --define 'dist .el4' -ba $(SPECFILE)	

rpmel5: bldprep dist $(SPECFILE)
	$(rpmbuild) --define 'dist .el5' -ba $(SPECFILE)

rpm: rpmel4 rpmel5 

sources: dist
	cd dist && tar -zcvf ../$(PKGNAME)-$(PKGVERS).tgz $(PKGNAME)-$(PKGVERS)/
	rm -rf dist

test:
	cd tests && make test

clean:
	rm -rf dist
	rm -rf $(PKGNAME)-$(PKGVERS).tgz
