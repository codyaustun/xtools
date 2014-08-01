from ..mongo.data import XData
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import formats as xff
import datetime
import os

class Activity(object):
    '''
    Routines for plotting person course information. 
    '''

    def __init__(self,xdata):
        self._xdata = xdata
        self.person = xdata.get('person_course',conditions={})
                
        self.mens2_cid = xdata.course_id.replace('/','__')
        self.nickname = xdata.course_id.split('/')[1].replace('_','.') #'2.01x'
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/Activity/'
        print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)


    def distribution_logic(self,ax,column,cert_switch):
        """
        Logic for generating distributions from the person_course collection.

        Parameters
        ----------
        ax : subplot of figure (add_subplot)
        column : specified column from person_course
        cert_swithc : True/False for turning certified data on/off

        Returns
        -------
        None
        """

        bins = int(self.person[column].max()) - int(self.person[column].min())
        
        if bins < 0 or not bins > 0:
            print "Issue with binning!"
            return False

        if bins > 50 or column in ['grade']:
            bins = 50

        
        if column not in ['nevents','nforum_events']:
            hmin = self.person[column].min()
            hmax = self.person[column].max()
            self.person[self.person.certified==0][column].hist(ax=ax,bins=bins,range=(hmin,hmax),log=True,cumulative=0,
                                                     color=xff.colors['neutral'],edgecolor=xff.colors['neutral'])
            ### Cert Switch
            if cert_switch == True:
                self.person[self.person.certified==1][column].hist(ax=ax,bins=bins,range=(hmin,hmax),log=True,cumulative=0,
                                                        color=xff.colors['institute'],edgecolor=xff.colors['institute'],alpha=0.8)
            
            xlab = column.replace('_',' ')
            ax.set_xlabel(r'%s' % (xlab),fontdict={'fontsize': 30,'style': 'oblique'})
            ax.set_ylabel(r'Count (log scale)',fontdict={'fontsize': 30,'style': 'oblique'})
            ax.set_xlim(0,hmax)
            ax.set_ylim(1,)
            ax.legend(['$Non-Certified$','$Certified$'],loc=1,prop={'size':24},frameon=False)
            ax.set_xticklabels([r'$%d$' % x for x in ax.get_xticks()],fontsize=30)
            ax.set_yticklabels([r'$%d$' % y for y in ax.get_yticks()],fontsize=30)
        
        else:
            hmin = 0.0
            hmax = np.log(self.person[column].max())
            #print hmin,hmax,self.person[column].min()

            min_events = 1
            if column == 'nevents':
                min_events = 1


            data = self.person[(self.person.certified==False) & (self.person[column]>min_events)][column].apply(np.log)
            data.hist(ax=ax,bins=bins,range=(hmin,hmax),log=False,cumulative=0,
                      color=xff.colors['neutral'],edgecolor=xff.colors['neutral'])
            ### Cert Switch
            if cert_switch == True:
                data = self.person[(self.person.certified==True) & (self.person[column]>min_events)][column].apply(np.log)
                data.hist(ax=ax,bins=bins,range=(hmin,hmax),log=False,cumulative=0,
                          color=xff.colors['institute'],edgecolor=xff.colors['institute'],alpha=0.8)

            ticks = [1,10,100,1000,10000]
            ax.set_xticks(np.log(ticks))
            ax.set_xticklabels(ticks)

            if column == 'nevents':
                xlab = 'Clicks'
            elif column == 'nforum_events':
                xlab = 'Forum Clicks'
            else:
                xlab = column.replace('_',' ')
            
            ax.set_xlabel(r'%s > %d' % (xlab,min_events), fontdict={'fontsize': 30,'style': 'oblique'})
            ax.set_ylabel(r'Count',fontdict={'fontsize': 30,'style': 'oblique'})
            ax.legend(['$Non-Certified$','$Certified$'],loc=1,prop={'size':24},frameon=False)
            ax.set_xticklabels([r'$%d$' % x for x in ticks],fontsize=30)
            ax.set_yticklabels([r'$%d$' % y for y in ax.get_yticks()],fontsize=30)

        return None


    def activity_distributions(self,columns=[],**kwargs):
        """
        Activity Distributions from person_course collection using Pandas built in hist function.

        There are several columns which can be plotted as distributions:
        features = ['ndays_act', 'nevents', 'nforum_events', 'nforum_posts', 'nplay_video', 'nproblem_check', 'nprogcheck']
            
        Course Reports focus on nevents, ndays_act, and nchapters

        Parameters
        ----------
        columns : list of column names

        Typical column names - ['ndays_act', 'nevents', 'nforum_events', 
                                'nforum_posts', 'nplay_video', 'nproblem_check', 
                                'nprogcheck']

        Returns
        -------
        None
        """

        data = self.person.filter(items=columns)

        for col in columns:
            if col not in self.person: 
                columns.remove(col)
                print "Some of the specified columns do not exist in the person_course collection."
                print col

        if len(columns) == 0:
            print "No specified columns available."  
            return None
        
        for column in data.columns:
            ### Plot
            fig = plt.figure(figsize=(12,7))
            ax1 = fig.add_subplot(1,1,1)
            check = self.distribution_logic(ax1,column,True)       
            
            ### Generalized Plotting functions
            figsavename = self.figpath+'distribution_'+column.replace(' ','_')+'_'+self.nickname.replace('.','_')
            print figsavename
            xff.texify(fig,ax1,figsavename=figsavename+'.png')

        return None













