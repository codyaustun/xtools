from ..mongo.data import XData
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import xtools.figures.formats as xff
import datetime
import os

class Outcomes(object):
    '''
    Routines for plotting person course information. 
    '''

    def __init__(self,xdata):
        self._xdata = xdata
        self.person = xdata.get('person_course',conditions={})
                
        self.mens2_cid = xdata.course_id.replace('/','__')
        self.nickname = xdata.course_id.split('/')[1]
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/Outcomes/'
        print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)

    
    def grade_distribution(self,**kwargs):
        '''
        Simple grade distribution.

        Parameters
        ----------
        None
        
        Output
        ------
        Figures and respective formats.

        Returns
        -------
        None
        '''

        if self.person.grade.count() < 50:
            print "Not enough grade information. Return without grade distribution."
            return None

        bins = 50 
        hmin = 0.0 #self.person['grade'].min()
        hmax = 1.0 #self.person['grade'].max()
        glowbound = 0.02

        ### Plot
        fig = plt.figure(figsize=(12,7))
        ax1 = fig.add_subplot(1,1,1)

        self.person[(self.person.grade>=glowbound) & (self.person.certified==0)]['grade'].hist(ax=ax1,bins=bins,range=(hmin,hmax),log=False,cumulative=0,
                                                 color=xff.colors['neutral'],edgecolor=xff.colors['neutral'])
        
        self.person[(self.person.grade>=glowbound) & (self.person.certified==1)]['grade'].hist(ax=ax1,bins=bins,range=(hmin,hmax),log=False,cumulative=0,
                                                 color=xff.colors['institute'],edgecolor=xff.colors['institute'],alpha=0.8)
        
        xlab = 'Grade'
        #ax1.set_xlabel(r'%s' % (xlab),fontdict={'fontsize': 30,'style': 'oblique'})
        #ax1.set_ylabel(r'Count (log scale)',fontdict={'fontsize': 30,'style': 'oblique'})
        ax1.set_xlim(0,hmax)
        ax1.set_ylim(1,)
        ax1.legend(['$Enrollees$','$Certified$'],loc=1,prop={'size':24},frameon=False)
        ax1.set_xticklabels([r'$%.1f$' % x for x in ax1.get_xticks()],fontsize=30)
        ax1.set_yticklabels([r'$%d$' % y for y in ax1.get_yticks()],fontsize=30)

        ### Generalized Plotting functions
        figsavename = self.figpath+'grade_distribution_'+self.nickname
        xff.texify(fig,ax1,
                   xlabel='Grade (> %.2f)' % (glowbound),
                   ylabel='Count',
                   gridb='y',
                   figsavename=figsavename+'.png')

        return None


    def grade_vs_nchapters(self,**kwargs):
        """
        Scatter plot of final grade versus nchapters accessed. All points are 
        jittered for clarity. Text labels are added to indicate subpopulations.

        Parameters
        ----------
        None
        
        Output
        ------
        Figures and respective formats.

        Returns
        -------
        None
        """
        
        if 'nchapters' not in self.person or 'grade' not in self.person or 'certified' not in self.person:
            print "One of the three columns necessary for this plot is missing. Check person_course for: 'nchapters','grade', and 'certified'."
            return None

        ### Data
        data = self.person[['nchapters','grade','certified']].copy()
        chap_jmax = 0.75
        grade_jmax = 0.005
        data.nchapters = data.nchapters.apply(lambda x: x + chap_jmax*(np.random.sample()-0.5))
        data.grade = data.grade.apply(lambda x: x + grade_jmax*(np.random.sample()))
        data = data.dropna()

        certcut = self.person[self.person['certified']==1].grade.min()

        ### Plot
        fig = plt.figure(figsize=(12,10))
        ax1 = fig.add_subplot(1,1,1)
        #Non-Certs
        data[data.certified==0].plot('nchapters','grade',style='.',color=xff.colors['neutral'],label=self.nickname,ax=ax1)
        #Certified
        data[data.certified==1].plot('nchapters','grade',style='.',color=xff.colors['institute'],ax=ax1)

        ### Illustrations (labels)
        ncmax = self.person[self.person.certified==1].nchapters.order()[-20::].min() ### Funny, but this cuts off staff
        ax1.hlines(certcut,0,ncmax+1,lw=2)
        ax1.vlines(int(ncmax/2),0,certcut,lw=2)
        ax1.text(ncmax/6,certcut-0.05,'$Viewed$',fontsize=30,alpha=0.75)
        ax1.text(ncmax/2+(ncmax/4),certcut-0.05,'$Explored$',fontsize=30,alpha=0.75)
        ax1.text(ncmax/2,0.8,'$Certified$',fontsize=30,alpha=0.75,horizontalalignment='center',)

        ### Plot Details
        ax1.set_xticklabels([r'$%0.f$' % x for x in ax1.get_xticks()])
        ax1.set_yticklabels([r'$%0.1f$' % x for x in ax1.get_yticks()],fontsize=30)
        #ax1.legend(loc=4,prop={'size':28},frameon=False)
        ax1.set_xlim(0,ncmax+1)
        ax1.set_ylim(0,1.01)


        ### Generalized Plotting functions
        figsavename = self.figpath+'scatter_grade_vs_nchapters_'+self.nickname
        xff.texify(fig,ax1,
                   xlabel='Chapters Viewed',
                   ylabel='Grade',
                   gridb='y',
                   figsavename=figsavename+'.png')

        return None



 






