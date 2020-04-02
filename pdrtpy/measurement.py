"""Manage spectral line or continuum observations"""

from copy import deepcopy

import astropy.units as u
from astropy.io import fits,registry
from astropy.nddata import NDDataArray, CCDData, NDUncertainty, StdDevUncertainty, VarianceUncertainty, InverseVariance
import numpy as np

class Measurement(CCDData):
    """Measurement represents one or more observations of a given spectral
    line or continuum.  It is made up of a value array, an
    uncertainty array, units, and a string identifier It is based
    on :class:`astropy.nddata.CCDData`.  It can represent a single pixel
    observation or an image.   Mathematical operations using Measurements
    will correctly propagate errors.  
       
    Typically, Measurements will be instantiated from a FITS file by using the the :func:`read` or :func:`make_measurement` methods.  For a list of recognized spectral line identifiers, see :meth:`~pdrtpy.modelset.Modelset.supported_lines`.
       
    :param data:  The actual data contained in this :class:`Measurement` object.
        Note that the data will always be saved by *reference*, so you should
        make a copy of the ``data`` before passing it in if that's the desired
        behavior.
    :type data: :class:`numpy.ndarray`-like

    :param uncertainty: Uncertainties on the data. If the uncertainty is a :class:`numpy.ndarray`, it assumed to be, and stored as, a :class:`astropy.nddata.StdDevUncertainty`.  Required.
    :type uncertainty: :class:`astropy.nddata.StdDevUncertainty`, \
            :class:`astropy.nddata.VarianceUncertainty`, \
            :class:`astropy.nddata.InverseVariance` or :class:`numpy.ndarray`
    :param unit: The units of the data.  Required.
    :type unit: :class:`astropy.units.Unit` or str
        
    :param identifier: string indicating what this is an observation of, e.g., "CO_10" for CO(1-0)
    :type identifier: str
    
    :meth:`read(\\*args, \\**kwargs)`
    ``Classmethod`` to create an Measurement instance based on a ``FITS`` file.
    This method uses :func:`fits_measurement_reader` with the provided
    parameters.  Example usage:
        
    .. code-block:: python

       from pdrtpy.measurement import Measurement

       my_obs = Measurement.read("file.fits",identifier="CII_158")
       my_other_obs = Measurement.read("file.fits",identifier="CO2_1",unit="K km/s")

    """
    def __init__(self,*args, **kwargs):
        debug = kwargs.pop('debug', False)
        if debug: 
            print("args=",*args)
            print("kwargs=",*kwargs)
        self._identifier = kwargs.pop('identifier', 'unknown')
        _beam = dict()
        _beam["BMAJ"] = kwargs.pop('bmaj', None)
        _beam["BMIN"] = kwargs.pop('bmin', None)
        _beam["BPA"] = kwargs.pop('bpa', None)
        self._filename = None

        #Won't work: On arithmetic operations, this raises the exception. 
        #if self._identifier is None:
        #    raise ValueError("an identifier for Measurement must be specified.")
        #On arithmetic operations, this causes an annoying 
        # log.info() message from CCDData about overwriting Quantity 

        # This workaround is needed because CCDData raises an exception if unit
        # not given. Whereas having BUNIT in the image header instead would be 
        # perfectly reasonable...
        self._defunit = "adu"
        _unit = kwargs.pop('unit', self._defunit)

        super().__init__(*args, **kwargs, unit=_unit)

        # Set unit to header BUNIT or put BUNIT into header if it 
        # wasn't present 
        if "BUNIT" in self.header:
            self.unit(self.header["BUNIT"])
            self.uncertainy.unit(self.header["BUNIT"])
        else: 
            # use str in case a astropy.Unit was given
            self.header["BUNIT"] = str(_unit) 

        # Ditto beam parameters
        if "BMAJ" not in self.header:
            self.header["BMAJ"] = _beam["BMAJ"]
        if "BMIN" not in self.header:
            self.header["BMIN"] = _beam["BMIN"]
        if "BPA" not in self.header:
            self.header["BPA"] = _beam["BPA"]

    @staticmethod
    def make_measurement(fluxfile,error,outfile,rms=None):
        """Create a FITS files with 2 HDUS, the first being the flux and the 2nd being 
        the flux uncertainty. This format makes allows the resulting file to be read into the underlying :class:'~astropy.nddata.CCDData` class.

        :param fluxfile: The FITS file containing the flux data as a function of spatial coordinates
        :type fluxfile: str
        :param error: The errors on the flux data
             Possible values for error are:
             1. a filename with the same shape as fluxfile containing the error values per pixel
             2. a percentage value 'XX%' must have the "%" symbol in it
             3. 'rms' meaning use the rms parameter if given, otherwise look for the RMS keyword in the FITS header of the fluxfile
        :type error: str
        :param outfile: The output file to write the result in (FITS format)
        :type outfile: str
        :param rms:  If error == 'rms', this value may give the rms in same units as flux.
        :type rms: float or :class:`astropy.units.Unit`
        :raises: Exception on various FITS header issues

        Example usage:
        
        .. code-block:: python

            # example with percentage error
            Measurement.make_measurement("my_infile.fits",error='10%',outfile="my_outfile.fits")

            # example with measurement in units of K km/s and error 
            # indicated by RMS keyword in input file.
            Measurement.make_measurement("my_infile.fits",error='rms',outfile="my_outfile.fits",units="K km/s")
        """
        _flux = fits.open(fluxfile)
            
        if error == 'rms':
            _error = deepcopy(_flux)
            if rms is None:
                _rms = _flux[0].header.get("RMS",None)
                if _rms is None:
                    raise Exception("rms not given as parameter and RMS keyword not present in flux header")
                _error[0].data = np.full(_error[0].data.shape,rms)
        elif "%" in error:
            percent = float(error.strip('%')) / 100.0
            _error = deepcopy(_flux)
            _error[0].data = _flux[0].data*percent
        else:
            _error = fits.open(error)
        #print(_error[0].data.shape)
 
        fb = _flux[0].header.get('bunit','adu')
        eb = _error[0].header.get('bunit','adu')
        if fb != eb:
            raise Exception("BUNIT must be the same in both flux (%s) and error (%s) maps"%(fb,eb))
        _out = fits.open(name=outfile,mode="append")
        _out.append(_flux[0])
        _out[0].header['bunit'] = fb
        _out.append(_error[0])
        _out[1].header['extname']='UNCERT'
        _out[1].header['bunit'] = eb
        _out[1].header['utype'] = 'StdDevUncertainty'
        _out.writeto(outfile,overwrite=True)
        
            
    @property
    def flux(self):
        '''Return the underlying flux data array
        
        :rtype: :class:`numpy.ndarray`
        '''
        return self.data

    @property
    def error(self):
        '''Return the underlying error array

        :rtype: :class:`numpy.ndarray`
        '''
        return self.uncertainty._array
    
    @property
    def SN(self):
        '''Return the signal to noise ratio (flux/error)

        :rtype: :class:`numpy.ndarray`
        '''
        return self.flux/self.error
    
    @property
    def id(self):
        '''Return the string ID of this measurement, e.g., CO_10

        :rtype: str
        '''
        return self._identifier

    def identifier(self,id):
        '''Set the string ID of this measurement, e.g., CO_10
      
        :param id: the identifier
        :type id: str
        '''
        self._identifier = id
    
    @property
    def filename(self):
        '''The FITS file that created this measurement, or None if it didn't originate from a file
        
        :rtype: str or None
        '''
        return self._filename
    
    def write(self,filename,**kwd):
        '''Write this Measurement to a FITS file with flux in 1st HDU and error in 2nd HDU. See astropy.nddata.CCDData.write
        
        :param filename:  Name of file.
        :type filename: str
        :param kwd: All additional keywords are passed to :py:mod:`astropy.io.fits`
        '''
        hdu = self.to_hdu()
        hdu.writeto(filename,**kwd)
        
    @property
    def levels(self):
        if self.flux.size != 1:
            raise Exception("This only works for Measurements with a single pixel")
        return np.array([np.float(self.flux-self.error),np.float(self.flux),np.float(self.flux+self.error)])

    
    def add(self,other):
        """Add this Measurement to another, propagating errors, units,  and updating identifiers

        :param other: a Measurement to add
        :type other: :class:`Measurement`
        """
        # need to do tricky stuff to preserve unit propogation.
        # super().add() does not work because it instantiates a Measurement
        # with the default unit "adu" and then units for the operation are
        # not conformable.  I blame astropy CCDData authors for making that
        # class so hard to subclass.
        z=CCDData.add(self,other)
        z=Measurement(z,unit=z._unit)
        z._identifier = self.id + '+' + other.id
        z._unit = self.unit
        return z
   
    def subtract(self,other):
        '''Subtract another Measurement from this one, propagating errors, units,  and updating identifiers

        :param other: a Measurement to subtract
        :type other: :class:`Measurement`
        '''
        z=CCDData.subtract(self,other)
        z=Measurement(z,unit=z._unit)
        z._identifier = self.id + '-' + other.id
        return z
    
    def multiply(self,other):
        '''Multiply this Measurement by another, propagating errors, units,  and updating identifiers

        :param other: a Measurement to multiply
        :type other: :class:`Measurement`
        '''
        z=CCDData.multiply(self,other)
        z=Measurement(z,unit=z._unit)
        z._identifier = self.id + '*' + other.id
        return z
        
    def divide(self,other):
        '''Divide this Measurement by another, propagating errors, units,  and updating identifiers

        :param other: a Measurement to divide
        :type other: :class:`Measurement`
        '''
        z=CCDData.divide(self,other)
        z=Measurement(z,unit=z._unit)
        z._identifier = self.id + '/' + other.id
        return z
    
    def __add__(self,other):
        '''Add this Measurement to another using + operator, propagating errors, units,  and updating identifiers'''
        z=self.add(other)
        return z
    def __sub__(self,other): 
        '''Subtract another Measurement from this one using - operator, propagating errors, units,  and updating identifiers'''
        z=self.subtract(other)
        return z
    
    def __mul__(self,other):
        '''Multiply this Measurement by another using * operator, propagating errors, units,  and updating identifiers'''
        z=self.multiply(other)
        return z
    
    def __truediv__(self,other):
        '''Divide this Measurement by another using / operator, propagating errors, units,  and updating identifiers'''
        z=self.divide(other)
        return z

    def __len__(self):
        return len(self.shape)

    def __repr__(self):
        m = "%s +/- %s %s" % (self.data,self.error,self.unit)
        return m
    
    def __str__(self):
        m = "%s +/- %s %s" % (self.data,self.error,self.unit)
        return m
    
    def __getitem__(self,index):
        '''Allows us to use [] to index into the data array
        '''
        return self._data[index]
    
def fits_measurement_reader(filename, hdu=0, unit=None, 
                        hdu_uncertainty='UNCERT',
                        hdu_mask='MASK', hdu_flags=None,
                        key_uncertainty_type='UTYPE', **kwd):
    '''Reader for Measurement class, which will be called by :meth:`Measurement.read`.
    
    :param filename: Name of FITS file.
    :type filename: str

    :param hdu: FITS extension from which Measurement should be initialized. 
         If zero and and no data in the primary extension, it will
         search for the first extension with data. The header will be
         added to the primary header.  Default is 0.
    :type hdu: int, optional

    :type unit: :class:`astropy.units.Unit`, optional
    :param unit: 
         Units of the image data. If this argument is provided and there is a
         unit for the image in the FITS header (the keyword ``BUNIT`` is used
         as the unit, if present), this argument is used for the unit.
         Default is ``None``.

    :type hdu_uncertainty: str or None, optional
    :param hdu_uncertainty: FITS extension from which the uncertainty
         should be initialized. If the extension does not exist the
         uncertainty of the Measurement is ``None``.  Default is
         ``'UNCERT'``.

    :type hdu_mask: str or None, optional
    :param hdu_mask: FITS extension from which the mask should be initialized. If the extension does not exist the mask of the Measurement is ``None``.  Default is ``'MASK'``.

    :type hdu_flags: str or None, optional
    :param hdu_flags: Currently not implemented.  Default is ``None``.

    :type key_uncertainty_type: str, optional
     :param key_uncertainty_type: The header key name where the class name of the uncertainty  is stored in the hdu of the uncertainty (if any).  Default is ``UTYPE``.
    :param kwd: Any additional keyword parameters are passed through to the FITS reader in :mod:`astropy.io.fits`; see Notes for additional discussion.

    :raises: TypeError
    '''
   
    _id = kwd.pop('identifier', 'unknown')
    z = CCDData.read(filename,hdu,unit,hdu_uncertainty,hdu_mask,key_uncertainty_type, **kwd)
    # @TODO if uncertainty plane not present, look for RMS keyword
    # @TODO header values get stuffed into WCS, others may be dropped by CCDData._generate_wcs_and_update_header
    try:
       z = Measurement(z)
    except Exception:
       raise TypeError('could not convert fits_measurement_reader output to Measurement')
    z.identifier(_id)
    # astropy.io.registry.read creates a FileIO object before calling the registered
    # reader (this method), so the filename is FileIO.name. 
    z._filename=filename.name
    return z

    
with registry.delay_doc_updates(Measurement):
    registry.register_reader('fits', Measurement, fits_measurement_reader)
    

if __name__ == "__main__":

    m1 = Measurement(data=[30.,20.],uncertainty = StdDevUncertainty([5.,5.]),identifier="OI_145",unit="adu")
    m2 = Measurement(data=10.,uncertainty = StdDevUncertainty(2.),identifier="CI_609",unit="adu")
    m3 = Measurement(data=10.,uncertainty = StdDevUncertainty(1.5),identifier="CO_21",unit="adu")
    m4 = Measurement(data=100.,uncertainty = StdDevUncertainty(10.),identifier="CII_158",unit="adu")

    print(m1/m2)
    print(m2/m3)
    print(m1*m2)
    print(m2/m4)
    print(m4*m3)
    print(m4+m3)
    print(m3-m1)

    print(m3.levels)
