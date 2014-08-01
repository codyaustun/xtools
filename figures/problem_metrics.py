import os

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import ujson as json

import xtools

class ProblemMetrics(object):
    '''
    Routines for plotting person course information. 
    '''

    def __init__(self,xdata):
        self.xdata = xdata
        # self.caxis = xdata.get('course_axis',conditions={})
        # self.caxis = self.caxis.sort('index') # Note, index is a column in the course axis collection.

        self.mens2_cid = xdata.course_id.replace('/','__')
        self.nickname = xdata.course_id.split('/')[1].replace('_','.') #'2.01x'
        self.institute = xdata.course_id.split('/')[0]#MITx
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/Problem_Metrics/'
        print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)

        ### Initiate Course Axis
        self.CS = xtools.figures.course_structure.CourseStructure(xdata)

        self.cviz_for_colors = self.CS.cviz.set_index('module_id')

        ### Load Problems from Courseware Student Module (can take a few minutes)
        self.cwsm = xdata.get('courseware_studentmodule', conditions={'course_id':xdata.course_id,'module_type':'problem'})



    def problem_attempt_figures(self):
        """
        Creates problem attempt figures for each chapter in a course.
        Each figure contains boxplots representing the distribution of attempts,
        and an overlay bubble chart indicating mean attempts and the number of 
        participants attempting the problem.
        
        Parameters (generated during class initialization)
        ----------
        cviz: provides relevant gformat, color, chapter, and module_id

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """

        ### Generate Problem Attempt Matrix
        pam = self.problem_attempt_matrix()

        for n in self.CS.caxis.chapter.unique():
            ### Identify each chapter's problems and filter the problem attempt matrix
            probs = self.CS.caxis[(self.CS.caxis.chapter==n) & (self.CS.caxis.category=='problem')].index

            ### Filter probs from pam
            matches = pam.filter(items=probs)

            ### Conditions to deal with empty chapters; note, 100 could be zero, 100 selected for MOOCs
            if len(probs) > 0 and n != 'nan' and matches.count().sum() > 100:  
                ### Set up colors and bubble size
                gformat_colors = [ self.cviz_for_colors.ix[i,'color'] if self.CS.caxis.ix[i,'gformat'] else 'Magenta' for i in matches.columns ]
                MAX = pam.count().max()

                ### Initialize Figure
                fig = plt.figure(figsize=[14,4])
                ax1 = fig.add_subplot(1,1,1)
                
                ### Matplotlib boxplot does not accept NULL values - so recast data frame values               
                vals = [matches[col].dropna().values for col in matches]

                ### Boxplots
                bp = ax1.boxplot(vals,widths=0.15)
                
                ### Scatter for mean and population size
                plt.scatter(ax1.get_xticks(),matches.mean(),
                            s=[80.*(i)/MAX for i in matches.count()],
                            c=gformat_colors,edgecolor=gformat_colors,
                            marker='s',label='mean (size ~ N)')
                
                ax1.legend(loc=2, scatterpoints=1)
                
                #ax1.set_xticklabels([r'%s' % (x.get_text().lstrip('MITx/8.02x/problem/')) for x in ax1.get_xticklabels()])
                ax1.set_xticklabels([r'%s' % (cn.split(self.institute+'/'+self.nickname+'/problem/')[1]) for cn in matches.columns],rotation=90)        
                
                if ax1.get_ylim()[1] == 1.0:
                    ax1.set_ylim(0,2)
                else:
                    ax1.set_ylim(0,)

                ax1.set_title(n)
            
                ax1.set_ylabel('attempts')
            
                fn = n.replace('/','__').replace(' ','_')
                figsavename = self.figpath+'prob_attempts_'+fn+'_'+self.nickname+'.png'
                fig.savefig(figsavename, bbox_inches='tight', dpi=300)

        return None


    def problem_attempt_matrix(self):
        """
        Create a problem attempt matrix from courseware_studentmodule
        Future: allow any problem metric to be placed inside matrix, e.g., score_matrix, time_spent_matrix
        
        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        attempts = self.cwsm.state.apply(self._parse_state_cmap2)
        attempts.name = 'attempts'

        ### Combining steps: 1) join "attempts" with self.cwsm, 2) create problem attempt matrix
        pam = pd.pivot_table( self.cwsm.join(attempts), values='attempts',rows='student_id',cols='module_id' )
        pam.columns = [x.lstrip('i4x://') for x in pam.columns]

        return pam


    def _parse_state_cmap2(self,state):        
        """
        Parses the correct map from a student's state in courseware student module. 
        Currently return only the number of attempts; note that score and correctness 
        also calculated (need efficient return of multiple values to data frame)

        Parameters
        ----------
        state : json encoded string containing problem submission information.

        Returns
        -------
        None
        """
        newstate = state.decode( 'unicode-escape' ).encode( 'utf-8' )
        attempts = None
        score = None
        try:
            Q = json.loads(newstate)
            CM = Q['correct_map']
            attempts = Q['attempts'] if Q['attempts']>0 else None
            num_parts = len(CM)
            corrects = len([1 for part in CM.values() if part['correctness'] in ['correct','partially-correct'] ] )
            partials = [part['npoints'] for part in CM.values() if part['npoints']!=None] # if partial credit
            #print partials
            
            ### Score
            if num_parts > 0 and corrects > 0:
                ### Normal Case
                score = float(corrects)/float(num_parts)
                ### Partial Credit
                if len(partials) > 0:
                    mid = CM.keys()[0].split('_')[0].replace('i4x-','').replace('-','/')
                    if mid in self.max_grades:
                        #print np.sum(partials)
                        score = score*(float(np.sum(partials))/float(self.max_grades[mid]))
                    else:
                        print "mid not found"
            else:
                score = 0.0

            #return attempts,score
            #[attempts,score]#pd.Series({'attempts':attempts, 'score':score})
            return attempts

        except:
            #print "Oops! Buggy state.\n", state
            #errfile.write("Oops! Buggy state.\n%s" % state)
            #return [attempts,score]#pd.Series({'attempts':None, 'score':None})
            return attempts
    


         
     











