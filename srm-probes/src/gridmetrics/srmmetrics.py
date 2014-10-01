##############################################################################
#
# NAME:        srmmetrics.py
#
# FACILITY:    SAM (Service Availability Monitoring)
#
# COPYRIGHT:
#         Copyright (c) 2009, Members of the EGEE Collaboration.
#         http://www.eu-egee.org/partners/
#         Licensed under the Apache License, Version 2.0.
#         http://www.apache.org/licenses/LICENSE-2.0
#         This software is provided "as is", without warranties
#         or conditions of any kind, either express or implied.
#
# DESCRIPTION:
#
#         Nagios SRM metrics.
#
# AUTHORS:     Konstantin Skaburskas, CERN
#
# CREATED:     21-Nov-2008
#
# NOTES:
#
# MODIFIED:
#    2009-12-07 : Konstantin Skaburskas
#         - using 'gridmon' and 'metrics' packages after merging
#           'gridmonsam' with 'gridmon'
#         - metrics implementation class was moved into the module
##############################################################################

"""
Nagios SRM metrics.

Nagios SRM metrics.

Konstantin Skaburskas <konstantin.skaburskas@cern.ch>, CERN
SAM (Service Availability Monitoring)
"""

import os
import sys
import getopt
import time #@UnresolvedImport
import commands
import errno

try:
    from gridmon import probe
    from gridmon import utils as samutils
    from gridmon import gridutils
    import lcg_util
    import gfal
except ImportError,e:
    summary = "UNKNOWN: Error loading modules : %s" % (e)
    sys.stdout.write(summary+'\n')
    sys.stdout.write(summary+'\nsys.path: %s\n'% str(sys.path))
    sys.exit(3)

# Reasonable defaults for timeouts
LCG_GFAL_BDII_TIMEOUT = 10

LCG_UTIL_TIMEOUT_BDII = LCG_GFAL_BDII_TIMEOUT
LCG_UTIL_TIMEOUT_CONNECT = 10
LCG_UTIL_TIMEOUT_SENDRECEIVE = 120
LCG_UTIL_TIMEOUT_SRM = 180

class SRMMetrics(probe.MetricGatherer) :
    """A Metric Gatherer specific for SRM."""

    # Service version(s)
    svcVers = ['1', '2'] # NOT USED YET
    svcVer  = '2'

    # The probe's author name space
    ns = 'org.sam'

    # Timeouts
    _timeouts = {
                 'srm_connect'      : LCG_UTIL_TIMEOUT_SENDRECEIVE,

                 'ldap_timelimit'   : LCG_GFAL_BDII_TIMEOUT,
                 'LCG_GFAL_BDII_TIMEOUT' : LCG_GFAL_BDII_TIMEOUT,
                 'lcg_util' : {
                               'CLI': {
                                       'connect-timeout'    : LCG_UTIL_TIMEOUT_CONNECT,
                                       'sendreceive-timeout': LCG_UTIL_TIMEOUT_SENDRECEIVE,
                                       'bdii-timeout'       : LCG_UTIL_TIMEOUT_BDII,
                                       'srm-timeout'        : LCG_UTIL_TIMEOUT_SRM },
                               'API': {
                                       'connect-timeout'    : LCG_UTIL_TIMEOUT_CONNECT}
                               }
                  }

    _ldap_url  = "ldap://sam-bdii.cern.ch:2170"

    probeinfo = { 'probeName'      : ns+'.SRM-Probe',
                  'probeVersion'   : '1.0',
                  'serviceVersion' : '1.*, 2.*'}
    # Metrics' info
    _metrics = {
               'GetSURLs' : {'metricDescription': "Get full SRM endpoints and storage areas from BDII.",
                             'cmdLineOptions'   : ['ldap-uri=',
                                                   'ldap-timeout='],
                             'cmdLineOptionsReq' : [],
                             'metricChildren'   : ['LsDir','Put','Ls','GetTURLs','Get','Del']
                             },
               'LsDir'    : {'metricDescription': "List content of VO's top level space area(s) in SRM.",
                             'cmdLineOptions'   : ['se-timeout='],
                             'cmdLineOptionsReq' : [],
                             'metricChildren'   : [],
                             'critical'         : 'Y',
                             'statusMsgs'       : {'OK'      :'OK: Storage Path directory was listed successfully.',
                                                   'WARNING' :'WARNING: Problems listing Storage Path directory.'  ,
                                                   'CRITICAL':'CRITICAL: Problems listing Storage Path directory.' ,
                                                   'UNKNOWN' :'UNKNOWN: Problems listing Storage Path directory.'}
                             },
               'Put'      : {'metricDescription': "Copy a local file to the SRM into default space area(s).",
                             'cmdLineOptions'   : ['se-timeout='],
                             'cmdLineOptionsReq' : [],
                             'metricChildren'   : ['Ls','GetTURLs','Get','Del']
                             },
               'Ls'       : {'metricDescription': "List (previously copied) file(s) on the SRM.",
                             'cmdLineOptions'   : ['se-timeout='],
                             'cmdLineOptionsReq' : [],
                             'metricChildren'   : [],
                             'critical'         : 'Y',
                             'statusMsgs'       : {'OK'      :'OK: File(s) was listed successfully.',
                                                   'WARNING' :'WARNING: Problems listing file(s).'  ,
                                                   'CRITICAL':'CRITICAL: Problems listing file(s).' ,
                                                   'UNKNOWN' :'UNKNOWN: Problems listing file(s).'}
                             },
               'GetTURLs' : {'metricDescription': "Get Transport URLs for the file copied to storage.",
                             'cmdLineOptions'   : ['se-timeout=',
                                                   'ldap-uri=',
                                                   'ldap-timeout='],
                             'cmdLineOptionsReq' : [],
                             'metricChildren'   : [],
                             'critical'         : 'Y'
                             },
               'Get'      : {'metricDescription': "Copy given remote file(s) from SRM to a local file.",
                             'cmdLineOptions'   : ['se-timeout='],
                             'cmdLineOptionsReq' : [],
                             'metricChildren'   : [],
                             'critical'         : 'Y'
                             },
               'Del'      : {'metricDescription': "Delete given file(s) from SRM.",
                             'cmdLineOptions'   : ['se-timeout='],
                             'cmdLineOptionsReq' : [],
                             'metricChildren'   : [],
                             'critical'         : 'Y'
                             },
               'All'      : {'metricDescription': "Run all metrics.",
                             'cmdLineOptions'   : ['srmv='],
                             'cmdLineOptionsReq' : [],
                             'metricsOrder'     : ['GetSURLs','LsDir','Put','Ls','GetTURLs','Get','Del']
                             },
               }


    def __init__(self, tuples, srmtype):

        probe.MetricGatherer.__init__(self, tuples, srmtype)

        self.usage="""    Metrics specific options:

--srmv <1|2>           (Default: %s)

%s
--ldap-uri <URI>       Format [ldap://]hostname[:port[/]]
                       (Default: %s)
--ldap-timeout <sec>   (Default: %i)

%s
--se-timeout <sec>     (Default: %i)

!!! NOT IMPLEMENTED YET !!!
--sapath <SAPath,...>  Storage Area Path to be tested on SRM. Comma separated
                       list of Storage Paths to be tested.

"""%(self.svcVer,
     self.ns+'.SRM-{GetSURLs,GetTURLs}',
     self._ldap_url,
     self._timeouts['ldap_timelimit'],
     self.ns+'.SRM-{LsDir,Put,Ls,GetTURLs,Get,Del}',
     self._timeouts['srm_connect'])

        # TODO: move to super class
        # Need to be parametrized from CLI at runtime
        self.childTimeout = 120 # timeout

        # initiate metrics description
        self.set_metrics(self._metrics)

        # parse command line parameters
        self.parse_cmd_args(tuples)

        # working directory for metrics
        self.make_workdir()

        # LDAP
        self._ldap_base = "o=grid"
        self._ldap_fileEndptSAPath = self.workdir_metric+"/EndpointAndPath"

        # files and patterns
        self._fileTest       = self.workdir_metric+'/testFile.txt'
        self._fileTestIn     = self.workdir_metric+'/testFileIn.txt'
        self._fileFilesOnSRM = self.workdir_metric+'/FilesOnSRM.txt'
        self._fileSRMPattern = 'testfile-put-%s-%s.txt' # time, uuid

        # lcg_util and GFAL versions
        self.lcg_util_gfal_ver = gridutils.get_lcg_util_gfal_ver()

        # lock file
        self._fileLock = self.workdir_metric+'/lock'
        self._fileLock_timelimit = 5*60
        'timelimit on working directory lock'

    def parse_args(self, opts):

        for o,v in opts:
            if o in ('--srmv'):
                if v in self.svcVers:
                    self.svcVer = str(v)
                else:
                    errstr = '--srmv must be one of '+\
                        ', '.join([x for x in self.svcVers])+'. '+v+' given.'
                    raise getopt.GetoptError(errstr)
            elif o in ('--ldap-uri'):
                [host, port] = samutils.parse_uri(v)
                if port == None or port == '':
                    port = '2170'
                self._ldap_url = 'ldap://'+host+':'+port
                os.environ['LCG_GFAL_INFOSYS'] = host+':'+port
            elif o in ('--ldap-timeout'):
                self._timeouts['ldap_timelimit'] = int(v)
            elif o in ('--se-timeout'):
                self._timeouts['srm_connect'] = int(v)

    def __workdir_islocked(self):
        """Check if working directory is locked within allowed timelimit.
        """
        if not os.path.exists(self._fileLock):
            return False
        else:
            delta = time.time() - os.stat(self._fileLock).st_ctime
            if delta >= self._fileLock_timelimit:
                os.unlink(self._fileLock)
                return False
            else:
                return True

    def __workdir_lock(self):
        """Lock working directory.
        """
        if self.__workdir_islocked():
            raise IOError('Working directory is locked: %s' %
                          self.workdir_metric)
        file(self._fileLock, 'w')

    def __workdir_unlock(self):
        """Unlock working directory.
        """
        try: os.unlink(self._fileLock)
        except Exception: pass

    def __query_bdii(self, ldap_filter, ldap_attrlist, ldap_url=''):
        'Local wrapper for gridutils.query_bdii()'

        ldap_url = ldap_url or self._ldap_url
        try:
            tl = self._timeouts['ldap_timelimit']
        except KeyError:
            tl = None
        self.printd('Query BDII.')
        self.printd('''Parameters:
 ldap_url: %s
 ldap_timelimit: %i
 ldap_filter: %s
 ldap_attrlist: %s'''% (ldap_url, tl, ldap_filter, ldap_attrlist))
        self.print_time()
        self.printd('Querying BDII %s' % ldap_url)
        rc, qres = gridutils.query_bdii(ldap_filter, ldap_attrlist,
                                    ldap_url=ldap_url,
                                    ldap_timelimit=tl)
        self.print_time()
        return rc, qres

    def metricGetSURLs(self):
        """Get full SRM endpoint(s) and storage areas from BDII.
        """
        try:
            self.__workdir_lock()
        except Exception, e:
            self.printd('Failed to lock. %s' % str(e))
            return 'UNKNOWN', 'UNKNOWN: Failed to lock working directory.'

        ldap_filter = "(|(&(GlueChunkKey=GlueSEUniqueID=%s)(|(GlueSAAccessControlBaseRule=%s)(GlueSAAccessControlBaseRule=VO:%s)))(&(GlueChunkKey=GlueSEUniqueID=%s)(|(GlueVOInfoAccessControlBaseRule=%s)(GlueVOInfoAccessControlBaseRule=VO:%s))) (&(GlueServiceUniqueID=*://%s*)(GlueServiceVersion=%s.*)(GlueServiceType=srm*)))" % (
                                    self.hostName,self.voName,self.voName,
                                    self.hostName,self.voName,self.voName,
                                    self.hostName,self.svcVer)
        ldap_attrlist = ['GlueServiceEndpoint', 'GlueSAPath', 'GlueVOInfoPath']

        rc, qres = self.__query_bdii(ldap_filter, ldap_attrlist,
                                     self._ldap_url)
        if not rc:
            if qres[0] == 0: # empty set
                sts = 'CRITICAL'
            else: # all other problems
                sts = 'UNKNOWN'
            self.printd(qres[2])
            return (sts, qres[1])

        res = {}
        for k in ldap_attrlist: res[k] = []

        for entry in qres:
            for attr in res.keys():
                try:
                    for val in entry[1][attr]:
                        if val not in res[attr]:
                            res[attr].append(val)
                except KeyError: pass

        # GlueServiceEndpoint is not published
        k = 'GlueServiceEndpoint'
        if not res[k]:
            return ('CRITICAL',
                    "%s is not published for %s in %s" % \
                    (k, self.hostName, self._ldap_url))
        elif len(res[k]) > 1:
            return ('CRITICAL',
                    "More than one SRMv"+self.svcVer+" "+\
                    k+" is published for "+self.hostName+": "+', '.join(res[k]))
        else:
            endpoint = res[k][0]

        self.printd('GlueServiceEndpoint: %s' % endpoint)

        # GlueVOInfoPath takes precedence
        # Ref:  "Usage of Glue Schema v1.3 for WLCG Installed Capacity
        #        information" v 1.9, Date: 03/02/2009
        if res['GlueVOInfoPath']:
            storpaths = res['GlueVOInfoPath']
            self.printd('GlueVOInfoPath: %s' % ', '.join(storpaths))
        elif res['GlueSAPath']:
            storpaths = res['GlueSAPath']
            self.printd('GlueSAPath: %s' % ', '.join(storpaths))
        else:
            # GlueSAPath or GlueVOInfoPath is not published
            return ('CRITICAL',
                    "GlueVOInfoPath or GlueSAPath not published for %s in %s" % \
                    (res['GlueServiceEndpoint'][0], self._ldap_url))

        eps = [ endpoint.replace('httpg','srm',1)+'?SFN='+sp+"\n" for sp in storpaths]
        self.printd('SRM endpoint(s) to test:')
        self.printd('\n'.join(eps).strip('\n'))

        self.printd('Saving endpoints to %s' % self._ldap_fileEndptSAPath, v=2)
        try:
            fp = open(self._ldap_fileEndptSAPath, "w")
            for ep in eps:
                fp.write(ep)
            fp.close()
        except IOError, e:
            try:
                os.unlink(self._ldap_fileEndptSAPath)
            except StandardError: pass
            return ('UNKNOWN', 'IOError: %s' % str(e))

        return ('OK', "Got SRM endpoint(s) and Storage Path(s) from BDII")

    def metricLsDir(self):
        "List content of VO's top level space area(s) in SRM using gfal_ls()."

        status = 'OK'
        summary = ''
        self.printd(self.lcg_util_gfal_ver)

        srms = []
        try:
            for srm in open(self._ldap_fileEndptSAPath, 'r'):
                srms.append(srm.rstrip('\n'))
            if not srms:
                return ('UNKNOWN', 'No SRM endpoints found in %s' %
                                    self._ldap_fileEndptSAPath)
        except IOError, e:
            self.printd('ERROR: %s' % str(e))
            return ('UNKNOWN', 'Error opening local file.')

        req = {'surls'          : srms,
               'defaultsetype'  : 'srmv'+self.svcVer,
               'setype'         : 'srmv'+self.svcVer,
               'timeout'        : self._timeouts['srm_connect'],
               'srmv2_lslevels' : 0,
               'no_bdii_check'  : 1
               }
        self.printd('Using gfal_ls().')
        self.printd('Parameters:\n%s' % '\n'.join(
                        ['  %s: %s' % (x,str(y)) for x,y in req.items()]))
        errmsg = ''
        try:
            (rc, gfalobj, errmsg) = gfal.gfal_init(req)
        except MemoryError, e:
            try: gfal.gfal_internal_free(gfalobj)
            except StandardError: pass
            summary = 'error initialising GFAL: %s' % str(e)
            self.printd('ERROR: %s' % summary)
            return ('UNKNOWN', summary)
        else:
            if rc != 0:
                summary = 'problem initialising GFAL: %s' % errmsg
                self.printd('ERROR: %s' % summary)
                return ('UNKNOWN', summary)

        self.print_time()
        self.printd('Listing storage url(s).')
        try:
            (rc, gfalobj, errmsg) = gfal.gfal_ls(gfalobj)
        except StandardError:
            try: gfal.gfal_internal_free(gfalobj)
            except StandardError: pass
            return ('UNKNOWN', 'problem invoking gfal_ls(): %s' % errmsg)
        else:
            self.print_time()
            if rc != 0:
                try: gfal.gfal_internal_free(gfalobj)
                except StandardError: pass
                em = probe.ErrorsMatching(self.errorDBFile, self.errorTopics)
                er = em.match(errmsg)
                summary = 'problem listing Storage Path(s).'
                if er:
                    if status != 'CRITICAL':
                        status = er[0][2]
                    summary += ' [ErrDB:%s]' % str(er)
                else:
                    status = 'CRITICAL'
                self.printd('ERROR: %s' % errmsg)
                return (status, summary)

        try:
            (rc, gfalobj, gfalstatuses) = gfal.gfal_get_results(gfalobj)
        except StandardError:
            try: gfal.gfal_internal_free(gfalobj)
            except StandardError: pass
            raise
        else:
            summary = ''
            for st in gfalstatuses:
                summary += 'Storage Path[%s]' % st['surl']
                self.printd('Storage Path[%s]' % st['surl'], cr=False)
                if st['status'] != 0:
                    em = probe.ErrorsMatching(self.errorDBFile, self.errorTopics)
                    er = em.match(st['explanation'])
                    if er:
                        if status != 'CRITICAL':
                            status = er[0][2]
                        summary += '-%s [ErrDB:%s];' % (status.lower(), str(er))
                    else:
                        status = 'CRITICAL'
                        summary += '-%s;' % status.lower()
                    self.printd('-%s;\nERROR: %s\n' % (status.lower(), st['explanation']))
                else:
                    summary += '-ok;'
                    self.printd('-ok;')

        try: gfal.gfal_internal_free(gfalobj)
        except StandardError: pass

        return (status, summary)

    def metricPut(self):
        "Copy a local file to the SRM into default space area(s)."

        self.printd(self.lcg_util_gfal_ver)

        # generate source file
        try:
            src_file = self._fileTest
            fp = open(src_file, "w")
            for s in "1234567890": fp.write(s+'\n')
            fp.close()

            # multiple 'SAPath's are possible
            dest_files = []
            fn = self._fileSRMPattern % (str(int(time.time())),
                                         samutils.uuidstr())
            for srmendpt in open(self._ldap_fileEndptSAPath):
                dest_files.append(srmendpt.rstrip('\n')+'/'+fn)
            if not dest_files:
                return ('UNKNOWN', 'No SRM endpoints found in %s' %
                                    self._ldap_fileEndptSAPath)

            fp = open(self._fileFilesOnSRM, "w")
            for dfile in dest_files:
                fp.write(dfile+'\n')
            fp.close()
        except IOError, e:
            self.printd('ERROR: %s' % str(e))
            return ('UNKNOWN', 'Error opening local file.')


        self.printd('Copy file using lcg_cp3().')
        # bug in lcg_util: https://gus.fzk.de/ws/ticket_info.php?ticket=39926
        # SRM types: string to integer mapping
        # TYPE_NONE  -> 0
        # TYPE_SRM   -> 1
        # TYPE_SRMv2 -> 2
        # TYPE_SE    -> 3
        defaulttype = int(self.svcVer)
        srctype     = 0
        dsttype     = defaulttype
        nobdii      = 1
        vo          = self.voName
        nbstreams   = 1
        conf_file   = ''
        insecure    = 0
        verbose     = 0 # if self.verbosity > 0: verbose = 1 # when API is fixed
        timeout     = self._timeouts['srm_connect']
        src_spacetokendesc  = ''
        dest_spacetokendesc = ''

        self.printd('''Parameters:
 defaulttype: %i
 srctype: %i
 dsttype: %i
 nobdi: %i
 vo: %s
 nbstreams: %i
 conf_file: %s
 insecure: %i
 verbose: %i
 timeout: %i
 src_spacetokendesc: %s
 dest_spacetokendesc: %s''' % (defaulttype, srctype,
                      dsttype, nobdii, vo, nbstreams, conf_file or '-',
                      insecure, verbose, timeout,
                      src_spacetokendesc or '-', dest_spacetokendesc or '-'))

        errmsg = ''
        stMsg = 'File was%s copied to SRM.'
        for dest_file in dest_files:
            self.print_time()
            self.printd('Destination: %s' % dest_file)
            try:
                rc, errmsg = \
                    lcg_util.lcg_cp3(src_file, dest_file, defaulttype, srctype,
                                     dsttype, nobdii, vo, nbstreams, conf_file,
                                     insecure, verbose, timeout,
                                     src_spacetokendesc, dest_spacetokendesc)
            except AttributeError, e:
                status = 'UNKNOWN'
                summary = stMsg % ' NOT'
                self.printd('ERROR: %s %s' % (str(e), sys.exc_info()[0]))
            else:
                if rc != 0:
                    em = probe.ErrorsMatching(self.errorDBFile, self.errorTopics)
                    er = em.match(errmsg)
                    if er:
                        status = er[0][2]
                        summary = stMsg % (' NOT')+' [ErrDB:%s]' % str(er)
                    else:
                        status = 'CRITICAL'
                        summary = stMsg % ' NOT'
                    self.printd('ERROR: %s' % errmsg)
                else:
                    status = 'OK'
                    summary = stMsg % ''
            self.print_time()
        return (status, summary)

    def metricLs(self):
        "List (previously copied) file(s) on the SRM."

        self.printd(self.lcg_util_gfal_ver)

        status = 'OK'

        srms = []
        try:
            for sfile in open(self._fileFilesOnSRM, 'r'):
                srms.append(sfile.rstrip('\n'))
        except IOError, e:
            self.printd('ERROR: %s' % str(e))
            return ('UNKNOWN', 'Error opening local file.')

        req = {'surls'          : srms,
               'defaultsetype'  : 'srmv'+self.svcVer,
               'setype'         : 'srmv'+self.svcVer,
               'no_bdii_check'  : 1,
               'timeout'        : self._timeouts['srm_connect'],
               'srmv2_lslevels' : 0
               }
        self.printd('Using gfal_ls().')
        self.printd('Parameters:\n%s' % '\n'.join(
                        ['  %s: %s' % (x,str(y)) for x,y in req.items()]))
        errmsg = ''
        try:
            (rc, gfalobj, errmsg) = gfal.gfal_init(req)
        except MemoryError, e:
            try: gfal.gfal_internal_free(gfalobj)
            except StandardError: pass
            summary = 'error initialising GFAL: %s' % str(e)
            self.printd('ERROR: %s' % summary)
            return ('UNKNOWN', summary)
        else:
            if rc != 0:
                summary = 'problem initialising GFAL: %s' % errmsg
                self.printd('ERROR: %s' % summary)
                return ('UNKNOWN', summary)

        self.print_time()
        self.printd('Listing file(s).')
        errmsg = ''
        try:
            (rc, gfalobj, errmsg) = gfal.gfal_ls(gfalobj)
        except StandardError:
            try: gfal.gfal_internal_free(gfalobj)
            except StandardError: pass
            return ('UNKNOWN', 'problem invoking gfal_ls(): %s' % errmsg)
        else:
            self.print_time()
            if rc != 0:
                try: gfal.gfal_internal_free(gfalobj)
                except StandardError: pass
                em = probe.ErrorsMatching(self.errorDBFile, self.errorTopics)
                er = em.match(errmsg)
                summary = 'problem listing file(s).'
                if er:
                    if status != 'CRITICAL':
                        status = er[0][2]
                    summary += ' [ErrDB:%s]' % str(er)
                else:
                    status = 'CRITICAL'
                self.printd('ERROR: %s' % errmsg)
                return (status, summary)

        try:
            (rc, gfalobj, gfalstatuses) = gfal.gfal_get_results(gfalobj)
        except StandardError:
            try: gfal.gfal_internal_free(gfalobj)
            except StandardError: pass
            raise
        else:
            summary = ''
            for st in gfalstatuses:
                summary += 'listing [%s]' % st['surl']
                self.printd('listing [%s]' % st['surl'], cr=False)
                if st['status'] != 0:
                    em = probe.ErrorsMatching(self.errorDBFile, self.errorTopics)
                    er = em.match(st['explanation'])
                    if er:
                        if status != 'CRITICAL':
                            status = er[0][2]
                        summary += '-%s [ErrDB:%s];' % (status.lower(), str(er))
                    else:
                        status = 'CRITICAL'
                        summary += '-%s;' % status.lower()
                    self.printd('-%s;\nERROR: %s\n' % (status.lower(), st['explanation']))
                else:
                    summary += '-ok;'
                    self.printd('-ok;')

        try: gfal.gfal_internal_free(gfalobj)
        except StandardError: pass

        return (status, summary)

    def metricGetTURLs(self):
        "Get Transport URLs for the file copied to storage."

        self.printd(self.lcg_util_gfal_ver)

        # discover transport protocols
        ldap_filter = "(&(objectclass=GlueSEAccessProtocol)"+\
                        "(GlueChunkKey=GlueSEUniqueID=%s))" % self.hostName
        ldap_attrlist = ['GlueSEAccessProtocolType']

        rc, qres = self.__query_bdii(ldap_filter, ldap_attrlist,
                                     self._ldap_url)
        if not rc:
            if qres[0] == 0: # empty set
                sts = 'WARNING'
            else: # all other problems
                sts = 'UNKNOWN'
            self.printd(qres[2])
            return (sts, qres[1])

        protoBlacklist = ['webdav', 'http', 'https']

        protos = []
        for e in qres:
            proto = e[1]['GlueSEAccessProtocolType'][0]
            if (proto not in protoBlacklist) and (proto not in protos):
                protos.append(proto)

#            if e[1]['GlueSEAccessProtocolType'][0] not in protos:
#                protos.append(e[1]['GlueSEAccessProtocolType'][0])

        if not protos:
            return ('WARNING', "No access protocol types for %s published in %s" % \
                                (self.hostName, self._ldap_url))

        self.printd('Discovered GlueSEAccessProtocolType: %s' % ', '.join(protos))

        src_files = []
        try:
            for sfile in open(self._fileFilesOnSRM, 'r'):
                src_files.append(sfile.rstrip('\n'))
        except IOError, e:
            self.printd('ERROR: %s' % str(e))
            return ('UNKNOWN', 'Error opening local file.')

        # lcg-gt $LCG_UTIL_TIMEOUT -b -D srmv2 -T srmv2 ${SURL} ${prot}
        defaulttype = 'srmv2'
        setype      = 'srmv2'
        timeouts = ''
        for k,v in self._timeouts['lcg_util']['CLI'].items():
            timeouts += '--%s %i ' % (k, v)

        self.printd('Using lcg-gt CLI.')
        _cmd = 'lcg-gt %s -b -D %s -T %s %s %s' % \
                        (timeouts, defaulttype, setype, '%s', '%s')
        self.printd('Command:\n%s' % _cmd % ('<SURL>', '<proto>') )

        ok = []; nok = []
        status = 'OK'
        for src_file in src_files:
            self.printd('=====\nSURL: %s\n-----' % src_file)
            for proto in protos:
                self.print_time()
                errmsg = ''
                try:
                    cmd = _cmd % (src_file, proto)
                    rc, errmsg = commands.getstatusoutput(cmd)
                    rc = os.WEXITSTATUS(rc)
                except Exception, e:
                    status = 'UNKNOWN'
                    self.printd('ERROR: %s\n%s' % (errmsg, str(e)))
                else:
                    if rc != 0:
                        if not proto in nok:
                            nok.append(proto)
                        self.printd('proto: %s - FAILED' % proto)
                        self.printd('error: %s' % errmsg)
                        em = probe.ErrorsMatching(self.errorDBFile, self.errorTopics)
                        er = em.match(errmsg)
                        if er:
                            status = er[0][2]
                        else:
                            status = 'CRITICAL'
                    else:
                        if not proto in ok:
                            ok.append(proto)
                        self.printd('proto: %s - OK' % proto)
                        if not samutils.to_retcode(status) > samutils.to_retcode('OK'):
                            status = 'OK'
                self.print_time()
                self.printd('-----')

        summary = 'protocols OK-[%s]' % ', '.join([x for x in ok])
        if nok:
            summary += ', FAILED-[%s]' % ', '.join([x for x in nok])

        return (status, summary)

    def metricGet(self):
        "Copy given remote file(s) from SRM to a local file."

        self.printd(self.lcg_util_gfal_ver)

        # multiple 'Storage Path's are possible
        src_files = []
        try:
            for sfile in open(self._fileFilesOnSRM, 'r'):
                src_files.append(sfile.rstrip('\n'))
        except IOError, e:
            self.printd('ERROR: %s' % str(e))
            return ('UNKNOWN', 'Error opening local file.')

        dest_file = 'file:'+self._fileTestIn

        self.printd('Get file using lcg_cp3().')
        # bug in lcg_util: https://gus.fzk.de/ws/ticket_info.php?ticket=39926
        # SRM types string to integer mapping
        # TYPE_NONE  -> 0
        # TYPE_SRM   -> 1
        # TYPE_SRMv2 -> 2
        # TYPE_SE    -> 3
        defaulttype = int(self.svcVer)
        srctype     = defaulttype
        dsttype     = 0
        nobdii      = 1
        vo          = self.voName
        nbstreams   = 1
        conf_file   = ''
        insecure    = 0
        verbose     = 0 # if self.verbosity > 0: verbose = 1 # when API is fixed
        timeout     = self._timeouts['srm_connect']
        src_spacetokendesc  = ''
        dest_spacetokendesc = ''

        self.printd('''Parameters:
 defaulttype: %i
 srctype: %i
 dsttype: %i
 nobdi: %i
 vo: %s
 nbstreams: %i
 conf_file: %s
 insecure: %i
 verbose: %i
 timeout: %i
 src_spacetokendesc: %s
 dest_spacetokendesc: %s''' % (defaulttype, srctype,
                      dsttype, nobdii, vo, nbstreams, conf_file or '-',
                      insecure, verbose, timeout,
                      src_spacetokendesc or '-', dest_spacetokendesc or '-'))

        stMsg = 'File was%s copied from SRM.'
        for src_file in src_files:
            self.print_time()
            self.printd('Source: %s' % src_file)
            errmsg = ''
            try:
                rc, errmsg = \
                    lcg_util.lcg_cp3(src_file, dest_file, defaulttype, srctype,
                                     dsttype, nobdii, vo, nbstreams, conf_file,
                                     insecure, verbose, timeout,
                                     src_spacetokendesc, dest_spacetokendesc);
            except Exception, e:
                status = 'UNKNOWN'
                summary = stMsg % ' NOT'
                self.printd('ERROR: %s\n%s' % (errmsg, str(e)))
            else:
                if rc != 0:
                    em = probe.ErrorsMatching(self.errorDBFile, self.errorTopics)
                    er = em.match(errmsg)
                    if er:
                        status = er[0][2]
                        summary = stMsg % (' NOT')+'[ErrDB:%s]' % str(er)
                    else:
                        status = 'CRITICAL'
                        summary = stMsg % ' NOT'
                    self.printd('ERROR: %s' % errmsg)
                else:
                    cmd = '`which diff` %s %s' % (self._fileTest, self._fileTestIn)
                    res = commands.getstatusoutput(cmd)
                    if res[0] == 0:
                        status = 'OK'
                        summary = stMsg % ('')+' Diff successful.'
                    elif res[0] == 256: # files differ
                        status = 'CRITICAL'
                        summary = stMsg % ('')+' Files differ!'
                        self.printd('diff ERROR: %s' % res[1])
                    else:
                        status = 'UNKNOWN'
                        summary = stMsg % ''+' Unknown problem when comparing files!'
                        self.printd('diff ERROR: %s' % res[1])
            self.print_time()

        return(status, summary)

    def metricDel(self):
        "Delete given file(s) from SRM."

        self.printd(self.lcg_util_gfal_ver)

        # TODO: - cleanup of the metric's working directory
        #   (this may go to metricAll() in the superclass)

        # multiple Storage Paths are possible
        src_files = []
        try:
            for sfile in open(self._fileFilesOnSRM, 'r'):
                src_files.append(sfile.rstrip('\n'))
            if not src_files:
                return ('UNKNOWN', 'No files to depete from SRM found in %s' %
                                    self._fileFilesOnSRM)
        except IOError, e:
            self.printd('ERROR: %s' % str(e))
            return ('UNKNOWN', 'Error opening local file.')

        # bug in lcg_util: https://gus.fzk.de/ws/ticket_info.php?ticket=39926
        # SRM types string to integer mapping
        # TYPE_NONE  -> 0
        # TYPE_SRM   -> 1
        # TYPE_SRMv2 -> 2
        # TYPE_SE    -> 3
        defaulttype = int(self.svcVer)
        setype      = defaulttype
        nobdii      = 1
        nolfc       = 1
        aflag       = 0
        se          = ''
        vo          = self.voName
        conf_file   = ''
        insecure    = 0
        verbose     = 0 # if self.verbosity > 0: verbose = 1 # when API is fixed
        timeout     = self._timeouts['srm_connect']

        self.printd('Using lcg_del4().')
        self.printd('''Parameters:
 defaulttype: %i
 setype: %i
 nobdii: %i
 nolfc: %i
 aflag: %i
 se: %s
 vo: %s
 conf_file: %s
 insecure: %i
 verbose: %i
 timeout: %i''' % (defaulttype, setype, nobdii, nolfc, aflag,
                          se or '-', vo, conf_file or '-', insecure,
                          verbose, timeout))

        stMsg = 'File was%s deleted from SRM.'
        for src_file in src_files:
            errmsg = ''
            self.print_time()
            self.printd('Deleting: %s' % src_file)
            try:
                rc, errmsg = \
                    lcg_util.lcg_del4(src_file, defaulttype, setype, nobdii, nolfc, aflag,
                                      se, vo, conf_file, insecure, verbose, timeout);
            except Exception, e:
                status = 'UNKNOWN'
                summary = stMsg % ' NOT'
                self.printd('ERROR: %s\n%s' % (errmsg, str(e)))
            else:
                if rc != 0:
                    em = probe.ErrorsMatching(self.errorDBFile, self.errorTopics)
                    er = em.match(errmsg)
                    if er:
                        status = er[0][2]
                        summary = stMsg % (' NOT')+' [ErrDB:%s]' % str(er)
                    else:
                        status = 'CRITICAL'
                        summary  = stMsg % ' NOT'
                    self.printd('ERROR: %s' % errmsg)
                else:
                    status = 'OK'
                    summary = stMsg % ''
            self.print_time()

        self.__workdir_unlock()
        return(status, summary)
