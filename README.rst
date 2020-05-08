pdrtpy, a toolbox for analyzing photodissociation regions
#########################################################


***************************************
PhotoDissociation Region Toolbox Python
***************************************

*Reliable astrophysics at everyday low, low prices!* |reg| 

``pdrtpy`` is the new and improved version of the classic `PhotoDissociation Region Toolbox <http://dustem.astro.umd.edu/pdrt>`_, rewritten in Python with new capabilities and giving more flexibility to end users. 

The new PDR Toolbox will cover many more spectral lines and metallicities
and allows map-based analysis so users can quickly compute spatial images
of density and radiation field from map data.  We provide example Jupyter
notebooks for data analysis.  It also can support other PDR model codes
enabling comparison of derived properties between codes.

The underlying model code has improved physics and chemistry. Critical updates include those discussed in 
`Neufeld & Wolfire 2016 <https://ui.adsabs.harvard.edu/abs/2016ApJ...826..183N/abstract>`_, plus photo rates from 
`Heays et al. 2017 <https://ui.adsabs.harvard.edu/abs/2017A%26A...602A.105H/abstract>`_, oxygen chemistry rates from 
`Kovalenko et al. 2018 <https://ui.adsabs.harvard.edu/abs/2018ApJ...856..100K/abstract>`_ and 
`Tran et al. 2018 <https://ui.adsabs.harvard.edu/abs/2018ApJ...854...25T/abstract>`_, 
and carbon chemistry rates from 
`Dagdigian 2019 <https://ui.adsabs.harvard.edu/abs/2019MNRAS.487.3427D/abstract>`_. We have also implemented new collisional
excitation rates for :math:`{\rm [O~I]}` from
`Lique et al. 2018 <https://ui.adsabs.harvard.edu/abs/2018MNRAS.474.2313L/abstract>`_ (and Lique private
communication) and have included :math:`{\rm ^{13}C}` chemistry along with the
emitted line intensities for  :math:`{\rm [^{13}C~II]}` and :math:`{\rm ^{13}CO}`.


Getting Started
===============

Installation
------------

``pdrtpy`` can be installed with 

.. code-block:: sh

   pip install pdrtpy

or 

.. code-block:: sh

   git clone https://github.com/mpound/pdrtpy
   sudo apt-get install python3-venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

Requirements
------------
Python 3 and recent versions of  astropy, numpy, scipy, matplotlib. And jupyter if you want to run the example notebooks.

What is a PDR? 
==============
Photodissociation regions (PDRs) include all of the neutral gas in the
ISM where far-ultraviolet (FUV) photons dominate the chemistry and/or
heating.  In regions of massive star formation, PDRS are created at
the boundaries between the HII regions and neutral molecular cloud,
as photons with energies :math:`6~{\rm eV} < h\nu < {\rm 13.6~eV}`
photodissociate molecules and photoionize other elements.  The gas is
heated from photo-electrons and cools mostly through far-infrared fine
structure lines like  :math:`{\rm [O~I]}` and  :math:`{\rm [C~II]}`.

For a full review of PDR physics and chemistry, see `Hollenbach & Tielens 1997 <https://ui.adsabs.harvard.edu/abs/1997ARA&A..35..179H>`_.

.. |reg|    unicode:: U+000AE .. REGISTERED SIGN