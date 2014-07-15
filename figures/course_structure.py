import xtools
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os

class CourseStructure(object):
    '''
    Routines for plotting person course information. 
    '''

    def __init__(self,xdata):
        self.xdata = xdata
        self.caxis = xdata.get('course_axis',conditions={})
        self.caxis = self.caxis.sort('index') # Note, index is a column in the course axis collection.

        self.mens2_cid = xdata.course_id.replace('/','__')
        self.nickname = xdata.course_id.split('/')[1]#'2.01x'
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/Course_Structure/'
        # print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)

        self.caxis = self.caxis[self.caxis.module_id.notnull()] 
        self.caxis = self._create_chapter_and_sequential_columns_in_caxis(self.caxis)
        self.caxis = self._handle_course_specific_issues(self.caxis)
        self.caxis = self.caxis[self.caxis.module_id.notnull()]
        
        ''' 
        3.091X 2013 FALL has duplicate module_ids. This is a temporary fix.
        '''
        self.caxis = self.caxis.drop_duplicates('module_id')

        self.caxis = self.caxis.set_index('module_id')
        #print self.caxis.head()

        ### Useful Lookup Tables for classifying gformats (used in give_weight_function)
        self.lec_video_names = ['null','Learning Sequence','Lecture Sequence','Lecture','Lesson Sequence','','Checkpoint']
        self.homework_names = ['Homework','Problem Set']
        self.exam_names = ['Final','Exam','Midterm','Midterm Exam','Midterm Exam 1','Midterm2','Midterm3','Final Exam'] 

        self.cviz = []
        for i,row in self.caxis.reset_index().iterrows():                      
            self.cviz.append(self.give_weight(i,row,self.caxis))
            #print give_weight(i,row,caxis)

        self.cviz = pd.DataFrame(self.cviz,columns=['order','scale','gformat','color','chapter','module_id','gformat_name','category'])
        #print cviz[['order','gformat','color','scale','category']].head(40)


         
    def content_touches_viz(self,horiz_w_data,certified):
        '''

        '''
        fig = plt.figure(figsize=(32,12))
        fig.subplots_adjust(hspace=.1)
        #plt.rcParams.update({'font.size': 20})
        ax1 = fig.add_subplot(2,1,1)
        ax2 = fig.add_subplot(2,1,2)

        #ax1.plot(tmp['order'],tmp['uniqU'],'o')
        bars1 = ax1.bar(horiz_w_data['order'],horiz_w_data['users'],3.0,alpha=0.8,edgecolor='none')
        #Colors the bars (this is where reindexing matters)
        for i,b in enumerate(bars1):
            flipi = i#len(tmp.index)-1-i
            if horiz_w_data.color[flipi] != 'Pink':
                bars1[i].set_facecolor(horiz_w_data.color[flipi])
                bars1[i].set_edgecolor(horiz_w_data.color[flipi])
            else:
                bars1[i].set_facecolor('none')
                bars1[i].set_edgecolor('none')
                
        #ax1.plot(tmp['order'],tmp.uniqU,'-o',color='Silver',alpha=0.8)
        ax1.set_xlabel('Course Index')
        ax1.set_ylabel('Unique Users')
        #ax1.set_xlim(0,2100)

        bars2 = ax2.bar(horiz_w_data['order'],horiz_w_data.scale,2.5,edgecolor='none')

        #Colors the bars (this is where reindexing matters)
        for i,b in enumerate(bars2):
           flipi = i#len(vert.index)-1-i
           bars2[i].set_facecolor(horiz_w_data.color[flipi])

        invert = True # Choose whether to have the CC plot left or right oriented
        ha = 'left'
        if invert == True:
            ax2.invert_yaxis()
            ha = 'right'

        ax2.axes.get_xaxis().set_ticks([])
        #ax2.set_xlim(0,500)
        ax2.axes.get_yaxis().set_ticks([])
        ax2.set_xlim(0,2100)
        ax2.set_ylim(7,-1)

        #fig.patch.set_visible(False)
        ax2.axis('off')

        #!!!!! x limits must be set together
        ax1.set_xlim(ax2.get_xlim()[0],ax2.get_xlim()[1])
        #ax1.set_ylim(0,7500)

        dpiset = 300
        if certified==True:
            figsavename = self.figpath+'content_touches_horizontal_certified_'+self.nickname+'.png'
        else:
            figsavename = self.figpath+'content_touches_horizontal_'+self.nickname+'.png'
        
        fig.savefig(figsavename, bbox_inches='tight', dpi=dpiset)

        return None


    def vertical_viz(self):
        '''
        Produces a vertically oriented visualization of the course axis. See 2014 MITx Working papers for examples.
        '''

        fig = plt.figure(figsize=(9,28))
        ax1 = fig.add_subplot(1,1,1)

        vert = self.cviz.copy()

        colors = ['Orange','Black','Silver','Green','CornFlowerBlue','Crimson']
        bars = ax1.barh(vert['order'],vert.scale,2.5,edgecolor='none')
        #print vert.scale

        for i,b in enumerate(bars):
            bars[i].set_facecolor(vert.color[i])

            
        #if self.xdata.course_id != 'MMITx/8.MReV/2013_Summer':    
        for i,row in vert[['chapter','order','gformat','scale']].drop_duplicates('chapter').iterrows():
            #print row['chapter']
            removewords = ['Introduction','Survey','Old','practice','nan',
                            'TEALsim','Panel','Overview','Foldit',
                            'Biology','Homework','Office','Optional','Grounds','Practice','Spring 2012']

            if len([j for j, x in enumerate(removewords) if x in row['chapter']]) == 0:
                if ':' in row['chapter']:
                    row['chapter'] = 'Unit '+row['chapter'].split(':')[0]
                
                exams = ['Exam', 'Midterm', 'Quiz', 'Final']
                if len([i for i, x in enumerate(exams) if x in row['chapter']]) > 0:
                    x = 5.0
                    y = row['order']
                    va = 'bottom'
                    ha = 'right'
                    if self.xdata.course_id == 'MITx/2.01x/2013_Spring':
                        y = y -20
                else:
                    x = -1.65
                    y = row['order']
                    va = 'top'
                    ha = 'left'
                
                if self.xdata.course_id == 'MITx/2.01x/2013_Spring':
                    row['chapter'] = row['chapter'].split('&')[0]
                                    
                t = '$'+row['chapter'].replace('Risk and ','Risk and$\n$').replace('Axial ','Axial$\n$').replace('_',' ').replace(' ','\ ')+'$'
                ax1.text(x,y,t,fontsize=20,va=va,ha=ha)
            
        ax1.axes.get_xaxis().set_ticks([])
        ax1.axes.get_yaxis().set_ticks([])
        ax1.set_xlim(-1.75,5.5)

        maxy = 0
        miny = len(self.caxis)
        for i,v in enumerate(vert.scale):
            if v>0.0 and maxy==0: 
                maxy=i

                
        ax1.set_ylim(-30+maxy,miny+30)

        dpiset = 300
        figsavename = self.figpath+'vertical_course_viz'+'_'+self.nickname+'.png'
        fig.savefig(figsavename, bbox_inches='tight', dpi=dpiset)

        return None


    def horizontal_viz(self):
        '''
        Produces a horizontally oriented visualization of the course axis. 
        '''

        # Change Orientation Back
        horiz = self.cviz.copy()
        #print horiz.head(20)
        horiz['order'] = horiz['order'].apply(lambda x: len(horiz)-1-x)
        #print horiz.head(20)

        fig = plt.figure(figsize=(36,6))
        ax1 = fig.add_subplot(1,1,1)

        colors = ['Orange','Black','RoyalBlue','Green','Silver','Crimson']
        bars = ax1.bar(horiz['order'],horiz.scale,2.0,edgecolor='none')

        #Colors the bars (this is where reindexing matters)
        for i,b in enumerate(bars):
           flipi = i#len(vert.index)-1-i
           bars[i].set_facecolor(horiz.color[flipi])

        invert = True # Choose whether to have the CC plot left or right oriented
        ha = 'left'
        if invert == True:
            ax1.invert_yaxis()
            ha = 'right'

        ax1.axes.get_xaxis().set_ticks([])
        ax1.axes.get_yaxis().set_ticks([])
        ax1.set_ylim(7,-1)
        
        maxx = 0
        minx = len(self.caxis)
        for i,v in enumerate(horiz.scale):
            if v>0.0 and maxx==0: 
                maxx=i

                
        ax1.set_xlim(-30+maxx,minx+30)

        dpiset = 300
        figsavename = self.figpath+'horizontal_course_viz'+'_'+self.nickname+'.png'
        fig.savefig(figsavename, bbox_inches='tight', dpi=dpiset)

        return horiz


    def _handle_course_specific_issues(self,caxis):
        ### Course Specific Issues
        if '6.002x' in self.xdata.course_id:
            ### Final Exam
            nanchap = caxis[(caxis.chapter=='nan') & (caxis.gformat=='Final')].index
            #print nanchap
            for i in nanchap:
                #caxis.ix[nanchap,'gformat'] = 'Final'
                caxis.ix[nanchap,'chapter'] = 'Final Exam'
                
            ### Lecture Sequences
            nanchap = caxis[(caxis.category.isin(['video','problem'])) ].index
            print len(nanchap)
            

        if self.xdata.course_id == 'MITx/6.002x/2013_Spring':
            vi = caxis[(caxis.category=='video') & (caxis.gformat.isnull()) & (caxis.sequential.str.contains('Tutorial')==False)].index
            caxis.ix[vi,'gformat'] = 'Lecture Sequence'
            pi = caxis[(caxis.category=='problem') & (caxis.gformat.isnull())].index
            caxis.ix[pi,'gformat'] = 'Lecture Sequence'            

        if '7.00x' in self.xdata.course_id:
            caxis = caxis[caxis.chapter!='nan']

        return caxis



    def _create_chapter_and_sequential_columns_in_caxis(self,caxis):    
        caxis = caxis.reset_index()
        
        ### Chapters
        ### Initialize chapter column
        caxis['chapter'] = 'nan'
        chap_indices = caxis[caxis.category=='chapter'].index
        #print chap_indices
        for i, v in enumerate(chap_indices):
            if i < len(chap_indices)-1:
                chapter = caxis.ix[v,'name']
                start = chap_indices[i]
                end = chap_indices[i+1]
                # caxis = chap_indices[i]  and  end = chap_indices[i+1]; caxis['chapter'][start:end]
                caxis['chapter'][start:end] = chapter
                #print chapter
        
        ### Sequentials
        ### Initialize sequential column
        caxis['sequential'] = 'nan'
        seq_indices = caxis[caxis.category=='sequential'].index
        #print seq_indices
        for i, v in enumerate(seq_indices):
            if i < len(seq_indices)-1:
                sequential = caxis.ix[v,'name']
                start = seq_indices[i]
                end = seq_indices[i+1]
                # start = chap_indices[i]  and  end = chap_indices[i+1]; caxis['chapter'][start:end]
                caxis['sequential'][start:end] = sequential
                #print chapter
        
        return caxis

    def give_weight(self,i,row,caxis):
        l = 1.0*i#/len(caxis)
        #print row['category'],row['gformat']
        scale = 0
        color = 'White'
        name = 'Other'        
        
        if row['category'] != None and row['gformat'] != None:
            #Lecture videos
            if row['category'] in ['video','html'] and (row['gformat'] in self.lec_video_names or 'minutes' in row['gformat']):
                scale = 0.5
                color = 'Orange'
                name = 'Lec. Video'
            #Lecture questions
            elif row['category'] == 'problem' and (row['gformat'] in self.lec_video_names or 'minutes' in row['gformat']):
                scale = 1.0
                color = 'Black'
                name = 'Lec. Question'
            #Tutorial Videos
            elif row['category'] == 'sequential' and (row['name'] in ['Deep Dives','Tutorial Index'] or row['gformat'] in ['Problem Solving']):
                scale = 2.0
                color = 'CornFlowerBlue'
                name = 'Tutorial Videos'
            #Lab
            elif row['category'] in ['problem','foldit'] and row['gformat'] in ['Lab','TEALsim','foldit']:
                scale = 3.0
                color = 'Green'
                name = 'Lab'
            #Lab 7.00x
            elif row['sequential'] in ['Lab Video','Lab Videos']:
                scale = 2.5
                color = 'Green'
                name = 'Lab'
            #Homework
            elif row['category'] == 'problem' and (row['gformat'] in self.homework_names or 'Homework' in row['gformat']):
                scale = 4.0
                color = 'Silver'
                name = 'Homework'
            #Exams
            elif row['category'] == 'problem' and (row['gformat'] in self.exam_names or 'Quiz' in row['gformat']):
                scale = 5.0
                color = 'Crimson'
                name = 'Exam'
                
        return (len(caxis)-l,scale,name,color,row['chapter'],row['module_id'],row['gformat'],row['category'])    

