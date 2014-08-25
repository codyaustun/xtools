import os
from datetime import datetime, timedelta, date

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import collections
import json
import mongoengine

from xtools.mongo.data import XData
from xtools.figures import formats as xff
class Enrollment(object):
    '''
    Routines for plotting person course information. 
    '''

    def __init__(self,xdata):
        ### Initialize data source and file pathways
        self._xdata = xdata
        self.person = xdata.get('person_course',conditions={})
                
        self.mens2_cid = xdata.course_id.replace('/','__')
        self.nickname = xdata.course_id.split('/')[1].replace('_','.') #'2.01x'
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/Enrollment/'
        #print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)

        ### Course Info
        self.cinfo = mongoengine.connect('dseaton').dseaton.course_info.find({'mongo_id':xdata.course_id})
        self.cinfo = pd.DataFrame.from_records([r for r in self.cinfo])
        self.cinfo = pd.Series(self.cinfo.ix[0,:].T)


        def date_transform(x):
            return datetime.strptime(x,"%Y-%m-%d")

        self.cinfo['start_date'] = date_transform(self.cinfo['start_date'])
        self.cinfo['end_date'] = date_transform(self.cinfo['end_date'])

        #------------------------------------------------------------
        ### Enrollment Data
        if 'start_time' in self.person:
            self.person.start_time = self.person[self.person.start_time.notnull()==True].start_time.apply(lambda x: np.datetime64(x))
        elif 'start_time_DI' in self.person:
            self.person.start_time = self.person.start_time_DI

        if 'last_event' in self.person:
            self.person['last_event'] = self.person[self.person.last_event.notnull()==True]['last_event'].apply(lambda x: np.datetime64(x) if x[-1]!='d' else np.datetime64(x[:-1]))
        elif 'last_event_DI' in self.person:
            self.person.last_event = self.person.last_event_DI#.apply(date_transform)

        startday = self.person.start_time.dropna().apply(lambda x: x.date()).value_counts().sort_index()
        lastday = self.person.last_event.dropna().apply(lambda x: x.date()).value_counts().sort_index()
        survival = lastday.cumsum().apply(lambda x: startday.sum()-x)
        
        self.enrollment_df = pd.concat([startday,startday.cumsum()],
                               axis=1,
                               keys=['Enroll Count','Enroll Cumulative'])

        self.lastact_df = pd.concat([lastday,survival],
                               axis=1,
                               keys=['Last Activity Count','Last Activity Survival'])


    def last_day_plots_dual(self,**kwargs):
        """
        Combining enroll count and cumulative enrollment.

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
        
        fig = plt.figure(figsize=(12,6))
        ax1 = fig.add_subplot(1,1,1)

        fsize = 24

        self.lastact_df['Last Activity Count'].plot(ax=ax1,lw=3,color='Silver',label='left axis')
        ax1 = xff.timeseries_plot_formatter(ax1)
        ax1.set_yticklabels([r'${0}$'.format("%d" % (y)) for y in ax1.get_yticks()])
        ax1.set_ylabel('$Last Activity Count$'.replace(' ','\ '),
                       fontdict={'fontsize': fsize,'style': 'oblique'})

        ax1.grid(which='both', b=False, axis='x')


        ax2 = ax1.twinx()
        self.lastact_df['Last Activity Survival'].plot(ax=ax2,lw=3,color='Crimson',label='right axis')
        ax2 = xff.timeseries_plot_formatter(ax2)
        ax2.set_yticklabels([r'${0}$'.format("%d" % (y)) for y in ax2.get_yticks()])
        ax2.set_ylabel('$Last Activity Survival$'.replace(' ','\ '),
                       fontdict={'fontsize': fsize,'style': 'oblique'})

        ax2.grid(which='both', b=False, axis='x')

        ylim2 = ax2.get_ylim()[1]
        ax2.vlines([self.cinfo['start_date'],self.cinfo['end_date']], 0, ylim2, colors='Gray', lw=1.5, linestyles='--')
        ax2.set_ylim(0,ylim2)

        #Tic Labels
        datefontsize = 20
        tic_size = fsize
        for ax in [ax1,ax2]:
            for tics in ax.get_xticklabels() + ax.get_yticklabels():
                if datefontsize != None and tics in ax.get_xticklabels():
                    tics.set_fontsize(datefontsize)
                else:
                    tics.set_fontsize(tic_size)
            
                tics.set_fontname('serif')
                tics.set_style('oblique')

        figsavename = self.figpath+'last_day_dual_'+self.nickname.replace('.','_')+'.png'
        print figsavename 
        if figsavename != None:
            dpiset = 300
            #fig.savefig('OUTPUT_Figures/%s/%s_%s.png' %(mens2_cid,figsavename,nickname), bbox_inches='tight', dpi=dpiset)
            fig.savefig('%s' % (figsavename), bbox_inches='tight', dpi=dpiset)

        return None#self.enrollment_df


    def enrollment_plots_dual(self,**kwargs):
        """
        Combining enroll count and cumulative enrollment.

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
        
        fig = plt.figure(figsize=(12,6))
        ax1 = fig.add_subplot(1,1,1)

        fsize = 24

        self.enrollment_df['Enroll Count'].plot(ax=ax1,lw=3,color='Silver',label='left axis')
        ax1 = xff.timeseries_plot_formatter(ax1)
        ax1.set_yticklabels([r'${0}$'.format("%d" % (y)) for y in ax1.get_yticks()])
        ax1.set_ylabel('$Enrollment Count$'.replace(' ','\ '),
                       fontdict={'fontsize': fsize,'style': 'oblique'})

        ax1.grid(which='both', b=False, axis='x')

        ax2 = ax1.twinx()
        self.enrollment_df['Enroll Cumulative'].plot(ax=ax2,lw=3,color='Crimson',label='right axis')
        ax2 = xff.timeseries_plot_formatter(ax2)
        ax2.set_yticklabels([r'${0}$'.format("%d" % (y)) for y in ax2.get_yticks()])
        ax2.set_ylabel('$Cumulative Enrollment$'.replace(' ','\ '),
                       fontdict={'fontsize': fsize,'style': 'oblique'})

        ax2.grid(which='both', b=False, axis='x')

        ylim2 = ax2.get_ylim()[1]
        ax2.vlines([self.cinfo['start_date'],self.cinfo['end_date']], 0, ylim2, colors='Gray', lw=1.5, linestyles='--')
        ax2.set_ylim(0,ylim2)

        #Tic Labels
        datefontsize = 20
        tic_size = fsize
        for ax in [ax1,ax2]:
            for tics in ax.get_xticklabels() + ax.get_yticklabels():
                if datefontsize != None and tics in ax.get_xticklabels():
                    tics.set_fontsize(datefontsize)
                else:
                    tics.set_fontsize(tic_size)
            
                tics.set_fontname('serif')
                tics.set_style('oblique')

        figsavename = self.figpath+'enrollment_dual_'+self.nickname.replace('.','_')+'.png'
        print figsavename 
        if figsavename != None:
            dpiset = 300
            #fig.savefig('OUTPUT_Figures/%s/%s_%s.png' %(mens2_cid,figsavename,nickname), bbox_inches='tight', dpi=dpiset)
            fig.savefig('%s' % (figsavename), bbox_inches='tight', dpi=dpiset)

        return None#self.enrollment_df


    
    def enrollment_plots(self,**kwargs):
        """
        Plots using the start_date from enrollment_df.

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
        
        ### For JSON Data Output
        jsondata = []
        
        def date2epoch(x):
            return int( (datetime.combine(x, datetime.min.time()) - datetime(1970,1,1)).total_seconds()*1000 )

        for C in self.enrollment_df.columns:
            fig = plt.figure(figsize=(12,6))
            ax1 = fig.add_subplot(1,1,1)
            self.enrollment_df[C].plot(ax=ax1,color=xff.colors['institute'],rot=0,lw=3,label=self.nickname)
            
            ax1 = xff.timeseries_plot_formatter(ax1)
            ax1.set_yticklabels([r'${0}$'.format("%d" % (y)) for y in ax1.get_yticks()])
            #ax1.legend(loc=4,prop={'size':22},frameon=False,scatterpoints=1)
            
            ### Generalized Plotting functions
            figsavename = self.figpath+C.replace(' ','_')+'_'+self.nickname.replace('.','_')
            print figsavename
            xff.texify(fig,ax1,
                          ylabel=C,
                          #title=self._xdata.course_id+' - All Registrants',
                          datefontsize=20,
                          gridb='y',
                          figsavename=figsavename+'.png')

            ### Append JSON Data
            record = collections.OrderedDict()
            record['key'] = C
            if C == 'Enroll Count':
                record['bar'] = 'true'
            record['values'] = [[date2epoch(d),int(v)] for d,v in self.enrollment_df[C].iteritems()]
            jsondata.append(record)
                        
        print "JSON dump currently commented out."
        # str_jsondata = 'var data = '+json.dumps(jsondata)
        # with open(self.figpath+'enrollment.json', 'w') as outfile:
        #     outfile.write(str_jsondata)

        return None#self.enrollment_df


    def enrollment_nvd3(self):
        """
        Enrollment Plots using python-nvd3.

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
        
        from nvd3 import linePlusBarChart

        def date2epoch(x):
            return int( (datetime.combine(x, datetime.min.time()) - datetime(1970,1,1)).total_seconds()*1000 )
        
        ### Output File
        figsavename = self.figpath+'interactive_enrollment_'+self.nickname+'.html'
        output_file = open(figsavename, 'w')
        print figsavename
        
        type = "linePlusBarChart"
        chart = linePlusBarChart(name=type, height=350, x_is_date=True, x_axis_format="%d %b %Y")
        chart.set_containerheader("\n\n<h2>" + type + "</h2>\n\n")

        DATA = self.enrollment_df.copy()

        xdata = [date2epoch(x) for x in DATA.index]
        ydata = DATA['Enroll Count'].values
        ydata2 = DATA['Enroll Cumulative'].values
        #print type(xdata),type(ydata),type(ydata2)

        #Series 1
        kwargs1 = {'bar':True}
        extra_serie1 = {"tooltip": {"y_start": "", "y_end": ""},
                        "color":"CornFlowerBlue"
                        }
        chart.add_serie(name="Enrollment", y=ydata, x=xdata, extra=extra_serie1, **kwargs1)
        
        #Series 2
        kwargs2 = {'color':'Orange'}
        extra_serie2 = {"tooltip": {"y_start": "", "y_end": ""},
                        "color":"Orange"
                        }
        chart.add_serie(name="Cumulative Enrollment", y=ydata2, x=xdata, extra=extra_serie2, **kwargs2)

        chart.buildhtml()
        output_file.write(chart.htmlcontent)
        #---------------------------------------

        #close Html file
        output_file.close()

        return None#self.enrollment_df


    def last_day_plots(self,**kwargs):
        """
        Plots using the last_event date from enrollment_df.

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

        col = self.lastact_df.columns[0]
        tmp = self.lastact_df[col][self.lastact_df[col]>100]
        mindate = tmp.index[0] - timedelta(days=21)
        maxdate = tmp.index[-1] + timedelta(days=21)
        #print mindate,maxdate

        ### For JSON Data Output
        jsondata = []
        
        def date2epoch(x):
            return int( (datetime.combine(x, datetime.min.time()) - datetime(1970,1,1)).total_seconds()*1000 )

        for C in self.lastact_df.columns:
            #print C,self.lastact_df[C].idxmin(),self.lastact_df[C].idxmax()
            fig = plt.figure(figsize=(12,6))
            ax1 = fig.add_subplot(1,1,1)
            self.lastact_df[C].plot(ax=ax1,color=xff.colors['institute'],rot=0,lw=3,label=self.nickname)
            
            ax1.set_xlim(mindate,maxdate)
            ax1 = xff.timeseries_plot_formatter(ax1)
            ax1.set_yticklabels([r'${0}$'.format("%d" % (y)) for y in ax1.get_yticks()])
            #ax1.legend(loc=4,prop={'size':22},frameon=False,scatterpoints=1)
            
            ### Generalized Plotting functions
            figsavename = self.figpath+C.replace(' ','_')+'_'+self.nickname.replace('.','_')
            print figsavename
            xff.texify(fig,ax1,
                          ylabel=C,
                          #title=self._xdata.course_id+' - All Registrants',
                          datefontsize=20,
                          gridb='y',
                          figsavename=figsavename+'.png')

            ### Append JSON Data
            record = collections.OrderedDict()
            record['key'] = C
            if C == 'Last Activity Count':
                record['bar'] = 'true'
            record['values'] = [[date2epoch(d),int(v)] for d,v in self.lastact_df[C].iteritems()]
            jsondata.append(record)
                        
        print "JSON dump currently commented out."
        # str_jsondata = 'var data = '+json.dumps(jsondata)
        # with open(self.figpath+'lastday.json', 'w') as outfile:
        #     outfile.write(str_jsondata)

        return None


    def lastday_nvd3(self):
        """
        Last Day Plots using python-nvd3.

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
        
        from nvd3 import linePlusBarChart

        def date2epoch(x):
            return int( (datetime.combine(x, datetime.min.time()) - datetime(1970,1,1)).total_seconds()*1000 )
        
        ### Generalized Plotting functions
        figsavename = self.figpath+'interactive_last_activity_'+self.nickname+'.html'
        output_file = open(figsavename, 'w')
        print figsavename
        
        type = "linePlusBarChart"
        chart = linePlusBarChart(name=type, height=350, x_is_date=True, x_axis_format="%d %b %Y")
        chart.set_containerheader("\n\n<h2>" + type + "</h2>\n\n")

        ### Set Date Limits
        col = self.lastact_df.columns[0]
        tmp = self.lastact_df[col][self.lastact_df[col]>100]
        mindate = tmp.index[0] - timedelta(days=21)
        maxdate = tmp.index[-1] + timedelta(days=21)

        TRIM = self.lastact_df[(self.lastact_df.index>=mindate) & 
                               (self.lastact_df.index<=maxdate)
                              ]

        xdata = [date2epoch(x) for x in TRIM.index]
        ydata = TRIM['Last Activity Count'].values
        ydata2 = TRIM['Last Activity Survival'].values
        #print type(xdata),type(ydata),type(ydata2)

        #Series 1
        kwargs1 = {'bar':True}
        extra_serie1 = {"tooltip": {"y_start": "", "y_end": ""},
                        "color":"Silver"
                        }
        chart.add_serie(name="Last Activity Day", y=ydata, x=xdata, extra=extra_serie1, **kwargs1)
        
        #Series 2
        kwargs2 = {'color':'Orange'}
        extra_serie2 = {"tooltip": {"y_start": "", "y_end": ""},
                        "color":"Crimson"
                        }
        chart.add_serie(name="Survival Function", y=ydata2, x=xdata, extra=extra_serie2, **kwargs2)

        chart.buildhtml()
        output_file.write(chart.htmlcontent)
        #---------------------------------------

        #close Html file
        output_file.close()

        return None#self.enrollment_df



    def andrew_ho_diagram(self,**kwargs):
        """
        Plot showing the intersection of enrollment populations by categories
        defined in the 2013 (published 2014) course reports.
        http://odl.mit.edu/mitx-working-papers/ 

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

        ### Registration Types
        self.person['Only Registered'] = 0
        self.person['Only Viewed'] = 0
        self.person['Only Explored'] = 0

        g = self.person ### This is a bit silly, but keeps lines short despite the conditions.
        
        ### Create disjoint groups (note g and self.person are the same)
        #Only Registered:  A - (B+C+D) 
        reg_list = g[ (g['registered']==1) & (g['viewed']==0) & (g['explored']==0) & (g['certified']==0) ].user_id
        self.person.ix[self.person[self.person.user_id.isin(reg_list)].index,'Only Registered'] = 1

        #Only Viewed:  B - (C+D) 
        view_list = g[ (g.user_id.isin(reg_list)==False) & (g['viewed']==1) & (g['explored']==0) & (g['certified']==0) ].user_id
        self.person.ix[self.person[self.person.user_id.isin(view_list)].index,'Only Viewed'] = 1

        #Only Explored:  C - (D)
        exp_list = g[ (g.user_id.isin(reg_list)==False) & (g.user_id.isin(view_list)==False) & (g['explored']==1) & (g['certified']==0) ].user_id
        self.person.ix[self.person[self.person.user_id.isin(exp_list)].index,'Only Explored'] = 1


        ### Figure
        fig = plt.figure(figsize=(12,8))
        ax1 = fig.add_subplot(111)

        #Circles
        SCALE = 1000
        expratio = SCALE*100.*len(self.person[self.person['Only Explored']==1])/len(self.person[self.person['registered']==1])
        #print expratio
        if expratio > 17000:
            expratio = 1000
        
        certratio = SCALE*100.*len(self.person[self.person['certified']==1])/len(self.person[self.person['registered']==1])
        #print certratio
        if certratio < 1000:
            certratio = 1000
        # csize = 1000  # Ratio and csize give relative size of explored and certified circles.
        # # expl = len(self.person[self.person['Only Explored']==1])
        # # cert = len(self.person[self.person['certified']==1])

        ax1.scatter([0.45],[0.5],s=expratio,edgecolor='Black',lw=2,color='white',alpha=0.8)
        ax1.scatter([0.50],[0.5],s=certratio,edgecolor=xff.colors['institute'],lw=2,color='white',alpha=0.8)

        #Rectangles
        rect1 = matplotlib.patches.Rectangle((0,0), 1, 1,fill=False,fc='white',ec='black',lw=2)
        rect2 = matplotlib.patches.Rectangle((0.15,0.15), 0.7, 0.7,fill=False,fc='white',ec='black',lw=2)
        ax1.add_patch(rect1)
        ax1.add_patch(rect2)

        FS = 25
        ### Only registerd
        x = len(self.person[self.person['Only Registered']==1])
        y = 100.0*x/len(self.person[self.person['registered']==1])
        ax1.text(0.05,0.925,'$Only\ registered:\ %d\ \ (%.1f\%%)$' % (x,y),fontsize=FS,ha='left')
        x = len(self.person[self.person['Only Viewed']==1])
        y = 100.0*x/len(self.person[self.person['registered']==1])
        ax1.text(0.2,0.775,'$Only\ viewed:\ %d\ \ (%.1f\%%)$' % (x,y),fontsize=FS,ha='left')
        x = len(self.person[self.person['Only Explored']==1])
        y = 100.0*x/len(self.person[self.person['registered']==1])
        ax1.text(0.175,0.2,'$Only\ explored:$\n$%d\ \ (%.1f\%%)$' % (x,y),fontsize=FS,ha='left')
        x = len(self.person[self.person['certified']==1])
        y = 100.0*x/len(self.person[self.person['registered']==1])
        ax1.text(0.625,0.35,'$Certified:$\n$%d\ \ (%.1f\%%)$' % (x,y),fontsize=FS,ha='left')

        ax1.set_xlim([-0.01, 1.01])
        ax1.set_ylim([-0.01, 1.01])

        ## suppress spines
        for key in ax1.spines.keys():
            ax1.spines[key].set_color('none')

        ax1.axes.get_xaxis().set_visible(False)
        ax1.axes.get_yaxis().set_visible(False)

        ### Generalized Plotting functions
        figsavename = self.figpath+'AHO_Diagram'+'_'+self.nickname.replace('.','_')
        xff.texify(fig,ax1,
                   figsavename=figsavename+'.png')

        # ### Package data
        # jsonout = pd.Series()
        # for sg in ['Only Registered','Only Viewed','Only Explored','certified']:
        #     count = len(self.person[self.person[sg]==1].username.unique())
        #     jsonout.set_value(sg.capitalize()+'(N=%d)'%(count),count)

        # jsonout = 100.0*jsonout/jsonout.sum()

        # jsondata = []
        # for l,v in jsonout.iteritems():
        #     record = collections.OrderedDict()
        #     record['label'] = l
        #     record['value'] = v
        #     jsondata.append(record)
        
        # print "JSON dump currently commented out."                
        # # str_jsondata = 'var data = '+json.dumps(jsondata)
        # # with open(self.figpath+'percent_participanttypes.json', 'w') as outfile:
        # #     outfile.write(str_jsondata)


        return None









