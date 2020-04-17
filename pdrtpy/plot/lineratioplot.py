#todo: 
# document
#
#todo: use matplotlib contourf to shade the area between +/- error rather than use dashed lines
#
# raise appropriate exceptions 
#
# Look into seaborn https://seaborn.pydata.org
# Also https://docs.bokeh.org/en
# especially for coloring and style

from copy import deepcopy

import numpy as np
import numpy.ma as ma
import scipy.stats as stats

import matplotlib.figure
import matplotlib.colors as mpcolors
import matplotlib.cm as mcm
from matplotlib import ticker
from matplotlib.lines import Line2D

from astropy.nddata.utils import Cutout2D
from astropy.io import fits
import astropy.wcs as wcs
import astropy.units as u
from astropy.nddata import NDDataArray, CCDData, NDUncertainty, StdDevUncertainty, VarianceUncertainty, InverseVariance

from .plotbase import PlotBase
from ..pdrutils import to

rad_title = dict()
rad_title['Habing'] = '$G_0$'
rad_title['Draine'] = '$\chi$'
rad_title['Mathis'] = 'ISRF$_{Mathis}$'

class LineRatioPlot(PlotBase):
    """Class to plot various results from PDR Toolbox model fitting.
    

    :Keyword Arguments:

    To manage the plots, the methods in this class take keywords (\*\*kwargs) that turn on or off various options, specify plot units, or map to matplotlib's :meth:`~matplotlib.axes.Axes.plot`, :meth:`~matplotlib.axes.Axes.imshow`, :meth:`~matplotlib.axes.Axes.contour` keywords.  The methods have reasonable defaults, so try them with no keywords to see what they do before modifying keywords.

     * *units* (``str`` or :class:`astropy.units.Unit`) data units to use in the plot. This can be either a string such as, 'cm^-3' or 'Habing', or it can be an :class:`astropy.units.Unit`.  Data will be converted to the desired unit. 

     * *image* (``bool``) whether or not to display the image map (imshow). 
     * *cmap* (``str``) colormap name, Default: 'plasma' 

     * *contours* (``bool``), whether or not to plot contours

     * *label* (``bool``), whether or not to label contours 

     * *linewidth* (``float``), the line width in points, Default: 1.0

     * *levels* (``int`` or array-like) Determines the number and positions of the contour lines / regions.  If an int n, use n data intervals; i.e. draw n+1 contour lines. The level heights are automatically chosen.  If array-like, draw contour lines at the specified levels. The values must be in increasing order.  

     * *norm* (``str`` or :mod:`astropy.visualization` normalization object) The normalization to use in the image. The string 'simple' will normalize with :func:`~astropy.visualization.simple_norm` with a log stretch and 'zscale' will normalize with IRAF's zscale algorithm.  See :class:`~astropy.visualization.ZScaleInterval`.

     * *aspect* (``str``) aspect ratio, 'equal' or 'auto' are typical defaults.

     * *origin* (``str``) Origin of the image. Default: 'lower'

     * *title* (``str``) A title for the plot.  LaTeX allowed.

     * *vmin*  (``float``) Minimum value for colormap normalization

     * *vmax*  (``float``) Maximum value for colormap normalization

     The following keywords are available, but you probably won't touch.

     * *nrows* (``int``) Number of rows in the subplot

     * *ncols* (``int``) Number of columns in the subplot

     * *index* (``int``) Index of the subplot

     * *reset* (``bool``) Whether or not to reset the figure.

     Providing keywords other than these has undefined results, but may just work!
       
    """

    def __init__(self,tool):
        """Init method

           :param tool: The line ratio fitting tool that is to be plotted.
           :type tool: `~pdrtpy.tool.LineRatioFit`
        """

        super().__init__(tool)
        self._figure = None
        self._axis = None
        self._ratiocolor=[]
        self._CB_color_cycle = ['#377eb8', '#ff7f00', '#4daf4a',
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999', '#e41a1c', '#dede00']

    def modelratio(self,id,**kwargs):
        """Plot one of the model ratios
     
           :param id: the ratio identifier, such as ``CII_158/CO_32``.
           :type id: str
           :param \**kwargs: see class documentation above
           :raises KeyError: if is id not in existing model ratios

        """
        if len(self._tool._modelratios[id].shape) == 0:
            return self._tool._modelratios[id]

        kwargs_opts = {'title': self._tool._modelset.table.loc[id]["title"], 'units': u.dimensionless_unscaled }
        kwargs_opts.update(kwargs)
        self._plot(self._tool._modelratios[id],**kwargs_opts)

    def observedratio(self,id,**kwargs):
        """Plot one of the observed ratios

           :param id: the ratio identifier, such as ``CII_158/CO_32``.
           :type id: - str
           :raises KeyError: if id is not in existing observed ratios
        """
        if len(self._tool._observedratios[id].shape) == 0:
            return self._tool._observedratios[id]

        kwargs_opts = {'title': self._tool._modelset.table.loc[id]["title"], 'units': u.dimensionless_unscaled }
        kwargs_opts.update(kwargs)
        self._plot(data=self._tool._observedratios[id],**kwargs_opts)

    def density(self,**kwargs):
        '''Plot the density map that was computed by :class:`~pdrtpy.tool.lineratiofit.LineRatioFit` tool. Default units: cm :math:`^{-3}`
        '''
        kwargs_opts = {'units': 'cm^-3',
                       'image':True,
                       'contours': False,
                       'label': False,
                       'linewidth': 1.0,
                       'levels': None,
                       'norm': None,
                       'title': None}

        kwargs_opts.update(kwargs)

        # handle single pixel case
        if len( self._tool._density.shape) == 0 :
            return to(kwargs_opts['units'],self._tool._density)

        #fancyunits=self._tool._density.unit.to_string('latex')
        fancyunits=u.Unit(units).to_string('latex')
        kwargs_opts['title'] = 'n ('+fancyunits+')'
        self._plot(self._tool._density,**kwargs_opts)

    def radiation_field(self,**kwargs):
        '''Plot the radiation field map that was computed by :class:`~pdrtpy.tool.lineratiofit.LineRatioFit` tool. Default units: Habing.
        '''

        #fancyunits=self._tool._radiation_field.unit.to_string('latex')

        kwargs_opts = {'units': 'Habing',
                       'image':True,
                       'contours': False,
                       'label': False,
                       'linewidth': 1.0,
                       'levels': None,
                       'norm': None,
                       'title': None}
        kwargs_opts.update(kwargs)

        # handle single pixel case
        if len( self._tool._radiation_field.shape) == 0 :
            return to(kwargs_opts['units'],self._tool._radiation_field)

        if units not in rad_title:
            fancyunits=u.Unit(units).to_string('latex')
            kwargs_opts['title'] = 'Radiation Field ('+fancyunits+')'
        else:
            kwargs_opts['title'] = rad_title[units]

        self._plot(self._tool._radiation_field,**kwarg_opts)

    #def chisq(self,xaxis,xpix,ypix):
    #    """Make a line plot of chisq as a function of G0 or n for a given pixel"""
    #    axes = {"G0":0,"n":1}
    #    axis = axes[xaxis] #yep key error if you do it wrong
    #        
    def chisq(self, **kwargs):           
        '''Plot the :math:`\chi^2` map that was computed by the
        :class:`~pdrtpy.tool.lineratiofit.LineRatioFit` tool.
        
        **Currently only works for single-pixel Measurements**
        '''

        kwargs_opts = {'units': None,
                       'image':True,
                       'contours': True,
                       'label': False,
                       'colors': ['white'],
                       'linewidth': 1.0,
                       'norm': 'zscale',
                       'title': r'$\chi^2$' }
        kwargs_opts.update(kwargs)
        # make a sensible choice about contours if image is not shown
        if not kwargs_opts['image'] and kwargs_opts['colors'][0] == 'white':
           kwargs_opts['colors'][0] = 'black'

        if len(self._tool._chisq.shape) != 2:
            raise NotImplementedError("Plotting of chisq is not yet implemented for maps")
        self._plot_no_wcs(data=self._tool._chisq,header=None,**kwargs_opts)

    def reduced_chisq(self, **kwargs):
        '''Plot the reduced :math:`\chi^2` map that was computed by the
        :class:`~pdrtpy.tool.lineratiofit.LineRatioFit` tool.
        
        **Currently only works for single-pixel Measurements**
        '''

        kwargs_opts = {'units': None,
                       'image':True,
                       'contours': True,
                       'label': False,
                       'colors': ['white'],
                       'linewidth': 1.0,
                       'norm': 'zscale',
                       'title': r'$\chi_\nu^2$'}
        kwargs_opts.update(kwargs)
        if len(self._tool._chisq.shape) != 2:
            raise NotImplementedError("Plotting of chisq is not yet implemented for maps")
        self._plot_no_wcs(self._tool._reduced_chisq,header=None,**kwargs_opts)

    def plot_both(self,units = ['Habing','cm^-3'], **kwargs):
        '''Plot both radiation field and density maps computed by the
        :class:`~pdrtpy.tool.lineratiofit.LineRatioFit` tool in a 1x2 panel subplot. Defaul units: ['Habing','cm^-3']
        '''

        _index = [1,2]
        _reset = [True,False]

        kwargs_opts = {'image':True,
                       'contours': False,
                       'label': False,
                       'levels': None,
                       'norm': None,
                       'title': None,
                       'nrows': 1,
                       'ncols': 2,
                       'index': _index[0],
                       'reset': _reset[0]
                       }

        kwargs_opts.update(kwargs)

        rf = self.radiation_field(units=units[0],**kwargs_opts)

        kwargs_opts['index'] = _index[1]
        kwargs_opts['reset'] = _reset[1]
 
        d = self.density(units=units[1],**kwargs_opts)
        return (rf,d)

    def confidence_intervals(self,**kwargs):
        '''Plot the confidence intervals from the :math:`\chi^2` map computed by the
        :class:`~pdrtpy.tool.lineratiofit.LineRatioFit` tool. Default levels:  [50., 68., 80., 95., 99.]
        
        **Currently only works for single-pixel Measurements**
        '''

        if len(self._tool._chisq.shape) != 2:
            raise NotImplementedError("Plotting of confidence intervals is not yet implemented for maps")

        kwargs_opts = {'units': None,
                       'image':False,
                       'contours': True,
                       'label': True,
                       'levels': [50., 68., 80., 95., 99.],
                       'colors': ['black'],
                       'linewidth': 1.0,
                       'norm': 'simple',
                       'title': "Confidence Intervals"}

        kwargs_opts.update(kwargs)

        chidata = self._tool._chisq.data
        chi2_stat = 100*stats.distributions.chi2.cdf(chidata,self._tool._dof)
        self._plot_no_wcs(data=chi2_stat,header=self._tool._chisq.header,**kwargs_opts)
        #print("CF min max ",np.min(chi2_stat),np.max(chi2_stat))
    
    def overlay_all_ratios(self,**kwargs):
        '''Overlay all the measured ratios and their errors on the :math:`(n,G_0)` space. Will uses Nx3 subplots.  Default ncols: 3. 
        '''

        if len(self._tool._chisq.shape) != 2:
            raise NotImplementedError("Plotting of ratio overlays is not yet implemented for maps")

        kwargs_opts = {'units': None,
                       'image':False,
                       'contours': False,
                       'levels' : None,
                       'label': False,
                       'linewidth': 1.0,
                       'ncols': 3.0,
                       'norm': None,
                       'title': None,
                       'reset': True}

        kwargs_opts.update(kwargs)

        i =0 
        ncols = kwargs_opts["ncols"]
        # where used??
        nrows = int(round(self._tool.ratiocount/ncols+0.49,0))
        for key,val in self._tool._modelratios.items():
            self._ratiocolor = self._CB_color_cycle[i]
            kwargs_opts['measurements'] = [self._tool._observedratios[key]]
            if i > 0: kwargs_opts['reset']=False
            self._plot_no_wcs(val,header=None,**kwargs_opts)
            i = i+1
        # do some sort of legend
        lines = [Line2D([0], [0], color=c, linewidth=3, linestyle='-') for c in self._CB_color_cycle[0:i]]
        labels = list(self._tool._model_files_used.keys())
        self._plt.legend(lines, labels)

    def ratios_on_models(self,**kwargs):
        '''Overlay all the measured ratios and their errors on the individual models for those ratios.
        '''

        if len(self._tool._chisq.shape) != 2:
            raise NotImplementedError("Plotting of ratio overlays is not yet implemented for maps")

        kwargs_opts = {'units': None,
                       'image':True,
                       'colorbar': True,
                       'contours': True,
                       'levels' : None,
                       'label': False,
                       'linewidth': 1.0,
                       'norm': 'zscale',
                       'title': None,
                       'reset': True}

        kwargs_opts.update(kwargs)

        for key,val in self._tool._modelratios.items():
            m = self._tool._model_files_used[key]
            kwargs_opts['measurements'] = [self._tool._observedratios[key]]
            self._ratiocolor='#4daf4a'
            kwargs_opts['title'] = key + " model (Observed ratio indicated)"
            self._plot_no_wcs(val,header=None,**kwargs_opts)
            

    def _plot(self,data,**kwargs):
        '''generic plotting method used by other plot methods'''

        kwargs_opts = {'units' : None,
                       'image':True,
                       'colorbar': True,
                       'contours': True,
                       'label': False,
                       'title': None
                       }

        kwargs_contour = {'levels': None, 
                          'colors': ['white'],
                          'linewidth': 1.0}


        # Merge in any keys the user provided, overriding defaults.
        kwargs_contour.update(kwargs)
        kwargs_opts.update(kwargs)

        if kwargs_opts['units'] is not None:
            k = to(kwargs_opts['units'], data)
        else:
            k = data
        km = ma.masked_invalid(k)
        # make sure nans don't affect the color map
        min_ = np.nanmin(km)
        max_ = np.nanmax(km)

        kwargs_imshow = { 'origin': 'lower', 
                          'norm': 'simple',
                          'vmin': min_, 
                          'vmax': max_,
                          'cmap': 'plasma',
                          'aspect': 'auto'}
 
        kwargs_subplot = {'nrows': 1,
                          'ncols': 1,
                          'index': 1,
                          'reset': True,
                         }

        # delay merge until min_ and max_ are known
        kwargs_imshow.update(kwargs)
        kwargs_imshow['norm']=self._get_norm(kwargs_imshow['norm'],km,min_,max_)

        kwargs_subplot.update(kwargs)
        kwargs_subplot['figsize'] = kwargs.get("figsize",(kwargs_subplot["nrows"]*5,kwargs_subplot["ncols"]*5))

        #print("Got non-default kwargs: ", kwargs)

        axidx = kwargs_subplot['index']-1
        if kwargs_subplot['reset']:
            self._figure,self._axis = self._plt.subplots(kwargs_subplot['nrows'],kwargs_subplot['ncols'],figsize=kwargs_subplot['figsize'],subplot_kw={'projection':k.wcs,'aspect':kwargs_imshow['aspect']},constrained_layout=True)

        # Make sure self._axis is an array because we will index it below.
        if type(self._axis) is not np.ndarray:
            self._axis = np.array([self._axis])
        
        if kwargs_opts['image']:
            current_cmap = mcm.get_cmap(kwargs_imshow['cmap'])
            current_cmap.set_bad(color='white',alpha=1)
            im=self._axis[axidx].imshow(km,**kwargs_imshow)
            if kwargs_opts['colorbar']:
                self._wcs_colorbar(im,self._axis[axidx])

        if kwargs_opts['contours']:
            if kwargs_contour['levels'] is None:
                # Figure out some autolevels 
                kwargs_contour['levels'] = self._autolevels(km,'log')

            # suppress warnings about unused keywords
            for kx in ['units', 'image', 'contours', 'label', 'title', 'cmap''aspect','colorbar','reset', 'aspect']:
                kwargs_contour.pop(kx,None)

            contourset = self._axis[axidx].contour(km, **kwargs_contour)
            if kwargs_opts['label']:
                self._axis[axidx].clabel(contourset,contourset.levels,inline=True,fmt='%1.1e')

        if kwargs_opts['title'] is not None: 
            self._axis[axidx].set_title(kwargs_opts['title'])

        if k.wcs is not None:
            self._axis[axidx].set_xlabel(k.wcs.wcs.lngtyp)
            self._axis[axidx].set_ylabel(k.wcs.wcs.lattyp)
        
       
    def _plot_no_wcs(self,data,header=None,**kwargs):
        '''generic plotting method for images with no WCS used by other plot methods'''
        #print("KWARGS is ",kwargs)
        measurements= kwargs.pop("measurements",None)
        _dataheader = getattr(data,"header",None)
        if _dataheader is None  and header is None:
            raise Exception("Either your data must have a header dictionary or you must provide one via the header parameter")
        # input header supercedes data header, under assumption user knows what they are doing.
        if header is not None: 
            _header = deepcopy(header)
        else:
            _header = deepcopy(_dataheader)
            # CRxxx might be in wcs and not in header
            if data.wcs is not None:
                _header.update(data.wcs.to_header())

        kwargs_opts = {'units' : None,
                       'image':True,
                       'colorbar': False,
                       'contours': True,
                       'label': False
                       }

        kwargs_contour = {'levels': None, 
                          'colors': ['white'],
                          'linewidth': 1.0}


        # Merge in any keys the user provided, overriding defaults.
        kwargs_contour.update(kwargs)
        #print("kwargs_opts 1: ",kwargs_opts)
        kwargs_opts.update(kwargs)
        #print("kwargs_opts 2: ",kwargs_opts)
        #print("kwargs 2: ",kwargs)

        if kwargs_opts['units'] is not None:
            k = to(kwargs_opts['units'], data)
        else:
            k = data
        km = ma.masked_invalid(k)
        # make sure nans don't affect the color map
        min_ = np.nanmin(km)
        max_ = np.nanmax(km)

        kwargs_imshow = { 'origin': 'lower', 
                          'norm': 'simple',
                          'vmin': min_, 
                          'vmax': max_,
                          'cmap': 'plasma',
                          'aspect': 'equal'}
 
        kwargs_subplot = {'nrows': 1,
                          'ncols': 1,
                          'index': 1,
                          'reset': True,
                         }

        # delay merge until min_ and max_ are known
        #print("plot kwargs 1: ",kwargs_imshow)
        kwargs_imshow.update(kwargs)
        #print("plot kwargs 2: ",kwargs_imshow)
        kwargs_imshow['norm']=self._get_norm(kwargs_imshow['norm'],km,min_,max_)

        kwargs_subplot.update(kwargs)
        kwargs_subplot['figsize'] = kwargs.get("figsize",(kwargs_subplot["nrows"]*5,kwargs_subplot["ncols"]*5))

        #print("Got non-default kwargs: ", kwargs)

        axidx = kwargs_subplot['index']-1
        if kwargs_subplot['reset']:
# @todo can probably consolodate this
            self._figure,self._axis = self._plt.subplots(kwargs_subplot['nrows'],kwargs_subplot['ncols'],figsize=kwargs_subplot['figsize'],subplot_kw={'aspect':kwargs_imshow['aspect']},constrained_layout=True)

        # Make sure self._axis is an array because we will index it below.
        if type(self._axis) is not np.ndarray:
            self._axis = np.array([self._axis])

        xstart=_header['crval1']
        xstop=xstart+_header['naxis1']*_header['cdelt1']
        ystart=_header['crval2']
        ystop=ystart+_header['naxis2']*_header['cdelt2']
        #print(xstart,xstop,ystart,ystop)
    
        y = 10**np.linspace(start=ystart, stop=ystop, num=_header['naxis2'])
        x = 10**np.linspace(start=xstart, stop=xstop, num=_header['naxis1'])
        locmaj = ticker.LogLocator(base=10.0, subs=(1.0, ),numticks=10)
        locmin = ticker.LogLocator(base=10.0, subs=np.arange(2, 10)*.1,numticks=10) 
        xlab = _header['ctype1'] + ' ['+_header['cunit1']+']'
        ylab = _header['ctype2'] + ' ['+_header['cunit2']+']'
        self._axis[axidx].set_ylabel(ylab)
        self._axis[axidx].set_xlabel(xlab)


        self._axis[axidx].set_xscale('log')
        self._axis[axidx].set_yscale('log')
        self._axis[axidx].xaxis.set_major_locator(locmaj)
        self._axis[axidx].xaxis.set_minor_locator(locmin)
        self._axis[axidx].xaxis.set_minor_formatter(ticker.NullFormatter())

        if kwargs_opts['image']:
            im = self._axis[axidx].pcolormesh(x,y,km,cmap=kwargs_imshow['cmap'],norm=kwargs_imshow['norm'])
            if kwargs_opts['colorbar']:
                self._figure.colorbar(im,ax=self._axis[axidx])
                #self._wcs_colorbar(im,self._axis[axidx])
    #todo: allow unit conversion to cgs or Draine
    
        if kwargs_opts['contours']:
            if kwargs_contour['levels'] is None:
                # Figure out some autolevels 
                kwargs_contour['levels'] = self._autolevels(km,'log')

            # suppress warnings about unused keywords
            for kx in ['units', 'image', 'contours', 'label', 'title', 'cmap''aspect','colorbar','reset', 'aspect']:
                kwargs_contour.pop(kx,None)

            contourset = self._axis[axidx].contour(x,y,km.data, **kwargs_contour)
            #print("contourset :",contourset.levels)

            if kwargs_opts['label']:
                drawn = self._axis[axidx].clabel(contourset,contourset.levels,inline=True,fmt='%1.2e')
                #print("drew %s"%drawn)

        if kwargs_opts['title'] is not None: 
            self._axis[axidx].set_title(kwargs_opts['title'])

        if measurements is not None:
            for m in measurements:
                lstyles = ['--','-','--']
                colors = [self._ratiocolor,self._ratiocolor,self._ratiocolor]
                for i in range(0,3):
                    cset = self._axis[axidx].contour(x,y,k.data,levels=m.levels, linestyles=lstyles, colors=colors)
                