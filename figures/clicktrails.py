from ..mongo.data import XData
import xtools
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import xtools.figures.formats as xff
import xtools.figures.course_structure as CS
from datetime import date,datetime,timedelta
import os
import mongoengine

class ClickTrails(object):
    '''
    Routines for plotting tracking log information. 
    '''

    def __init__(self,xdata):
        self._xdata = xdata
        self.person = xdata.get('person_course',conditions={})
                
        self.mens2_cid = xdata.course_id.replace('/','__')
        self.nickname = xdata.course_id.split('/')[1].replace('_','.')
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/ClickTrails/'
        print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)

        ### Parse first and last times
        self.person.start_time = self.person[self.person.start_time.notnull()==True].start_time.apply(lambda x: np.datetime64(x))
        self.person['last_event'] = self.person[self.person.last_event.notnull()==True]['last_event'].apply(lambda x: np.datetime64(x) if x[-1]!='d' else np.datetime64(x[:-1]))

        ### Course Axis
        ### Initiate Course Axis
        self.CS = CS.CourseStructure(xdata)
        self.caxis = self.CS.caxis

        ### Course Info
        self.cinfo = mongoengine.connect('dseaton').dseaton.course_info.find({'mongo_id':xdata.course_id})
        self.cinfo = pd.DataFrame.from_records([r for r in self.cinfo])
        self.cinfo = self.cinfo.ix[0,:].T

        self.cinfo['start_date'] = np.datetime64(datetime.strptime(self.cinfo['start_date'],"%Y-%m-%d"))
        self.cinfo['end_date'] = np.datetime64(datetime.strptime(self.cinfo['end_date'],"%Y-%m-%d"))

        query = mongoengine.connect('mitxdb').mitxdb.tracking_log.find({'course_id':xdata.course_id},
                                                                       {'username':1,'module_id':1,'time':1})
        
        # query = mongoengine.connect('dseaton').dseaton.derived_person_object_time.find({'course_id':xdata.course_id},
        #                                                                                {'username':1,'module_id':1,'time':1})

        self.potime = pd.DataFrame.from_records((r for r in query))
        print "self.potime loaded"

        self.potime['date'] = self.potime.time.apply(lambda x: x.split('T')[0])
        print "date added to self.potime"

        self.potime['rel_week'] = self.potime.date.apply(lambda x: (np.datetime64(x) - self.cinfo['start_date']).item().days/7)
        print "Relative week (rel_week) added to self.potime"


    def groupby_username(self):
        """
        Individual Student Time Series via groupby(username) 
        Note: Unclear if this should live in "init" or the 
        individual functions. Placed here so only have to execute
        mongo query once.

        Parameters (generated during class initialization)
        ----------
        None

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """
        grouped = self.potime.groupby('username')
        
        time_spent = pd.Series()
        for n,g in grouped:
            ut = g.sort('time').time.apply(np.datetime64)
            if len(g) > 1:
                ### Time Spent
                ut = (ut.diff()/np.timedelta64(1, 's')).shift(-1)
                ut = ut[(ut>=10.0) & (ut<=3600.0)]
                time_spent.set_value(n,ut.sum())
        
                ### Transition Between Resources
                # To Be Done

        ### Remove Blank User
        time_spent = time_spent[1:]
        self.time_spent = time_spent
        print "time spent estimated"

        dftimespent = self.time_spent.reset_index().rename(columns={'index':'username',0:'time_in_course'})
        self.person = pd.merge(self.person,dftimespent,how='left',left_on='username',right_on='username')
        # print self.person.time_in_course

        self._xdata['person_course_w_time'] = self.person

        return None


    def latex_table_course_data(self):
        """
        Create a latex table using course info and person_course.

        Parameters (generated during class initialization)
        ----------
        None

        Output
        ------
        Saves latex file.

        Returns
        -------
        None
        """

        custom_figpath = '../Analytics_Data/'+self.mens2_cid+'/CourseDataTables/'
        print custom_figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(custom_figpath):
            os.makedirs(custom_figpath)

        #### Course Meta Data Table
        #--------------------------------------------------------------------------------------------------
        N_enrolled = len(self.person[self.person.registered==1].username.unique())
        N_certified = len(self.person[self.person.certified==1].username.unique())

        data = ['MITx',self.cinfo.start_date.item().date(),self.cinfo.course_length,self.cinfo.estimated_effort,N_enrolled,N_certified]
        index = ['School','Launch Date','Course Length','Estimated Effort','N Enrolled','N Certified']
        columns = ['\textbf{'+self.cinfo.code+'}']
        coursemeta = pd.DataFrame(data=data,index=index,columns=columns)
        coursemeta.index.name = '\textbf{Course Metadata}'
        #print coursemeta.to_latex(header=True)

        tablesavename = custom_figpath+'CourseMetaData_'+self.nickname.replace('.','_')+'.tex'
        coursemeta.to_latex(tablesavename,header=True)

        #### Course Activity Stats Table
        #--------------------------------------------------------------------------------------------------
        subgroups = ['\textbf{Non-Certified}','\textbf{Certified}']
        course_stats = []
        for sg in [0,1]:
            hours_served = str( round(self.person[self.person.certified==sg].time_in_course.sum()/3600.0, 1) ) + ' hrs'
            mean_time = str( round(self.person[self.person.certified==sg].time_in_course.mean()/3600.0, 1) ) + ' hrs'
            total_clicks = self.person[self.person.certified==sg].nevents.sum()
            mean_clicks = round(self.person[self.person.certified==sg].nevents.mean(), 1)
            total_post_events = self.person[self.person.certified==sg].nforum_events.sum()
            mean_post_events = round(self.person[self.person.certified==sg].nforum_events.mean(), 1)
            
            course_stats.append( pd.Series(data=[total_clicks,mean_clicks,hours_served,mean_time,total_post_events,mean_post_events],
                                           index=['Summed Number of Clicks','Mean Clicks per User','Summed Total Time','Mean Total Time per User','Summed Number of Forum Events','Mean Forum Events per User'])
                                )

        course_stats = pd.concat(course_stats,axis=1,keys=subgroups)   
        course_stats.index.name = '\textbf{Activity Highlights}'
        #print course_stats.to_latex()

        tablesavename = custom_figpath+'CourseActivityStats_'+self.nickname.replace('.','_')+'.tex'
        course_stats.to_latex(tablesavename,header=True)

        return None


    def daily_unique_users(self):
        """

        """
        fig = plt.figure(figsize=[20,6])
        ax1 = fig.add_subplot(1,1,1)

        sgcolors = ['Silver','Crimson']
        sglabels = ['$Non-Certified$','$Certified$']

        for sg in [0,1]:
            users = self.person[self.person.certified==sg].username.dropna().unique()
            daily = pd.crosstab(self.potime[self.potime.username.isin(users)].username,self.potime.date)
            daily = daily[daily>0].count().sort_index()
            daily.index = [np.datetime64(d) for d in daily.index]
            daily.plot(ax=ax1,style="-o",ms=6,lw=2,color=sgcolors[sg],rot=0,label=sglabels[sg])
        
        xmin = (self.cinfo['start_date'] - np.timedelta64(2,'W')).item().date()
        xmax = (self.cinfo['end_date'] + np.timedelta64(4,'W')).item().date()

        ax1.set_xlim(xmin,xmax)
        ax1 = xff.timeseries_plot_formatter(ax1, interval=1)
        ax1.legend(loc=1,prop={'size':24},frameon=False)

        ylim1 = ax1.get_ylim()[1]
        ax1.vlines([self.cinfo.start_date.item().date(),self.cinfo.end_date.item().date()], 0, ylim1, colors='Gray', lw=1.5, linestyles='--')
        ax1.set_ylim(0,ylim1)

        figsavename = self.figpath+'daily_unique_users_'+self.nickname.replace('.','_')
        xff.texify(fig,ax1,ylabel='Unique Users',
                   tic_size=20,label_size=24,
                   datefontsize=20,
                   title=self.nickname,
                   figsavename=figsavename+'.png')


        return None

    def content_touches_viz(self,horiz):

        ###----------------
        ### Non-Certified
        touches = pd.concat([self.caxis.category,self.freq.ix[:,:].count(),self.freq.sum()],axis=1,keys=['category','users','freq'])
        #print len(touches)
        horiz_w_data = pd.merge(horiz,touches,how='left',left_on='module_id',right_index=True)
        self.CS.content_touches_viz(horiz_w_data,False)

        ###---------------
        ### Certified
        certs = self.person[self.person.certified==1].username.unique()
        touches = pd.concat([self.caxis.category,self.freq.ix[certs,:].count(),self.freq.sum()],axis=1,keys=['category','users','freq'])
        #print len(touches)
        horiz_w_data = pd.merge(horiz,touches,how='left',left_on='module_id',right_index=True)
        self.CS.content_touches_viz(horiz_w_data,True)

        return None


    def resource_use(self,category):
        """
        Number of unique resources by category.

        Parameters (generated during class initialization)
        ----------
        category: ['video','problem', etc.]

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """



        resources = self.caxis[self.caxis.category==category].index.unique()
        usage = self.freq.filter(resources).count(axis=1)  
        
        bins = len(resources)
        brange = (0,usage.max())
        sgcolors = ['Silver','Crimson']
        sglabels = ['$Non-Certified$','$Certified$']

        fig = plt.figure(figsize=[12,6])
        ax1 = fig.add_subplot(1,1,1)

        for sg in [0,1]:  ### Note, later this could be all four subgroups: explored, certified, etc
            subpop = self.person[self.person.certified==sg].username.dropna().unique()
            usage[subpop].hist(range=brange,bins=bins,
                               cumulative=0,#histtype='step',
                               normed=True,alpha=0.85,
                               edgecolor=sgcolors[sg],color=sgcolors[sg])
            # usage[subpop].hist(range=brange,bins=bins,
            #                    cumulative=-1,histtype='step',
            #                    normed=True,alpha=0.85,
            #                    edgecolor=sgcolors[sg],color=sgcolors[sg],label=None)

        ax1.legend(sglabels,loc=9,prop={'size':24},frameon=False)
    

        figsavename = self.figpath+'resource_use_'+category+'_dist_'+self.nickname.replace('.','_')
        xff.texify(fig,ax1,
                   xlabel='Unique %s resources' % (category),
                   ylabel='Normalized Count',
                   title=self.nickname,
                   figsavename=figsavename+'.png')

        return None


    def create_freq_table(self):
        """
        Creat Frequency Table of usernames versus module_id
        """
        freq = pd.crosstab(self.potime.username,self.potime.module_id)
        freq = freq[freq>0]
        nickname = self._xdata.course_id.split('/')[1]#'2.01x'
        #print tmp.filter(regex='video').columns

        ### Have to clean up video ids for most courses
        ### e.g., MITx/2_01x/VIDEO must go to MITx/2.01x/VIDEO
        if '_' not in nickname:
            badname = nickname.replace('.','_')
            freq.columns = [x.replace(badname,nickname) if x.replace(badname,nickname) not in freq.columns else x for x in freq.columns ]

        self.freq = freq

        return None


    def time_on_course(self):
        """
        Estimation of time spent in course. Using self.potime,
        click events are grouped by username and time sorted. 
        Time differences >= 10 sec and <= 3600 sec are summed. 
        Justification for those cutoffs can be found here:
        http://cacm.acm.org/magazines/2014/4/173221-who-does-what-in-a-massive-open-online-course/fulltext
        Submitted Paper: "eText Use in Blended Introductory Physics Courses: Interpreting Meaningful Interactions and the Effects of Course Structure"
        
        Only estimates time for users with more than one event.

        Parameters (generated during class initialization)
        ----------
        None

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """

        fig = plt.figure(figsize=[12,6])
        ax1 = fig.add_subplot(1,1,1)

        ### All Non-Certified
        participants = self.person[self.person.certified==0].username.dropna().unique()
        self.time_spent[participants].apply(np.log).hist(ax=ax1,bins=100,range=[0,16],
                                                    color='Silver',edgecolor=None,alpha=0.9,label="$Non-Certified$")
        
        ### Certified
        certs = self.person[self.person.certified==1].username.dropna().unique()
        self.time_spent[certs].apply(np.log).hist(ax=ax1,bins=100,range=[0,16],
                                             color='Crimson',edgecolor=None,alpha=0.9,label="$Certified$")

        ax1.set_xticks([np.log(x) for x in [1,10,60,600,3600,10*3600,100*3600]])
        ax1.set_xticklabels(['1 sec','10 sec','1 min','10 min','1 hr','10 hrs','100 hrs'],rotation=40)
        ax1.legend()

        figsavename = self.figpath+'time_in_course_'+self.nickname.replace('.','_')
        xff.texify(fig,ax1,
                   xlabel='Total Time In Course',
                   ylabel='Count',
                   # title=self.nickname,
                   tic_size=24,
                   label_size=24,
                   gridb='y',
                   figsavename=figsavename+'.png')


        # print figsavename 
        # if figsavename != None:
        #     dpiset = 300
        #     #fig.savefig('OUTPUT_Figures/%s/%s_%s.png' %(mens2_cid,figsavename,nickname), bbox_inches='tight', dpi=dpiset)
        #     fig.savefig('%s' % (figsavename), bbox_inches='tight', dpi=dpiset)

        return None


    def scatter_bubble_size(self,colx,coly,disc_act,figsave=False):
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
        data = self.person[[colx,coly,disc_act,'certified']].copy()
        Jcolx = 0.75
        Jcoly = 0.01
        Jcolz = 10 # 1.0/sqrt(10000)
        # print Jcolz
        bmin = 1.0
        bscale = 0.2
        data[colx] = data[colx].apply(lambda x: x + Jcolx*(np.random.sample()-Jcolx))
        data[coly] = data[coly].apply(lambda x: x + Jcoly*(np.random.sample()))
        data[disc_act] = data[disc_act].fillna(1.0).apply(lambda x: x + Jcolz*(np.random.sample()))
        ### Take top N discussants, and set their dot size to the Nth + 1 highest (lowest of the set)
        Nd = 5 
        topN = data[disc_act].order().index[-Nd:]
        data.ix[topN,disc_act] = data.ix[topN[1],disc_act] 

        if colx=='time_in_course':
            data[colx] = data[colx].apply(np.log)
        if coly=='time_in_course':
            data[coly] = data[coly].apply(np.log)
        if disc_act=='time_in_course':
            data[disc_act] = data[disc_act].apply(np.log)

        certcut = self.person[self.person['certified']==1].grade.min()

        fig = plt.figure(figsize=[12,10])
        ax1 = fig.add_subplot(1,1,1)
        #Non-Certs
        tmp = data[data.certified==0]
        ax1.scatter(tmp[colx],tmp[coly],s=bscale*tmp[disc_act],color=xff.colors['neutral'])
        #Certified
        tmp = data[data.certified==1]
        ax1.scatter(tmp[colx],tmp[coly],s=bscale*tmp[disc_act],color=xff.colors['institute'])

        #ax1.legend(loc=5,prop={'size':18},scatterpoints=1,frameon=False)
        
        ax1.set_ylim(-0.05,1.05)

        ax1.set_xlim(6,16)
        ax1.set_xticks([np.log(x) for x in [600,3600,10*3600,100*3600]])
        ax1.set_xticklabels(['10 min','1 hr','10 hrs','100 hrs'],rotation=40)
        # ax1.set_xticks([np.log(x) for x in [1,10,60,600,3600,10*3600,100*3600]])
        # ax1.set_xticklabels(['1 sec','10 sec','1 min','10 min','1 hr','10 hrs','100 hrs'],rotation=40)

        ### Generalized Plotting functions
        figsavename = self.figpath+'scatter_'+colx+'_'+coly+'_disc_size_'+self.nickname.replace('.','_')
        ylabel = coly.replace('_',' ')
        if ylabel == 'time in course':
            ylabel = 'Total Time In Course'
        xff.texify(fig,ax1,xlabel=colx.replace('_',' '),
                   ylabel=ylabel,
                   title='bubble size proportional to %s' % (disc_act.replace('_',' ')),
                   tic_size=20,label_size=24,datefontsize=20,
                   figsavename=figsavename+'.png')

        return None


    def bubble_heat_rel_week_vs_chapter(self):
        """
        Bubble Heat - Unique users relative week versus chapter accessed
        Color and bubble size indicate population size.
        
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
        data = self.potime.groupby(['rel_week','module_id']).username.apply(lambda x: len(x.unique()))
        data = data.reset_index().rename(columns={0:'uniqU'})
        data = pd.merge(data,self.caxis[['index','chapter']],how='left',left_on='module_id',right_index=True).dropna()
        
        MINUSERS = 20
        data = data[data.uniqU>MINUSERS]

        W = data.groupby(['chapter','rel_week'])['index','uniqU'].agg([min,max]).reset_index()
        
        fig = plt.figure(figsize=[24,16])
        ax1 = fig.add_subplot(1,1,1)

        c = W[('uniqU','max')]
        cmhot = plt.get_cmap("CMRmap")

        sc = ax1.scatter(W[('index','min')],W[('rel_week','')],s=0.95*W[('uniqU','max')],
                    c=c,edgecolors='None',cmap=cmhot,alpha=0.95)

        cbar = plt.colorbar(sc)
        cbar.set_label('$N$',rotation=90,fontsize=30)
        cbar.ax.tick_params(labelsize=30)
        cbar.ax.tick_params(labelsize=30)
        #cbar.set_ticklabels([r'${0}$'.format("%s" % (y.get_text())) for y in cbar.ax.get_yticklabels()])

        ### Generalized Plotting functions
        figsavename = self.figpath+'bubble_heat_rel_week_vs_chapter_'+self.nickname.replace('.','_')
        xff.texify(fig,ax1,xlabel='Course Structure Index',ylabel='Week Relative to Course Launch',
                   title='Unique Users visiting Chapters each Relative Week (min %d users for display)' % (MINUSERS),
                   tic_size=30,label_size=30,
                   figsavename=figsavename+'.png')

        return None





    
 






