import xtools
import pandas as pd
import matplotlib.pyplot as plt
import xtools.figures.formats as xff
import os
import datetime
import numpy as np

class Demographics(object):
    '''
    Routines for plotting person course information. 
    '''

    def __init__(self,xdata):
        self._xd = xdata
        self.person = xdata.get('person_course',conditions={})
                
        self.mens2_cid = xdata.course_id.replace('/','__')
        self.nickname = xdata.course_id.split('/')[1].replace('_','.') #'2.01x'
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/Demographics/'
        print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)

        self.mincerts = 40 #Threshold for plotting certificate earners (21W.789x reason for 40)

    
    def age(self,**kwargs):
        """
        Creates gender distribution figures.
       
        Parameters (generated during class initialization)
        ----------
        NVD3 = False.  If true, nvd3 interactive figure output.

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """

        NVD3 = kwargs.get('NVD3',False)

        ### Removes those users not having the option to fill in edX registration data.
        trim_data = self.person[(self.person.registered==1) & (self.person.user_id>156633)]
        # Add age column from year_of_birth
        trim_data['age'] = trim_data['YoB'].apply(lambda x: datetime.datetime.now().year - x if isinstance(x,int) else None)

        age = trim_data.age.dropna()
        h,e = np.histogram(age.values,bins=9,range=(0,90))
        age = pd.Series(data=h,index=['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89'])
        
        certs = trim_data[trim_data.certified==1]
        if certs.username.count() > self.mincerts:
            certs = certs.age.dropna()
            h,e = np.histogram(certs.values,bins=9,range=(0,90))
            certs = pd.Series(data=h,index=['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89'])
        else:
            certs = pd.Series(index=age.index)

        age = pd.concat([age,certs],join='inner',axis=1,keys=['$Non-Certified$','$Certified$']) 
        age = 100.*age/age.sum()
        age = age.apply(lambda x: np.round(x,1))
        #print age



        #----------------------------------------------------------------
        ### Static Matplotlib PNG
        fig = plt.figure(figsize=(12,6))
        ax1 = fig.add_subplot(1,1,1)
        age.plot(ax=ax1,kind='bar',color=[xff.colors['neutral'],xff.colors['institute']],rot=40,)

        ### Plot Details
        ax1.set_xticklabels([r'$%s$' % x for x in age.index])
        ax1.set_yticklabels([r'${0}\%$'.format("%.0f" % (y)) for y in ax1.get_yticks()],fontsize=30)
        ax1.legend(loc=1,prop={'size':28},frameon=False)
        
        ### Generalized Plotting functions
        figsavename = self.figpath+'age_distribution_'+self.nickname.replace('.','_')
        print figsavename
        xff.texify(fig,ax1,xlabel='Age',ylabel=None,figsavename=figsavename+'.png')

        #----------------------------------------------------------------
        ### NVD3 Interactive http://nvd3.org/
        if NVD3:
            ### FIGURE
            from nvd3 import multiBarChart

            ### Output File
            figsavename = self.figpath+'interactive_age_distribution_'+self.nickname+'.html'
            output_file = open(figsavename, 'w')
            print figsavename

            title = "Age Distribution: %s" % self._xd.course_id
            charttype = 'multiBarChart'
            chart = multiBarChart(name=charttype, height=350, x_axis_format="", y_axis_format=".1f")
            chart.set_containerheader("\n\n<h2>" + title + "</h2>\n\n")
            nb_element = len(age)
            X = age.index #list(range(nb_element))
            Y1 = age['$Non-Certified$'].values
            Y2 = age['$Certified$'].values

            ### Series 1
            extra_serie1 = {"tooltip": {"y_start": "", "y_end": "%"},
                            "color":xff.colors['neutral'],
                            "format":".1f"
                            }
            chart.add_serie(name="Participants", y=Y1, x=X, extra=extra_serie1)
            
            ### Series 2
            extra_serie2 = {"tooltip": {"y_start": "", "y_end": "%"},
                            "color":xff.colors['institute'],
                            "format":".1f"
                            }
            chart.add_serie(name="Certificate Earners", y=Y2, x=X, extra=extra_serie2)
            
            ### Final Output
            chart.buildhtml()
            output_file.write(chart.htmlcontent)

            #---------------------------------------

            #close Html file
            output_file.close()


        return None


    # def age_nvd3(self):
    #     """
    #     Age plot for all participants and certificate earners using python-nvd3.

    #     Parameters
    #     ----------
    #     None
        
    #     Output
    #     ------
    #     html file with all necessary data and javascript references.

    #     Returns
    #     -------
    #     None
    #     """

    #     ### Data Munging
    #     ### Removes those users not having the option to fill in edX registration data.
    #     trim_data = self.person[(self.person.registered==1) & (self.person.user_id>156633)]
    #     # Add age column from year_of_birth
    #     trim_data['age'] = trim_data['YoB'].apply(lambda x: datetime.datetime.now().year - x if isinstance(x,int) else None)

    #     age = trim_data.age.dropna()
    #     h,e = np.histogram(age.values,bins=9,range=(0,90))
    #     age = pd.Series(data=h,index=['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89'])
        
    #     certs = trim_data[trim_data.certified==1]
    #     if certs.username.count() > self.mincerts:
    #         certs = certs.age.dropna()
    #         h,e = np.histogram(certs.values,bins=9,range=(0,90))
    #         certs = pd.Series(data=h,index=['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89'])
    #     else:
    #         certs = pd.Series(index=age.index)

    #     age = pd.concat([age,certs],join='inner',axis=1,keys=['$Non-Certified$','$Certified$']) 
    #     age = 100.*age/age.sum()
    #     age = age.apply(lambda x: np.round(x,1))
    #     #print age


    #     ### FIGURE
    #     from nvd3 import multiBarChart

    #     ### Output File
    #     figsavename = self.figpath+'interactive_age_distribution_'+self.nickname+'.html'
    #     output_file = open(figsavename, 'w')
    #     print figsavename

    #     title = "Age Distribution: %s" % self._xd.course_id
    #     chart = multiBarChart(name=title, height=350, x_axis_format="", y_axis_format=".1f")
    #     chart.set_containerheader("\n\n<h2>" + title + "</h2>\n\n")
    #     nb_element = len(age)
    #     X = age.index #list(range(nb_element))
    #     Y1 = age['$Non-Certified$'].values
    #     Y2 = age['$Certified$'].values

    #     ### Series 1
    #     extra_serie1 = {"tooltip": {"y_start": "", "y_end": "%"},
    #                     "color":xff.colors['neutral']],
    #                     "format":".1f"
    #                     }
    #     chart.add_serie(name="Participants", y=Y1, x=X, extra=extra_serie1)
        
    #     ### Series 2
    #     extra_serie2 = {"tooltip": {"y_start": "", "y_end": "%"},
    #                     "color":xff.colors['institute']],
    #                     "format":".1f"
    #                     }
    #     chart.add_serie(name="Certificate Earners", y=Y2, x=X, extra=extra_serie2)
        
    #     ### Final Output
    #     chart.buildhtml()
    #     output_file.write(chart.htmlcontent)

    #     #---------------------------------------

    #     #close Html file
    #     output_file.close()

    #     return None


    def gender(self,**kwargs):
        """
        Creates gender distribution figures.
       
        Parameters (generated during class initialization)
        ----------
        NVD3 = False.  If true, nvd3 interactive figure output.

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """
        
        NVD3 = kwargs.get('NVD3',False)

        ### Removes those users not having the option to fill in edX registration data.
        trim_data = self.person[(self.person.registered==1) & (self.person.user_id>156633)]

        ### Data
        gdict =  {'f': "$Female$",'m': "$Male$",'o':"$Other$"}
        glist = ['$Female$','$Male$']

        ### Munge and Plot
        gender = trim_data.gender.dropna().apply(lambda x: gdict[x]).value_counts()
        #print gender
        certs = trim_data[trim_data.certified==1]
        if certs.username.count() > self.mincerts:
            certs = certs.gender.dropna().apply(lambda x: gdict[x]).value_counts()
        else:
            certs = pd.Series(index=gender.index)    

        gender = pd.concat([gender,certs],join='inner',axis=1,keys=['$Non-Certified$','$Certified$']) 
        gender = 100.*gender/gender.sum()
        gender = gender.apply(lambda x: np.round(x,1))

        fig = plt.figure(figsize=(12,6))
        ax1 = fig.add_subplot(1,1,1)
        gender.ix[glist,:].plot(ax=ax1,kind='bar',color=[xff.colors['neutral'],xff.colors['institute']],rot=0)

        ### Plot Details
        ax1.set_xticklabels([r'%s' % x for x in glist])
        ax1.set_yticklabels([r'${0}\%$'.format("%.0f" % (y)) for y in ax1.get_yticks()],fontsize=30)
        ax1.legend(loc=2,prop={'size':28},frameon=False)

        ### Generalized Plotting functions
        figsavename = self.figpath+'gender_distribution_'+self.nickname.replace('.','_')
        print figsavename
        xff.texify(fig,ax1,xlabel=None,ylabel='Count',figsavename=figsavename+'.png')

        # ### Output JSON Records
        # gender.name = 'value'
        # gender = gender.reset_index().rename(columns={'index':'label'})
        # gender.dropna().to_json(figsavename+'.json',orient='records')


        #----------------------------------------------------------------
        ### NVD3 Interactive http://nvd3.org/
        if NVD3:
            
            'http://nvd3.org/examples/pie.html'
            

            X = [ x.replace('$','') for x in gender.index ]
            Y1 = gender.ix[glist,'$Non-Certified$'].values
            Y2 = gender.ix[glist,'$Certified$'].values

            #----------------------------------------------------------------
            ### BAR Chart
            from nvd3 import multiBarChart

            ### Output File
            figsavename = self.figpath+'interactive_gender_distribution_'+self.nickname+'.html'
            output_file = open(figsavename, 'w')
            print figsavename

            title = "Gender Distribution: %s" % self._xd.course_id
            charttype = 'multiBarChart'
            chart = multiBarChart(name=charttype, height=350, x_axis_format="", y_axis_format=".1f")
            chart.set_containerheader("\n\n<h2>" + title + "</h2>\n\n")
            nb_element = len(gender.ix[glist,:])
            

            ### Series 1
            extra_serie1 = {"tooltip": {"y_start": "", "y_end": "%"},
                            "color":xff.colors['neutral'],
                            "format":".1f"
                            }
            chart.add_serie(name="Participants", y=Y1, x=X, extra=extra_serie1)
            
            ### Series 2
            extra_serie2 = {"tooltip": {"y_start": "", "y_end": "%"},
                            "color":xff.colors['institute'],
                            "format":".1f"
                            }
            chart.add_serie(name="Certificate Earners", y=Y2, x=X, extra=extra_serie2)
            
            ### Final Output
            chart.buildhtml()
            output_file.write(chart.htmlcontent)

            #---------------------------------------

            #close Html file
            output_file.close()


            #----------------------------------------------------------------
            ### Pie Chart
            from nvd3 import pieChart

            ### Output File
            figsavename = self.figpath+'interactive_gender_piechart_'+self.nickname+'.html'
            output_file = open(figsavename, 'w')
            print figsavename

            title = "Gender Pie Chart: %s" % self._xd.course_id
            charttype = 'multiBarChart'
            chart = pieChart(name=charttype, color_category='category20c', height=400, width=400)
            chart.set_containerheader("\n\n<h2>" + title + "</h2>\n\n")

            extra_serie = {"tooltip": {"y_start": "", "y_end": " certified"}}

            chart.add_serie(y=Y1, x=X, extra=extra_serie)
            
            ### Final Output
            chart.buildhtml()
            output_file.write(chart.htmlcontent)

            #---------------------------------------

            #close Html file
            output_file.close()



        return None


    def level_of_education(self,**kwargs):
        '''
        Plot Level of Education Attained; typically taken from the edX enrollment questionairre.
        '''
        """
        Creates distribution of highest level of education attained.
       
        Parameters (generated during class initialization)
        ----------
        NVD3 = False.  If true, nvd3 interactive figure output.

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """
        
        NVD3 = kwargs.get('NVD3',False)

        ### Level of Education (LoE)
        ### Data
        eddict = {'el': "Less\ than$\n$ Secondary",'jhs': "Less\ than$\n$ Secondary",'none':"Less\ than$\n$ Secondary",
                  'hs':"Secondary",'a':"Secondary",
                  'b':"Bachelor\'s",
                  'm': "Master\'s",
                  'p_se': "Doctorate",'p_oth': "Doctorate",'p': "Doctorate",
                  'other': None,'NA':None,'nan':None,
                  }

        edlist = ["Less\ than$\n$ Secondary","Secondary","Bachelor\'s","Master\'s","Doctorate"]
        trim_data = self.person[(self.person.registered==1) & (self.person.user_id>156633)]
        
        edlevels = trim_data.LoE.apply(lambda x: eddict[str(x)] if x in eddict.keys() else None).value_counts()[edlist]
        if trim_data[trim_data.certified==1].username.count() > self.mincerts:
            certs = trim_data[trim_data.certified==1].LoE.apply(lambda x: eddict[str(x)] if x in eddict.keys() else None).value_counts()[edlist]
        else:
            certs = pd.Series(index=edlevels.index)    

        edlevels = pd.concat([edlevels,certs],join='inner',axis=1,keys=['$Non-Certified$','$Certified$']) 
        edlevels = 100.*edlevels/edlevels.sum()
        edlevels = edlevels.apply(lambda x: np.round(x,1))

        #print edlevels
        
        #Plot
        fig = plt.figure(figsize=(12,6))
        ax1 = fig.add_subplot(1,1,1)
        
        edlevels.plot(ax=ax1,kind='bar',color=[xff.colors['neutral'],xff.colors['institute']],rot=40)
        
        ### Plot Details
        ax1.set_xticklabels([r'$%s$' % x for x in edlist])
        ax1.set_yticklabels([r'${0}\%$'.format("%.0f" % (y)) for y in ax1.get_yticks()],fontsize=30)
        ax1.legend(loc=2,prop={'size':22},frameon=False)
        
        ### Generalized Plotting functions
        figsavename = self.figpath+'loe_distribution_'+self.nickname.replace('.','_')
        print figsavename
        xff.texify(fig,ax1,xlabel=None,ylabel=None,figsavename=figsavename+'.png')

        ### Output JSON Records
        #cc.name = 'value'
        #cc = cc.reset_index().rename(columns={'index':'label'})
        #cc.dropna().to_json(figsavename+'.json',orient='records')


        #----------------------------------------------------------------
        ### NVD3 Interactive http://nvd3.org/
        if NVD3:
            ### FIGURE
            from nvd3 import multiBarChart

            ### Output File
            figsavename = self.figpath+'interactive_edlevel_distribution_'+self.nickname+'.html'
            output_file = open(figsavename, 'w')
            print figsavename

            title = "Education Level Distribution: %s" % self._xd.course_id
            charttype = 'multiBarChart'

            chart = multiBarChart(name=charttype, height=350, x_axis_format="", y_axis_format=".1f")
            chart.set_containerheader("\n\n<h2>" + title + "</h2>\n\n")
            nb_element = len(edlevels)
            X = [ x.replace('\ ',' ').replace('$\n$',' ') for x in edlevels.index ] #list(range(nb_element))
            Y1 = edlevels.ix[:,'$Non-Certified$'].values
            Y2 = edlevels.ix[:,'$Certified$'].values

            ### Series 1
            extra_serie1 = {"tooltip": {"y_start": "", "y_end": "%"},
                            "color":xff.colors['neutral'],
                            "format":".1f"
                            }
            chart.add_serie(name="Participants", y=Y1, x=X, extra=extra_serie1)
            
            ### Series 2
            extra_serie2 = {"tooltip": {"y_start": "", "y_end": "%"},
                            "color":xff.colors['institute'],
                            "format":".1f"
                            }
            chart.add_serie(name="Certificate Earners", y=Y2, x=X, extra=extra_serie2)
            
            ### Final Output
            chart.buildhtml()
            output_file.write(chart.htmlcontent)

            #---------------------------------------

            #close Html file
            output_file.close()


        return None


    def country_of_origin(self,**kwargs):
        """
        Creates figures for the top "ccnum" of enrolled countries.
       
        Parameters (generated during class initialization)
        ----------
        ccnum = number of requested countries to be plotted. Max 25 for plotting issues.
        NVD3 = False.  If true, nvd3 interactive figure output.

        Output
        ------
        Saves figures to specified directories.

        Returns
        -------
        None
        """
        
        NVD3 = kwargs.get('NVD3',False)

        ccnum = kwargs.get('ccnum',10)

        cc = self.person.final_cc.value_counts().order(ascending=False)
        if self.person[self.person.certified==1].username.count() > self.mincerts:
            certs = self.person[self.person.certified==1].final_cc.value_counts()
        else:
            certs = pd.Series(index=cc.index)

        cc = pd.concat([cc,certs],join='inner',axis=1,keys=['$Non-Certified$','$Certified$'])
        cc = cc.sort('$Non-Certified$',ascending=False)[0:ccnum]
        perc = 100.*cc/cc.sum()
        perc = perc.apply(lambda x: np.round(x,1))
        #print perc

        fig = plt.figure(figsize=(12,6))
        ax1 = fig.add_subplot(1,1,1)
        perc.plot(ax=ax1,kind='bar',color=[xff.colors['neutral'],xff.colors['institute']],rot=40,)

        ### Plot Details
        ax1.set_xticklabels([r'$%s$' % x for x in perc.index])
        ax1.set_yticklabels([r'${0}\%$'.format("%.0f" % (y)) for y in ax1.get_yticks()],fontsize=30)
        ax1.legend(loc=1,prop={'size':28},frameon=False)
        
        ### Generalized Plotting functions
        figsavename = self.figpath+'country_geoloc_distribution_'+self.nickname.replace('.','_')
        print figsavename
        xff.texify(fig,ax1,xlabel='Country Code',ylabel=None,figsavename=figsavename+'.png')

        ### Output JSON Records
        #cc.name = 'value'
        #cc = cc.reset_index().rename(columns={'index':'label'})
        #cc.dropna().to_json(figsavename+'.json',orient='records')
        

        #----------------------------------------------------------------
        ### NVD3 Interactive http://nvd3.org/
        if NVD3:
            ### FIGURE
            from nvd3 import multiBarChart

            ### Output File
            figsavename = self.figpath+'interactive_country_distribution_'+self.nickname+'.html'
            output_file = open(figsavename, 'w')
            print figsavename

            title = "Education Level Distribution: %s" % self._xd.course_id
            charttype = 'multiBarChart'
            chart = multiBarChart(name=charttype, height=350, x_axis_format="", y_axis_format=".1f")
            chart.set_containerheader("\n\n<h2>" + title + "</h2>\n\n")
            nb_element = len(perc)
            X = perc.index #list(range(nb_element))
            Y1 = perc.ix[:,'$Non-Certified$'].values
            Y2 = perc.ix[:,'$Certified$'].values

            ### Series 1
            extra_serie1 = {"tooltip": {"y_start": "", "y_end": "%"},
                            "color":xff.colors['neutral'],
                            "format":".1f"
                            }
            chart.add_serie(name="Participants", y=Y1, x=X, extra=extra_serie1)
            
            ### Series 2
            extra_serie2 = {"tooltip": {"y_start": "", "y_end": "%"},
                            "color":xff.colors['institute'],
                            "format":".1f"
                            }
            chart.add_serie(name="Certificate Earners", y=Y2, x=X, extra=extra_serie2)
            
            ### Final Output
            chart.buildhtml()
            output_file.write(chart.htmlcontent)

            #---------------------------------------

            #close Html file
            output_file.close()

        return None









