from ..mongo.data import XData
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import xtools.figures.formats as xff
from datetime import date,datetime
import os
import mongoengine

class Outcomes(object):
    '''
    Routines for plotting person course information. 
    '''

    def __init__(self,xdata):
        self._xdata = xdata
        self.person = xdata.get('person_course',conditions={})
                
        self.mens2_cid = xdata.course_id.replace('/','__')
        self.nickname = xdata.course_id.split('/')[1].replace('_','.')
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/Outcomes/'
        print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)

        ### Parse first and last times
        self.person.start_time = self.person[self.person.start_time.notnull()==True].start_time.apply(lambda x: np.datetime64(x))
        self.person['last_event'] = self.person[self.person.last_event.notnull()==True]['last_event'].apply(lambda x: np.datetime64(x) if x[-1]!='d' else np.datetime64(x[:-1]))


        ### Course Info
        self.cinfo = mongoengine.connect('dseaton').dseaton.course_info.find({'mongo_id':xdata.course_id})
        self.cinfo = pd.DataFrame.from_records([r for r in self.cinfo])
        self.cinfo = self.cinfo.ix[0,:].T

        self.cinfo['start_date'] = datetime.strptime(self.cinfo['start_date'],"%Y-%m-%d")

    def certification_prob(self,**kwargs):
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

        data = self.person[['start_time','certified']].copy()
        data.start_time = data.start_time.apply(lambda x: (x-self.cinfo['start_date']).days/7 if pd.notnull(x) else x)
        data.certified = data.certified.apply(lambda x: 'Certified' if x == 1 else 'Non-Certified')
        data = pd.crosstab(data.start_time,data.certified).sort_index()

        print data.head()

        # mindate = tmp.index[0] - timedelta(days=21)
        # maxdate = tmp.index[-1] + timedelta(days=21)

        NVD3 = kwargs.get('NVD3',False)
        
        #----------------------------------------------------------------
        ### NVD3 Interactive http://nvd3.org/
        if NVD3:
            
            ### Data
            bins = 50
            hmin = 0.0
            hmax = 1.0
            DATA = self.person[(self.person.grade>=glowbound)]
            Y1,X1 = np.histogram(DATA[DATA.certified==0].grade.values,bins=bins,range=(hmin,hmax))
            Y2,X2 = np.histogram(DATA[DATA.certified==1].grade.values,bins=bins,range=(hmin,hmax))

            ### FIGURE
            from nvd3 import multiBarChart

            ### Output File
            figsavename = self.figpath+'interactive_grade_distribution_'+self.nickname+'.html'
            output_file = open(figsavename, 'w')
            print figsavename

            title = "Certification Bubble Chart: %s" % self._xdata.course_id
            chart = multiBarChart(name=title, height=400)
            chart.set_containerheader("\n\n<h2>" + title + "</h2>\n\n")
            nb_element = len(X1)

            extra_serie = {"tooltip": {"y_start": "", "y_end": ""},
                           "color":xff.colors['neutral']
                           }
            chart.add_serie(name="Count", y=Y1, x=X1, extra=extra_serie)
            extra_serie = {"tooltip": {"y_start": "", "y_end": ""},
                           "color":xff.colors['institute']
                           }
            chart.add_serie(name="Duration", y=Y2, x=X2, extra=extra_serie)

            ### Final Output
            chart.buildhtml()
            output_file.write(chart.htmlcontent)

            #---------------------------------------

            #close Html file
            output_file.close()

        return None

    
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

        NVD3 = kwargs.get('NVD3',False)

        if self.person.grade.count() < 50:
            print "Not enough grade information. Return without grade distribution."
            return None

        bins = 50 
        hmin = 0.0 #self.person['grade'].min()
        hmax = 1.0 #self.person['grade'].max()
        glowbound = 0.1

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
        ax1.legend(['$Non-Certified$','$Certified$'],loc=1,prop={'size':24},frameon=False)
        ax1.set_xticklabels([r'$%.1f$' % x for x in ax1.get_xticks()],fontsize=30)
        ax1.set_yticklabels([r'$%d$' % y for y in ax1.get_yticks()],fontsize=30)

        ### Generalized Plotting functions
        figsavename = self.figpath+'grade_distribution_'+self.nickname.replace('.','_')
        xff.texify(fig,ax1,
                   xlabel='Grade (> %.2f)' % (glowbound),
                   ylabel='Count',
                   gridb='y',
                   figsavename=figsavename+'.png')

        
        #----------------------------------------------------------------
        ### NVD3 Interactive http://nvd3.org/
        if NVD3:
            
            ### Data
            bins = 50
            hmin = 0.0
            hmax = 1.0
            DATA = self.person[(self.person.grade>=glowbound)]
            Y1,X1 = np.histogram(DATA[DATA.certified==0].grade.values,bins=bins,range=(hmin,hmax))
            Y2,X2 = np.histogram(DATA[DATA.certified==1].grade.values,bins=bins,range=(hmin,hmax))

            ### FIGURE
            from nvd3 import multiBarChart

            ### Output File
            figsavename = self.figpath+'interactive_grade_distribution_'+self.nickname+'.html'
            output_file = open(figsavename, 'w')
            print figsavename

            title = "Grade Distribution: %s" % self._xdata.course_id
            chart = multiBarChart(name=title, height=400)
            chart.set_containerheader("\n\n<h2>" + title + "</h2>\n\n")
            nb_element = len(X1)

            extra_serie = {"tooltip": {"y_start": "", "y_end": ""},
                           "color":xff.colors['neutral']
                           }
            chart.add_serie(name="Count", y=Y1, x=X1, extra=extra_serie)
            extra_serie = {"tooltip": {"y_start": "", "y_end": ""},
                           "color":xff.colors['institute']
                           }
            chart.add_serie(name="Duration", y=Y2, x=X2, extra=extra_serie)

            ### Final Output
            chart.buildhtml()
            output_file.write(chart.htmlcontent)

            #---------------------------------------

            #close Html file
            output_file.close()

        return None


    def scatter_bubble_size(self,DF,colx,coly,disc_act,figsave=False):
        """
        Creates scatter plot with x=colx, y=coly.
        Size of markers always proportional to disc_act (discussion activity).
        
        Parameters (generated during class initialization)
        ----------
        colx: column to be plotted on x-axis
        coly: column to be plotted on y-axis
        disc_act: column for scaling marker (bubble) size
        figsave: True/False to allow exploratory analysis without saving fig.

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """

        ### Data
        data = DF[[colx,coly,disc_act,'certified']].copy()
        Jcolx = 0.75
        Jcoly = 0.01
        bmin = 1.0
        bscale = 0.2
        data[colx] = data[colx].apply(lambda x: x + Jcolx*(np.random.sample()-Jcolx))
        data[coly] = data[coly].apply(lambda x: x + Jcoly*(np.random.sample()))
        data[disc_act] = data[disc_act].fillna(1.0)

        certcut = DF[DF['certified']==1].grade.min()

        fig = plt.figure(figsize=[12,10])
        ax1 = fig.add_subplot(1,1,1)
        #Non-Certs
        tmp = data[data.certified==0]
        ax1.scatter(tmp[colx],tmp[coly],s=bscale*tmp[disc_act],color=xff.colors['neutral'])
        #Certified
        tmp = data[data.certified==1]
        ax1.scatter(tmp[colx],tmp[coly],s=bscale*tmp[disc_act],color=xff.colors['institute'])

        #ax1.legend(loc=5,prop={'size':18},scatterpoints=1,frameon=False)
        ax1.set_xlim(-0.05,)
        ax1.set_ylim(-0.05,1.05)

        ### Generalized Plotting functions
        xff.texify(fig,ax1,xlabel=colx,ylabel=coly,
                   title='bubble size proportional to %s' % (disc_act.replace('_',' ')),
                   tic_size=20,label_size=24,datefontsize=20)

        figsavename = self.figpath+'scatter_'+colx+'_'+coly+'_disc_size_'+self.nickname.replace('.','_')+'.png'
        fig.savefig(figsavename, bbox_inches='tight', dpi=300)

        return None


    def grade_vs_nchapters(self,**kwargs):
        """
        Scatter plot of final grade versus nchapters accessed. All points are 
        jittered for clarity. Text labels are added to indicate subpopulations.

        Parameters
        ----------
        NVD3 = False.  If true, nvd3 interactive figure output.
        
        Output
        ------
        Figures and respective formats.

        Returns
        -------
        None
        """

        NVD3 = kwargs.get('NVD3',False)
        
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
        figsavename = self.figpath+'scatter_grade_vs_nchapters_'+self.nickname.replace('.','_')
        xff.texify(fig,ax1,
                   xlabel='Chapters Viewed',
                   ylabel='Grade',
                   gridb='y',
                   figsavename=figsavename+'.png')

        
        #----------------------------------------------------------------
        ### NVD3 Interactive http://nvd3.org/
        if NVD3:
            
            data = data[(data.nchapters>0) & (data.grade>0)].dropna()
            randrows = np.random.choice(data.index.values,2000)
            data = data.ix[randrows,:]
            X1 = data[data.certified==0].nchapters.values
            Y1 = data[data.certified==0].grade.values
            X2 = data[data.certified==1].nchapters.values
            Y2 = data[data.certified==1].grade.values
            #print X1,Y1

            ### FIGURE
            from nvd3 import scatterChart

            ### Output File
            figsavename = self.figpath+'interactive_scatter_grade_nchap_'+self.nickname+'.html'
            output_file = open(figsavename, 'w')
            print figsavename

            title = "Scatter Plot Grade vs Chapters Viewed: %s" % self._xdata.course_id
            chart = scatterChart(name=title, width=850, height=550, x_is_date=False, x_axis_format=".1f", y_axis_format=".1f")
            chart.set_containerheader("\n\n<h2>" + title + "</h2>\n\n")
            nb_element = len(X1)

            kwargs1 = {'shape': 'circle', 'size': '3'}
            kwargs2 = {'shape': 'circle', 'size': '3'}

            extra_serie = {"tooltip": {"y_start": "", "y_end": " calls"}}

            chart.add_serie(name="Participants", y=Y1, x=X1, extra=extra_serie, **kwargs1)
            chart.add_serie(name="Certified", y=Y2, x=X2, extra=extra_serie, **kwargs2)

            
            ### Final Output
            chart.buildhtml()
            output_file.write(chart.htmlcontent)

            #---------------------------------------

            #close Html file
            output_file.close()


        return None



 






