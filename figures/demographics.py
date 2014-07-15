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
        self.nickname = xdata.course_id.split('/')[1]#'2.01x'
        self.figpath = '../Analytics_Data/'+self.mens2_cid+'/Demographics/'
        print self.figpath

        ### Create Directiory if does not already exist in Analytics Data
        if not os.path.exists(self.figpath):
            os.makedirs(self.figpath)

    
    def age(self,**kwargs):
        '''
        Age distribution. 
        '''

        ### Removes those users not having the option to fill in edX registration data.
        trim_data = self.person[(self.person.registered==1) & (self.person.user_id>156633)]
        # Add age column from year_of_birth
        trim_data['age'] = trim_data['YoB'].apply(lambda x: datetime.datetime.now().year - x if isinstance(x,int) else None)

        age = trim_data.age.dropna()
        h,e = np.histogram(age.values,bins=9,range=(0,90))
        age = pd.Series(data=h,index=['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89'])
        
        certs = trim_data[trim_data.certified==1]
        if certs.username.count() > 100:
            certs = certs.age.dropna()
            h,e = np.histogram(certs.values,bins=9,range=(0,90))
            certs = pd.Series(data=h,index=['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89'])
        else:
            certs = pd.Series(index=age.index)

        age = pd.concat([age,certs],join='inner',axis=1,keys=['$Enrollees$','$Certified$']) 
        age = 100.*age/age.sum()
        #print age


        fig = plt.figure(figsize=(12,6))
        ax1 = fig.add_subplot(1,1,1)
        age.plot(ax=ax1,kind='bar',color=[xff.colors['neutral'],xff.colors['institute']],rot=40,)

        ### Plot Details
        ax1.set_xticklabels([r'$%s$' % x for x in age.index])
        ax1.set_yticklabels([r'${0}\%$'.format("%.0f" % (y)) for y in ax1.get_yticks()],fontsize=30)
        ax1.legend(loc=1,prop={'size':28},frameon=False)
        
        ### Generalized Plotting functions
        figsavename = self.figpath+'age_distribution_'+self.nickname
        print figsavename
        xff.texify(fig,ax1,xlabel='Age',ylabel=None,figsavename=figsavename+'.png')

        return None


    def gender(self,**kwargs):
        '''
        Gender distribution. 
        kind = 'pie' or 'bar'
        '''
        
        ### Removes those users not having the option to fill in edX registration data.
        trim_data = self.person[(self.person.registered==1) & (self.person.user_id>156633)]

        ### Data
        gdict =  {'f': "$Female$",'m': "$Male$",'o':"$Other$"}
        glist = ['$Female$','$Male$','$Other$']

        ### Munge and Plot
        gender = trim_data.gender.dropna().apply(lambda x: gdict[x]).value_counts()
        #print gender
        certs = trim_data[trim_data.certified==1]
        if certs.username.count() > 100:
            certs = certs.gender.dropna().apply(lambda x: gdict[x]).value_counts()
        else:
            certs = pd.Series(index=gender.index)    

        gender = pd.concat([gender,certs],join='inner',axis=1,keys=['$Enrollees$','$Certified$']) 
        gender = 100.*gender/gender.sum()

        fig = plt.figure(figsize=(12,6))
        ax1 = fig.add_subplot(1,1,1)
        gender.ix[glist,:].plot(ax=ax1,kind='bar',color=[xff.colors['neutral'],xff.colors['institute']],rot=0)

        ### Plot Details
        ax1.set_xticklabels([r'%s' % x for x in glist])
        ax1.set_yticklabels([r'${0}\%$'.format("%.0f" % (y)) for y in ax1.get_yticks()],fontsize=30)
        ax1.legend(loc=1,prop={'size':28},frameon=False)

        ### Generalized Plotting functions
        figsavename = self.figpath+'gender_distribution_'+self.nickname
        print figsavename
        xff.texify(fig,ax1,xlabel=None,ylabel='Count',figsavename=figsavename+'.png')

        # ### Output JSON Records
        # gender.name = 'value'
        # gender = gender.reset_index().rename(columns={'index':'label'})
        # gender.dropna().to_json(figsavename+'.json',orient='records')


        return None



    def level_of_education(self,**kwargs):
        '''
        Plot Level of Education Attained; typically taken from the edX enrollment questionairre.
        '''
        
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
        if trim_data[trim_data.certified==1].username.count() > 100:
            certs = trim_data[trim_data.certified==1].LoE.apply(lambda x: eddict[str(x)] if x in eddict.keys() else None).value_counts()[edlist]
        else:
            certs = pd.Series(index=edlevels.index)    

        edlevels = pd.concat([edlevels,certs],join='inner',axis=1,keys=['$Enrollees$','$Certified$']) 
        edlevels = 100.*edlevels/edlevels.sum()
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
        figsavename = self.figpath+'loe_distribution_'+self.nickname
        print figsavename
        xff.texify(fig,ax1,xlabel=None,ylabel=None,figsavename=figsavename+'.png')

        ### Output JSON Records
        #cc.name = 'value'
        #cc = cc.reset_index().rename(columns={'index':'label'})
        #cc.dropna().to_json(figsavename+'.json',orient='records')

        return None


    def country_of_origin(self,**kwargs):
        '''
        Plots top "ccnum" countries based on overall enrollment.
        
        ccnum : integer giving the top "ccnum" countries from overall enrollment.

        '''
        
        ccnum = kwargs.get('ccnum',10)

        cc = self.person.final_cc.value_counts().order(ascending=False)
        if self.person[self.person.certified==1].username.count() > 100:
            certs = self.person[self.person.certified==1].final_cc.value_counts()
        else:
            certs = pd.Series(index=cc.index)

        cc = pd.concat([cc,certs],join='inner',axis=1,keys=['$Enrollees$','$Certified$'])
        cc = cc.sort('$Enrollees$',ascending=False)[0:ccnum]
        perc = 100.*cc/cc.sum()
        #print perc

        fig = plt.figure(figsize=(12,6))
        ax1 = fig.add_subplot(1,1,1)
        perc.plot(ax=ax1,kind='bar',color=[xff.colors['neutral'],xff.colors['institute']],rot=40,)

        ### Plot Details
        ax1.set_xticklabels([r'$%s$' % x for x in perc.index])
        ax1.set_yticklabels([r'${0}\%$'.format("%.0f" % (y)) for y in ax1.get_yticks()],fontsize=30)
        ax1.legend(loc=1,prop={'size':28},frameon=False)
        
        ### Generalized Plotting functions
        figsavename = self.figpath+'country_geoloc_distribution_'+self.nickname
        print figsavename
        xff.texify(fig,ax1,xlabel='Country Code',ylabel=None,figsavename=figsavename+'.png')

        ### Output JSON Records
        #cc.name = 'value'
        #cc = cc.reset_index().rename(columns={'index':'label'})
        #cc.dropna().to_json(figsavename+'.json',orient='records')
        
        return None









