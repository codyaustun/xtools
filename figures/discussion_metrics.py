import os
from datetime import date,datetime,timedelta

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import ujson as json
import mongoengine

import xtools
from xtools.figures import formats as xff

class DiscussionMetrics(object):
    '''
    Routines for plotting person course information. 
    '''

    def __init__(self,xdata):
        self.xdata = xdata
        # self.caxis = xdata.get('course_axis',conditions={})
        # self.caxis = self.caxis.sort('index') # Note, index is a column in the course axis collection.

        self.mens2_cid = xdata.course_id.replace('/','__')
        self.nickname = xdata.course_id.split('/')[1].replace('_','.') #'2.01x'
        self.institute = xdata.course_id.split('/')[1]#MITx
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/Discussion_Metrics/'
        print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)

        ### Course Info
        self.cinfo = mongoengine.connect('dseaton').dseaton.course_info.find({'mongo_id':xdata.course_id})
        self.cinfo = pd.DataFrame.from_records([r for r in self.cinfo])
        self.cinfo = self.cinfo.ix[0,:].T

        self.cinfo['start_date'] = np.datetime64(datetime.strptime(self.cinfo['start_date'],"%Y-%m-%d"))
        self.cinfo['end_date'] = np.datetime64(datetime.strptime(self.cinfo['end_date'],"%Y-%m-%d"))

        ### Load Person Course
        person = xdata.get('person_course')

        ### Load Forum Data
        self.forum = xdata.get('forum_data',mongo_id=True)

        self.forum['created_at'] = self.forum['created_at'].apply(lambda x: pd.to_datetime(x) if pd.notnull(x) else None)
        # forum['last_activity_at'] = forum['last_activity_at'].apply(lambda x: np.datetime64(munge_time(x)) if pd.notnull(x) else None)
        self.forum['updated_at'] = self.forum['updated_at'].apply(lambda x: pd.to_datetime(x) if pd.notnull(x) else None)

        self.forum['up_count'] = self.forum.votes.apply(lambda x: x['up_count'] if 'up_count' in x else None) 
        self.forum['up_user_id'] = self.forum.votes.apply(lambda x: x['up'] if 'up' in x else None) 

        """
        Parse Discussion Metrics - Then merge with person course.
        """

        ### Here we are mering forum data with person_course 
        ### Consider making this general at course report initialization

        #Create matrix of user-upvotes
        upvotes = []
        for i in self.forum.index:
            if len(self.forum.ix[i,'up_user_id']) > 0:
                #print forum.ix[i,'up_user_id']
                upvotes.append(pd.Series(data=1,index=[u for u in self.forum.ix[i,'up_user_id']]))

        #Sum all upvotes
        upvotes = pd.concat(upvotes,axis=1,keys=self.forum._id.values).sum(axis=1).order()
        #Count total number of posts (Comment) and comments [CommentThread])
        posts = self.forum.author_id.value_counts()
        #Count total number of comments (CommentThread)
        comments = self.forum[self.forum._type=='Comment'].author_id.value_counts()
        #Total Activity
        total = pd.concat([upvotes,posts,comments],axis=1).sum(axis=1)
       
        """
        Merge discussion metrics with person-course (pc_plus)
        """
        self.pc_plus = pd.concat([upvotes,posts,comments,total],axis=1,keys=['upvotes','posts','comments','total_disc']).fillna(0)
        self.pc_plus = self.pc_plus.reset_index().rename(columns={'index':'user_id'})
        self.pc_plus.user_id = self.pc_plus.user_id.apply(np.int64)

        self.pc_plus = person.merge(self.pc_plus,how='left',left_on='user_id',right_on='user_id')


    def top_text_threads(self,Nthreads):
        """
        Creates list of top "text threads" with baseline stats.
        Text threads imply the most writing, as opposed to most up votes.
        
        Parameters (generated during class initialization)
        ----------
        Nthreads: number of top threads to return (don't return all yet)

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """
        
        if Nthreads > 20:
            print "Unable to output more than 20 threads; waiting for FERPA review."
            sys.exit(100)

        print self.forum.ix[4,:]


        return None


    def activity_distributions(self):
        """
        Creates discussion activity distributions for 
        users with > 0 activities (at least one action).
        
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
        
        gtzero = self.pc_plus[self.pc_plus.total_disc>0]
        for col in ['upvotes','posts','comments','total_disc']:
            gtzero[col] = gtzero[col].apply(lambda x: np.log(x) if x else None)
            fig = plt.figure(figsize=[12,7])
            ax1 = fig.add_subplot(1,1,1)
            ### Non-Certs
            gtzero[gtzero.certified==0][col].hist(bins=50,range=[0,9],log=True,
                                                  color=xff.colors['neutral'],
                                                  edgecolor=xff.colors['neutral'])
            ### Certs
            gtzero[gtzero.certified==1][col].hist(bins=50,range=[0,9],log=True,
                                                  color=xff.colors['institute'],
                                                  edgecolor=xff.colors['institute'],
                                                  alpha=0.8)
            tics = [1,10,100,1000,10000]
            ax1.set_xticks([np.log(x) for x in tics])
            ax1.set_xticklabels(tics)
            ax1.set_xlim([0,8])
            xff.texify(fig,ax1,xlabel=col.replace('_',' '),ylabel='Count')

            figsavename = self.figpath+'disc_act_distribution_'+col+'_'+self.nickname+'.png'
            fig.savefig(figsavename, bbox_inches='tight', dpi=300)

        return None

    
    def scatter_discussion_size(self,colx,coly,disc_act,figsave=False):
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
        data = self.pc_plus[[colx,coly,disc_act,'certified']].copy()
        Jcolx = 0.75
        Jcoly = 0.01
        bmin = 1.0
        bscale = 0.2
        data[colx] = data[colx].apply(lambda x: x + Jcolx*(np.random.sample()-Jcolx))
        data[coly] = data[coly].apply(lambda x: x + Jcoly*(np.random.sample()))
        data[disc_act] = data[disc_act].fillna(1.0)

        certcut = self.pc_plus[self.pc_plus['certified']==1].grade.min()

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


    def daily_activity(self):
        """
        Creates daily timeseries of discussion activity (only posts/comments/votes from forum data).
       
        
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

        fig = plt.figure(figsize=[20,6])
        ax1 = fig.add_subplot(1,1,1)

        ### List of Certified Participants
        certs = self.pc_plus[self.pc_plus.certified==1].user_id.unique()
        certs = [str(u) for u in certs]

        ### Non-Certified
        post_act = self.forum[ (self.forum.created_at.notnull()) & (self.forum.author_id.isin(certs)==False) ].created_at.apply(lambda x: x.date()).value_counts().sort_index()
        post_act.plot(ax=ax1,style="-o",ms=6,lw=2,color=xff.colors['neutral'],label='$Non-Certified$')
        #(post_act.cumsum()/10).plot(ax=ax1,style="-",ms=3,color='Orange')
        
        ### Certified
        post_act = self.forum[ (self.forum.created_at.notnull()) & (self.forum.author_id.isin(certs)) ].created_at.apply(lambda x: x.date()).value_counts().sort_index()
        post_act.plot(ax=ax1,style="-o",ms=6,lw=2,color=xff.colors['institute'],label='$Certified$')

        xmin = (self.cinfo['start_date'] - np.timedelta64(2,'W')).item().date()
        xmax = (self.cinfo['end_date'] + np.timedelta64(4,'W')).item().date()

        ax1.set_xlim(xmin,xmax)

        ylim1 = ax1.get_ylim()[1]
        ax1.vlines([self.cinfo.start_date.item().date(),self.cinfo.end_date.item().date()], 0, ylim1, colors='Gray', lw=1.5, linestyles='--')
        ax1.set_ylim(0,ylim1)

        ax1 = xff.timeseries_plot_formatter(ax1,interval=1)
        ax1.legend(loc=1,prop={'size':24},frameon=False)

        figsavename = self.figpath+'discussion_activity_'+self.nickname.replace('.','_')
        xff.texify(fig,ax1,ylabel='Forum Text Submissions',
                   tic_size=20,label_size=24,
                   datefontsize=20,
                   title=self.nickname,
                   figsavename=figsavename+'.png')

        return None
    


         
     











