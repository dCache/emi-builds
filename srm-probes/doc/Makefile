# Generate documentation for 'gridmetrics' and 'gridmon' packages. 'gridmon' is 
# added as well because 'gridmetrics' heavily realies on it.
#
# Or simply use
# 
# export PYTHOPATH=/path/to/packages
# epydoc --include-log -o html/ --html gridmetrics gridmon
# 
# if generating for pre-installed or separately available packages.

DOCHTML=html
P1=gridmetrics
P2=gridmon
PKGS=$(P1) $(P2)  
$(P2):
	svn co http://www.sysadmin.hep.ac.uk/svn/grid-monitoring/trunk/GridMon/python/$(P2)
doc: $(P2)
	rm -rf $(DOCHTML)
	mkdir -p $(DOCHTML)
	export PYTHONPATH=${PWD}/../src:.; epydoc -v --include-log -o $(DOCHTML) --html $(PKGS)

clean:
	rm -rf $(P2)
