
import matplotlib

colors = {'institute':'FireBrick','neutral':'Silver'}


def timeseries_plot_formatter(ax):
        """
        Routines to transform datetime axis labels to a sensible format.

        Parameters
        ----------
        ax : subplot of figure (add_subplot)

        Returns
        -------
        ax : transformed subplot
        """

        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d.%m.%Y'))
        #print data.index
        formatter = matplotlib.dates.DateFormatter('%b\n%Y')
        ### Every Day Minor Ticks
        # days   = matplotlib.dates.DayLocator()  # every day
        ### Every Sunday Minor Ticks
        sundays   = matplotlib.dates.WeekdayLocator(matplotlib.dates.SUNDAY)
        months   = matplotlib.dates.MonthLocator(bymonthday=1, interval=2)  # every two months
        ax.xaxis.set_minor_locator(sundays)
        ax.xaxis.set_major_locator(months)
        ax.xaxis.set_major_formatter(formatter)
        ax.tick_params(which='minor', length=6, color='k')
        ax.tick_params(which='major', length=10, color='k')
        return ax


def texify(fig,ax,**kwargs):
    '''
    Plot formatting for course reports.
    ax:  subplot from a defined figure.
    xlabel: str label for x-axis
    ylabel: str label for y-axis
    gridb: grid option (values=x,y,None)
    '''
    xlabel = kwargs.get('xlabel', ax.get_xlabel())
    ylabel = kwargs.get('ylabel', ax.get_ylabel())
    title = kwargs.get('title', ax.get_title())
    gridb = kwargs.get('gridb', None)
    datefontsize = kwargs.get('datefontsize',None)
    figsavename = kwargs.get('figsavename',None)
    tic_size = kwargs.get('tic_size', 30)
    label_size = kwargs.get('label_size', 30)
    watermark = kwargs.get('watermark',None)

    ## suppress spines
    for key in ax.spines.keys():
        if key not in ['left','bottom']:
            ax.spines[key].set_color('none')

    ax.grid(which='both', b=False, axis='both')
    if gridb=='x' or gridb=='y':
        ax.grid(which='both', b=True, axis=gridb)

    ax.get_xaxis().tick_bottom()   # remove unneeded ticks
    ax.get_yaxis().tick_left()

    #Axis Labels
    if xlabel != None and len(xlabel) > 1:
        ax.set_xlabel(r'$%s$'%(xlabel.replace(' ','\ ')),
            fontdict={'fontsize': label_size,'style': 'oblique'})
    if ylabel != None and len(ylabel) > 1:
        ax.set_ylabel(r'$%s$'%(ylabel.replace(' ','\ ')),
            fontdict={'fontsize': label_size,'style': 'oblique'})

    # Title
    if title != None and len(title) > 1:
        ax.set_title(r'$%s$'%(title.replace(' ','\ ')),
            fontdict={'fontsize': label_size,'style': 'oblique'})

    ax.tick_params('both', length=12, width=1, which='major')

    # Watermark
    if watermark:
        ax.text(0.5,1.,watermark, transform=ax.transAxes, color='Silver', alpha=0.5,
                horizontalalignment='right', verticalalignment='top')

    #Tic Labels
    for tics in ax.get_xticklabels() + ax.get_yticklabels():
        if datefontsize != None and tics in ax.get_xticklabels():
            tics.set_fontsize(datefontsize)
        else:
            tics.set_fontsize(tic_size)

        tics.set_fontname('serif')
        tics.set_style('oblique')

    if figsavename != None:
        dpiset = 300
        #fig.savefig('OUTPUT_Figures/%s/%s_%s.png' %(mens2_cid,figsavename,nickname), bbox_inches='tight', dpi=dpiset)
        fig.savefig('%s' % (figsavename), bbox_inches='tight', dpi=dpiset)


