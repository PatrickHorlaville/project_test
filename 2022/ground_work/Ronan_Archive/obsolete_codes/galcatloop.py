#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue May 30 11:32:30 2017

@author: rkerr31
"""
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate as scp
import matplotlib.animation as animation

Omega_M = 0.25
h       = 0.7
rhomean = 2.775E11*Omega_M*(h**2)
pixbm   = 1./2            #in arcminutes
amtdeg  = 1./60           #convert arcmin to degrees
dgtrad  = np.pi/180.      #convert degrees to radians
nzbins  = 100000.          #number of redshift bins 
c       = 2.998E5
del_mf  = 1.0
alpha   = 1.37
beta    = -1.74
nuco    = 115.3
amtsr   = 8.461595e-8     #convert arcmin**2 to steradians
G       = 6.67E-11
mpctm   = 3.086E22
convfac = 2.63083e-6
mnz     = 2.4
mxz     = 3.4
##LOAD##DATA####################################################################
data = np.load('fullcatvhrmc.npy')
print "start list generation"
X   = data[:,0]
print '1'
Y   = data[:,1]
print '2'
Z   = data[:,2]
print '3'
R   = np.sqrt(X**2+Y**2+Z**2)
print '7'
M   = data[:,3]
VR  = data[:,4]
RH  = ((3*M)/(4*np.pi*rhomean))**(1./3)
S   = (np.sqrt(4.0/9*np.pi*G*rhomean*6.7702543e-38)*RH*mpctm)/1000.
print 'done'
pntanx  = -4.049
pntany  = 3.236
pbrad   = pixbm*amtdeg*dgtrad  #pixel beam in radians 

print 'rs start' 
za=np.linspace(0,4,1000)
def hubble(za):
    return h*100*np.sqrt(Omega_M*(1+za)**3+1-Omega_M)
def drdz(za):
    return 3e5 / hubble(za)
ra  = np.cumsum(drdz(za)*(za[1]-za[0]))
ra -= ra[0]
z_to_r = scp.interpolate.interp1d(za,ra)
r_to_z = scp.interpolate.interp1d(ra,za)

rs = r_to_z(R)
print "rs done"
def vcorr(rs, vr):
        znew = ((1+rs)*(1+(vr/c)))-1
        return znew
print "vcorr start"
rsvc = vcorr(rs, VR)
print "done"
print "distance filter"
cond1 = (rsvc < mxz) & (rsvc > mnz)
M    = M[cond1]
X    = X[cond1]
Y    = Y[cond1]
Z    = Z[cond1]
R    = R[cond1]
VR   = VR[cond1]
S    = S[cond1]
RSVC = rsvc[cond1]
print "done"
bins   = np.linspace(np.min(RSVC), np.max(RSVC), nzbins+1)
binctr = (bins[:-1] + bins[1:]) / 2
         
def pltdata(pntx, pnty):
    slope   = np.tan(pbrad/2)      #slope of beam relative to beam centre
    bmctrx  = np.tan(pntx*dgtrad)
    bmctry  = np.tan(pnty*dgtrad)
    cond2 = (X > (bmctrx-slope)*Z) & (X< (bmctrx+slope)*Z) & (Y>(bmctry-slope)*Z) & (Y< (bmctry+slope)*Z)
    print pntx, pnty
    ML     = M[cond2]
    RL     = R[cond2]
    RSVCL  = RSVC[cond2]
    SL      = S[cond2]
    ##BIN###########################################################################
#    bins   = np.linspace(min(RSVC), max(RSVC), nzbins+1)
#    mpcb   = np.linspace(min(RL) , max(RL) , nzbins+1)
#    zmpc   = (mpcb[:-1] + mpcb[1:]) / 2
#    zspect = np.histogram(RSVC, weights=ML, bins=bins)[0]
#    binctr = (bins[:-1] + bins[1:]) / 2
    ###START##CONVERSION##TO##LCO###################################################
    dat_zp1, dat_logm, dat_logsfr, _ = np.loadtxt("sfr_release.dat", unpack=True) # Columns are: z+1, logmass, logsfr, logstellarmass
    # Intermediate processing of tabulated data                                                                         
    dat_logzp1 = np.log10(dat_zp1)
    dat_sfr    = 10.**dat_logsfr
    
    # Reshape arrays                                                                                                    
    dat_logzp1  = np.unique(dat_logzp1)  # log(z+1), 1D                                                                 
    dat_logm    = np.unique(dat_logm)  # log(Mhalo), 1D                                                                 
    dat_sfr     = np.reshape(dat_sfr, (dat_logm.size, dat_logzp1.size))
    
    # Get interpolated SFR value(s)                                                                                     
    rbv         = scp.interpolate.RectBivariateSpline(dat_logm, dat_logzp1, dat_sfr, kx=1, ky=1)    
    ###MAKE##A##FUNCTION##FOR##IT###################################################
    def LCO(Mhal, z, chi):
        sfr      = rbv.ev(np.log10(Mhal+1E2), np.log10(z+1))
        zeroes   = sfr < 2E-4
        sfr[zeroes]=0.0
        lir      = sfr * 1e10 / del_mf
        alphainv = 1./alpha
        lcop     = lir**alphainv * 10**(-beta * alphainv)
        Lco      = 4.9e-5 * lcop
        return Lco
            
    return RSVCL, LCO(ML, RSVCL, RL), SL

def gaussian(x,s,mu):
    return np.e**(-(x-mu)**2/(2*(s/c)**2))

def nrmfac(lco, spec):
    return lco/sum(spec)

def Tline(Lco,z,chi):
    numin    = nuco/(mxz+1.)
    numax    = nuco/(mnz+1.)
    dnu      = (numax-numin)/nzbins
    pxsz     = pixbm**2*amtsr
    nuobs    = nuco/(z+1.)
    I_line   = (Lco)/(4*np.pi*dnu*chi**2*(1+z)**2*pxsz)
    T_line   = (1./2)*convfac*I_line/nuobs**2               
    return T_line*1E6

print 'start'
spread = 19
cs     = []
lt      = []
for i in xrange(spread):
    l  = []
    cs = []
    for j in xrange(spread):
        RS,LCO,SF = pltdata(pntanx+(pixbm*amtdeg*(i-int(spread/2.))), pntany+(pixbm*amtdeg*(j-int(spread/2.))))
        print np.max(LCO)
        spect = np.zeros(binctr.shape)
        for k in xrange(len(RS)):
            gussn = gaussian(binctr, SF[k], RS[k])
            norm  = nrmfac(LCO[k], gussn)
            spect = spect + (gussn*norm)

        chi = z_to_r(binctr)

        SpctT = Tline(spect, binctr, chi)
        
        cs.append(SpctT)
    lt.append(cs)
print 'done'

np.save('datcbe.npy', np.asarray(lt))
#plt.semilogy(binctr, SpctT+1e-3)
'''
f, axarr = plt.subplots(3, sharex=True)
axarr[0].semilogy(binctr, Sf1+1E-3)
axarr[2].set_ylabel('$T_{CO} [\mu K]$')
axarr[1].semilogy(binctr, Sf2+1E-3)
axarr[1].set_ylabel('$T_{CO} [\mu K]$')
axarr[2].semilogy(binctr, Sf3+1E-3)
plt.xlabel('$Z$')
axarr[0].set_ylabel('$T_{CO} [\mu K]$')
'''