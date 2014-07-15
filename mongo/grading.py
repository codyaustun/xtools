import pandas as pd
from pandas import Series, DataFrame
import numpy as np
import scipy as sp
import scipy.stats as ss
import sys
import datetime
import math
import ujson as json

class Grader(object):
    
    def __init__(self, xdata):
        '''
        This grader can calculate the grades of students from either courseware
        student module or person object time, which is a distillation of the
        tracking logs. The grades of all students are calculated at once through
        a method based largely on matrix multiplication.

        The method is compromised of three matrices: the score, 
        sequence, and weight matrices. The rows of score matrix represent
        the students while the columns represent every graded problem module in 
        the course. Each cell contains a number in the range [0,1] to express 
        the correctness of a user's answer on the module. If a user hasn't 
        attempted a module the corresponding cell is set to 0. This matrix can
        be derived from either courseware student module or person object time.

        The sequence matrix maps the contribution of each module to the grade of
        each sequence. Rows represent modules and columns represent sequences. 
        Cells range from [0,1] and represent the contribution of a single module
        to the grade of a sequence. Each column in the sequence matrix sums to 
        one. This matrix is derived from the course axis and courseware student
        module.

        The weight matrix (vector) encapsulates how the performance on each 
        sequence in a course impacts a student's overall grades. Rows represent 
        contribution of each sequential to the overall grade and there is only 1
        column. Ranging from [0,1] each cell is derived from the grading policy
        which is extracted from the course policy file. Sequences of the same
        gformat (type) contributing evenly to the overall grade.

        Using these three matrics, final grades can be contributed as follows:

            score matrix x sequence matrix x weight matrix = final grades

        Unfortunately, this equation doesn't work in practice because some
        courses allow students to drop problem sets. To circumvent this issue,
        only the score and sequence matrices are multipled together. The result
        is then process to account for drops. 

        Parameters
        ----------
        xdata : XData
            Provides methods for getting any data needed to create the 
            collection defined by this strategy as well as any additional 
            constraints
        '''
        self._xd = xdata

        # The following attributes are create upon construction since they are
        #   critical in calculating grades but independent of the score 
        #   matrix. They don't need to be recalculated for different grading 
        #   inputs
        self.grading_policy = self._grading_policy()
        self.max_grades = self._max_grades()
        self.axis = self._course_axis()

        conditions = (self.axis.category == 'sequential')
        conditions = conditions | (self.axis.category=='videosequence')
        conditions = conditions & self.axis.graded
        self.gformat_mapping = self.axis[conditions].loc[:,['name','gformat']]
        self.gformat_mapping = self.gformat_mapping.set_index('name').gformat
        
        # Only graded problems count towards the final grade, so the sequence
        #   matrix can be reduce to only include these modules
        conditions = (self.axis.graded) & (self.axis.category == 'problem')
        grading_axis = self.axis[conditions]
        grading_axis = grading_axis.loc[:,['sequential','module_id','weight']]
        
        self.sequence_matrix = grading_axis.pivot_table(\
            rows='module_id',
            cols = 'sequential',
            values = 'weight',
            ).fillna(0)

        sequence_totals = self.sequence_matrix.sum()
        self.sequence_matrix = self.sequence_matrix*1. / sequence_totals
            
    def run(self, source = 'derived_person_object_time'):
        '''
        Fetches student information from the 'source' using XData and 
        calculates the grades for all students. 

        Parameters
        ----------
        source : str
            The name of source to use to calculate grades. It can either be 
            derived_person_object_time or courseware_studentmodule.

        Returns
        -------
        grades : DataFrame
            The final grade of every student in the source indexed by username.
        '''
        # Fetches the student information from the source
        if source == 'derived_person_object_time':
            conditions = {'verb': {"$in": ['problem_save','problem_check']}}
            data = self._xd.get('derived_person_object_time',
                conditions = conditions).dropna(subset=['detail'])
        elif source == 'courseware_studentmodule':
            cols = ['student_id',
                'course_id',
                'module_id',
                'module_type',
                'max_grade',
                'state',
                'created']

            data = self._xd.get("courseware_studentmodule", fields = cols)
        else:
            raise KeyError(sources+'is a valid source')
            
        # Calculates the grades using the data collected
        grades = self.from_data(data, source = source)
        return grades

    def from_data(self, data, source = 'derived_person_object_time'):
        '''
        Calculates the grades for all students using the given data.

        Parameters
        ----------
        data : DataFrame
            Raw data from the specified source to be used for grading
        source : str
            The name of source to use to calculate grades. It can either be 
            derived_person_object_time or courseware_studentmodule.

        Returns
        -------
        grades : DataFrame
            The final grade of every student in the source indexed by username.
        '''
        # Calculates every user's grade on each problem module in the course.
        if source == 'derived_person_object_time':
            score_matrix = self._from_pot(data)
        elif source == 'courseware_studentmodule':
            score_matrix = self._from_cwsm(data)
        else:
            raise KeyError(sources+'is a valid source')

        # From the score_matrix grades are calculated
        grades = self._calculate_grades(score_matrix)
        return grades

    def _calculate_grades(self, score_matrix):
        '''
        Uses the score_matrix, sequence_matrix and weight_matrix* in order to 
        calculate the grades for every student
        
        Parameters
        ----------
        score_matrix : DataFrame
            Contains every user's grade on each problem module in the course.
            It is indexed by username with columns of module id.

        Returns
        -------
        grades : DataFrame
            The final grade of every student in the source indexed by username.
        '''
        # Since the score_matrix is calculated using student responses and the
        #   sequence_matrix is calculated using the course axis, the columns of
        #   the score_matrix and the rows of the sequence_matrix might not line
        #   up. This is fixed by ix and then sequential grades are computed.
        seqs = self.sequence_matrix.ix[score_matrix.columns.values,:].fillna(0)
        seq_grades = score_matrix.dot(seqs)

        # Grading is done based on sequential gformat (types), so the 
        #   sequential grades are mapped to these types.
        grades = seq_grades.unstack().reset_index().set_index('sequential')
        grades.rename(columns = {0: 'grade'}, inplace = True)
        grades['type'] = self.gformat_mapping
        grades = grades.reset_index()

        # Using the sequentials corresponding types, grades for each type are 
        #   calculated for every user
        grades_grouped = grades.groupby(['username', 'type'])
        grades = grades_grouped.apply(self._seq_type_grade) 

        # Using the grades on every sequential type final grades are calculated
        final = grades.reset_index().groupby('username').agg(sum)
        final.rename(columns = {0: 'grade'}, inplace = True)
        final['grade'] = final.grade.apply(lambda x: round(x+0.0049,2))
        return final


    def _grading_policy(self):
        '''
        Gets the grading policy from the course policy.

        Returns
        -------
        grading_policy : DataFrame
            Information about how grades are determined in a course.
        '''
        course_policy = self._xd.get('grading_policy')
        grading_policy = DataFrame(course_policy.iloc[0,:]['GRADER'])

        # type == the gformat of sequences
        grading_policy = grading_policy.set_index('type')

        def max_seqs(seq_type):
            '''
            Determines the max number of sequenences that should contribute to 
            a users final grade for each gformat
            '''
            return seq_type.get('min_count', 1) - seq_type.get('drop_count', 0)

        grading_policy['max_seqs'] = grading_policy.apply(max_seqs, axis = 1)

        return grading_policy
    
    def _max_grades(self):
        '''
        Uses courseware student module to calculate the most common max grade 
        value for each module. This is used to determine the relative weight of
        problems in a sequential.

        Returns
        -------
        max_grades : Series
            The maximum possible grade for every module in a course
        '''
        #  Fetches courseware Student Module
        cols = ['student_id','module_id','module_type','max_grade']
        cwsm = self._xd.get("courseware_studentmodule", fields = cols)
        cwsm = cwsm[cwsm.module_type == 'problem']
        
        # Calculates the maximum possible grade for every module in a course.
        #   The maximum possible grade can change throughput the course, so the
        #   modal maximum grade is used.
        def modal_max(group):
            '''
            Finds the modal max grade
            '''
            return group.max_grade.value_counts().idxmax()
        grades_grouped = cwsm[(cwsm.max_grade!='NULL')].groupby('module_id')
        max_grades = grades_grouped.apply(modal_max)

        # Unifies the module ids in the index to match the other data.
        raw_index = max_grades.index.to_series()
        max_grades.index = raw_index.apply(lambda x: x.replace('i4x://', ''))
        return max_grades
    
    def _course_axis(self):
        '''
        Fetches the course axis and adds additional columns 
        ('sequential', 'graded', 'weight') for grading

        Returns
        -------
        caxis : DataFrame
            A distillation of the course structure
        '''
        caxis = self._xd.get('course_axis')
        # Insure index order
        caxis['index'] = caxis['index'].apply(np.int32)
        caxis = caxis.sort('index').set_index('index')
        
        # Initialize graded column to false
        caxis['graded'] = False
        # Initialize sequential column
        caxis['sequential'] = 'nan'

        conditions = (caxis.category == 'sequential')
        conditions = conditions | (caxis.category=='videosequence')
        seq_indices = caxis[conditions].index
        graded_sequences = self.grading_policy.index.values
        
        for i, seq_index in enumerate(seq_indices):
            if i < len(seq_indices)-1:
                sequential = caxis.ix[seq_index,'name']
                seq_gformat = caxis.ix[seq_index,'gformat']
                start = seq_indices[i]
                end = seq_indices[i+1]
                caxis['sequential'][start:end] = sequential
                
                if seq_gformat in graded_sequences:
                    caxis['graded'][start:end] = True
                    
                    
        caxis = caxis.set_index('module_id')
        caxis['weight'] = self.max_grades
        caxis = caxis.reset_index()

        return caxis

    def _seq_type_grade(self, group):
        '''
        Calculates a user's grade on a specific type of sequential using all
        of their grades for that type.

        Parameters
        ----------
        group : DataFrameGroupBy
            All of the grades for a specific username and type

        Returns
        -------
        weighted : float
            The weighted grade for a user of a specific sequential type
        '''
        # Since courses have droppable psets, a weight_matrix can't be
        #   calculated and used directly. Instead the highest sequential grades
        #   are averaged and weighted according to the policy file.
        max_seqs = self.grading_policy.ix[group.name[1],'max_seqs']
        type_grade = group.grade.order(ascending = False).iloc[:max_seqs].mean()
        weighted = self.grading_policy.weight[group.name[1]]*type_grade
        return weighted

    def _from_pot(self, data):
        '''
        Generates the score matrix using information from person object time

        Parameters
        ----------
        data : DataFrame
            Server side problem save and check events from person object time

        Returns
        -------
        score_matrix : DataFrame
            Contains every user's grade on each problem module in the course.
            It is indexed by username with columns of module id.
        '''
        data['correctness'] = data.detail.apply(lambda x: x['correct'])

        high_scores = data.loc[:,['username','module_id','correctness']].\
            groupby(['username','module_id']).max().reset_index()
            
        score_matrix = high_scores.pivot_table(\
            rows='username',
            cols='module_id',
            values = 'correctness').fillna(0)
        return score_matrix
        
    def _from_cwsm(self, data):
        '''
        Generates the score matrix using information from courseware student 
        module

        Parameters
        ----------
        data : DataFrame
            Courseware student module pulled from the database

        Returns
        -------
        score_matrix : DataFrame
            Contains every user's grade on each problem module in the course.
            It is indexed by username with columns of module id.
        '''
        # BADDDDD
        # FIX THIS
        data = data.rename(columns={'student_id': 'username'})
        data['cmap'] = data['state'].apply(self._parse_state_cmap)
        score_matrix = data.pivot(\
            index='username',
            columns='module_id',
            values='cmap')

        mod_ids = score_matrix.columns.to_series()
        score_matrix.columns = mod_ids.apply(lambda x: x.replace('i4x://', ''))

        return score_matrix.fillna(0)

    def _parse_state_cmap(self, state):
        '''
        Parses a the correct map from courseware student module to calculate the
        correctness of a user's answer
        '''
        #Must decode first    
        newstate = state.decode( 'unicode-escape' ).encode( 'utf-8' )
        correct_map = json.loads(newstate).get('correct_map', None)
        if correct_map:
            total = 0.0
            correct = 0.0
            for key, val in correct_map.iteritems():
                total += 1.
                if val['correctness'] == 'correct':
                    correct += 1.
                elif val['correctness'] == 'partially-correct':
                    correct += 0.5
            if total > 0:
                correct = correct / total
            return correct
        else:
            return 0

    def _parse_state_cmap2(self,state):
        '''
        Parses a the correct map from courseware student module to calculate the
        correctness of a user's answer
        '''
        newstate = state.decode( 'unicode-escape' ).encode( 'utf-8' )
        try:
            J = json.loads(newstate)['correct_map']
            num_parts = len(J)
            corrects = len([1 for part in J.values() if part['correctness'] in ['correct','partially-correct'] ] )
            partials = [part['npoints'] for part in J.values() if part['npoints']!=None] # if partial credit
            #print partials
            if num_parts > 0 and corrects > 0:
                ### Normal Case
                score = float(corrects)/float(num_parts)
                ### Partial Credit
                if len(partials) > 0:
                    mid = J.keys()[0].split('_')[0].replace('i4x-','').replace('-','/')
                    if mid in self.max_grades:
                        #print np.sum(partials)
                        score = score*(float(np.sum(partials))/float(self.max_grades[mid]))
                    else:
                        print "mid not found"
            else:
                score = 0.0
            #print 's',score
            return score
        except:
            #print "Oops! Buggy state.\n", state
            #errfile.write("Oops! Buggy state.\n%s" % state)
            return None
